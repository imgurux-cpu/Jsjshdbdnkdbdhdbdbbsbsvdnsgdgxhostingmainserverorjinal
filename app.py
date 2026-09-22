# -*- coding: utf-8 -*-
import base64
import copy
from datetime import datetime, timedelta
import json
import logging
import hashlib
import mimetypes
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
import requests
from flask import Flask
from threading import Thread
import psutil
import telebot
from telebot import types

# --- Configurable Conversion Rate ---
USDT_BDT_RATE = 120.0  # 1 USDT = 120 BDT (প্রয়োজনে পরিবর্তন করতে পারেন)

# --- Flask Keep Alive ---
app = Flask("")


@app.route("/")
def home():
    return "OK", 200


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)


def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Flask Keep-Alive server started.")


# --- End Flask Keep Alive ---

# --- Configuration ---
# Keep credentials in Render environment variables, never in source control.
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError(
        "Missing TELEGRAM_BOT_TOKEN environment variable. "
        "Set it in the hosting environment before starting the bot."
    )


def required_int_env(name, fallback=None):
    value = os.environ.get(name, fallback)
    if value is None or str(value).strip() == "":
        raise RuntimeError(f"Missing {name} environment variable.")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a numeric Telegram user ID.") from exc
# Direct numeric Admin/Owner IDs
OWNER_ID = required_int_env("OWNER_ID")
ADMIN_ID = required_int_env("ADMIN_ID")

YOUR_USERNAME = os.environ.get("OWNER_USERNAME", "@Masrafi01")
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/")
# Manual payment review only. This value is displayed to users; no Binance API
# credentials or Binance network calls are used by this bot.
BINANCE_PAY_ID = os.environ.get("BINANCE_PAY_ID", "SET_YOUR_BINANCE_PAY_ID")

# Folder setup - using absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, "upload_bots")

# File upload limits
FREE_USER_LIMIT = 0  # Default free limit
SUBSCRIBED_USER_LIMIT = 15
ADMIN_LIMIT = 999
OWNER_LIMIT = float("inf")

# Uploaded bot files must remain local so the bot can run them. User records
# and admin configuration are never stored in this directory.
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)

# Google Sheets is the only persistent data source. Keep credentials in
# environment variables / Replit Secrets, never in this file.
GOOGLE_SHEET_ID = (
    os.environ.get("GOOGLE_SHEET_ID")
    or os.environ.get("SHEET_ID")
    or ""
).strip()
GOOGLE_SERVICE_ACCOUNT_JSON = (
    os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    or os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    or os.environ.get("GOOGLE_CREDENTIALS_JSON")
    or ""
).strip()
try:
    GOOGLE_SYNC_INTERVAL = max(
        1.0, float(os.environ.get("GOOGLE_SYNC_INTERVAL", "1"))
    )
except (TypeError, ValueError):
    GOOGLE_SYNC_INTERVAL = 1.0

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
hosted_bot_records = {}
file_callback_refs = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False
user_selected_plan = {}  # Temp state for upload flow


def _file_callback_token(owner_id, file_name):
    """Map long filenames to a short Telegram-safe callback token."""
    if len(file_callback_refs) > 5000:
        file_callback_refs.clear()
    marker = f"{int(owner_id)}:{str(file_name)}"
    token = hashlib.sha256(marker.encode("utf-8")).hexdigest()[:16]
    file_callback_refs[token] = (int(owner_id), str(file_name))
    return token


def _file_callback_target(token):
    target = file_callback_refs.get(str(token))
    if not target:
        return None, None
    return target

# --- Malware Detection Configuration ---
MALWARE_SIGNATURES = [
    b"MZ",  # Windows executable
    b"\x7fELF",  # Linux executable
    b"\xfe\xed\xfa",  # Mach-O binary
    b"\xce\xfa\xed\xfe",  # Mach-O binary (reverse)
    b"PK",  # ZIP archive
    b"Rar!",  # RAR archive
]

ENCRYPTED_FILE_INDICATORS = [
    b"openssl",
    b"encrypted",
    b"cipher",
    b"AES",
    b"DES",
    b"RSA",
    b"GPG",
    b"PGP",
]

SUSPICIOUS_KEYWORDS = [
    b"ransomware",
    b"trojan",
    b"virus",
    b"malware",
    b"backdoor",
    b"exploit",
    b"payload",
    b"botnet",
    b"keylogger",
    b"rootkit",
]

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- Command Button Layouts ---
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["✨ 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ✨"],
    ["🚀 𝗨𝗽𝗹𝗼𝗮𝗱 𝗙𝗶𝗹𝗲", "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗙𝗶𝗹𝗲𝘀"],
    ["💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀", "⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴"],
    ["📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀", "💻 𝗧𝗲𝗿𝗺𝗶𝗻𝗮𝗹 𝗖𝗺𝗱"],
    ["👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿"],
]

ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    ["✨ 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ✨"],
    ["🚀 𝗨𝗽𝗹𝗼𝗮d 𝗙𝗶𝗹𝗲", "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗙𝗶𝗹𝗲𝘀"],
    ["💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀", "🛡️ 𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹"],
    ["⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴", "📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀"],
    ["👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿"],
]

# --- Runtime-only collections ---
# These dictionaries are intentionally not written to the filesystem. They
# are populated from Google Sheets before polling starts and mirrored back
# after each meaningful change.
google_runtime_lock = threading.RLock()
google_sheet_data_loaded = False
google_sheet_last_error = ""
google_sheet_last_signature = None
google_sync_trigger_scheduled = False
google_sync_trigger_lock = threading.Lock()
google_sheet_initial_sync = True
google_sheet_tabs = set()

user_records = {}
plans_runtime = []
payment_requests_runtime = {}
next_payment_request_id = 1


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _normalize_username(value):
    value = str(value or "").strip()
    if not value:
        return ""
    return "@" + value.lstrip("@")


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_number(value, default=0.0):
    try:
        number = float(str(value).strip())
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return default


def _expiry_from_value(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _user_is_premium(user_id):
    subscription = user_subscriptions.get(int(user_id))
    return bool(subscription and subscription.get("expiry") > datetime.now())


def _user_row(user_id):
    """Return the only user fields that are allowed in Google Sheets."""
    user_id = int(user_id)
    record = user_records.get(user_id, {})
    subscription = user_subscriptions.get(user_id, {})
    premium = _user_is_premium(user_id)
    stored_plan = subscription.get("plan_name", "Free") if subscription else "Free"
    stored_expiry = (
        subscription.get("expiry").isoformat(timespec="seconds")
        if subscription.get("expiry")
        else ""
    )
    return {
        "user_name": str(record.get("user_name", ""))[:120],
        "username": _normalize_username(record.get("username", ""))[:120],
        "user_id": user_id,
        "balance": _as_number(record.get("balance", 0), 0.0),
        "plan": stored_plan,
        "expiry": stored_expiry,
        "banned": bool(record.get("banned", False)),
        "active": bool(user_id in active_users or record.get("active", False)),
        "user_type": "Premium" if premium else "Free",
    }


def _ensure_runtime_user(user_id, user_name="", username=None):
    user_id = int(user_id)
    record = user_records.setdefault(
        user_id,
        {
            "user_id": user_id,
            "user_name": "",
            "username": "",
            "balance": 0.0,
            "banned": False,
            "active": False,
            "created_at": _now_iso(),
        },
    )
    if user_name:
        record["user_name"] = str(user_name).strip()[:120]
    if username is not None:
        record["username"] = _normalize_username(username)[:120]
    return record


def update_user_profile(user_id, user_name="", username=None):
    record = _ensure_runtime_user(user_id, user_name, username)
    record["updated_at"] = _now_iso()
    trigger_google_sheets_sync()
    return record


def is_user_banned(user_id):
    record = user_records.get(int(user_id))
    return bool(record and record.get("banned", False))


def set_user_banned(user_id, banned):
    record = _ensure_runtime_user(user_id)
    record["banned"] = bool(banned)
    record["updated_at"] = _now_iso()
    trigger_google_sheets_sync()


def get_user_stats():
    total_users = len(user_records)
    premium_users = sum(1 for uid in user_records if _user_is_premium(uid))
    return {
        "total_users": total_users,
        "active_users": len(active_users),
        "free_users": max(total_users - premium_users, 0),
        "premium_users": premium_users,
        "banned_users": sum(
            1 for item in user_records.values() if item.get("banned", False)
        ),
        "total_files": sum(len(items) for items in user_files.values()),
    }


def _canonicalize_plans(items):
    result = []
    seen = set()
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            plan_id = int(_as_number(item.get("plan_id"), 0) or 0)
            name = str(item.get("name", "")).strip()
            limit = int(_as_number(item.get("file_limit"), 0) or 0)
            price = str(item.get("price", "")).strip()
            duration = int(_as_number(item.get("duration"), 0) or 0)
            buy_link = str(item.get("buy_link", "")).strip()
        else:
            try:
                plan_id, name, limit, price, duration, buy_link = item
                plan_id = int(plan_id)
                limit = int(limit)
                duration = int(duration)
            except (TypeError, ValueError):
                continue
            name, price, buy_link = str(name).strip(), str(price).strip(), str(buy_link).strip()
        if not name:
            continue
        marker = plan_id or name.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        result.append({
            "plan_id": plan_id,
            "name": name,
            "file_limit": limit,
            "price": price,
            "duration": duration,
            "buy_link": buy_link,
        })
    result.sort(key=lambda item: (int(item.get("plan_id", 0)), item["name"].casefold()))
    return result


def _plan_tuple(item):
    return (
        item["plan_id"],
        item["name"],
        item["file_limit"],
        item["price"],
        item["duration"],
        item["buy_link"],
    )


# --- Price Parser & Conversion Helper ---
def parse_price_to_usdt(price_str):
    """
    টাকা বা ডলারের ফিল্ড থেকে সংখ্যা ও কারেন্সি বের করে USDT কনভার্ট করে।
    যেমন: '500 BDT' -> (4.17, '500 BDT (~4.17 USDT)')
    '5 USDT' -> (5.0, '5.0 USDT')
    """
    price_clean = str(price_str).upper().strip()
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", price_clean)
    if not numbers:
        return 0.0, price_str

    val = float(numbers[0])
    if "BDT" in price_clean or "TAKA" in price_clean or "TK" in price_clean:
        usdt_val = round(val / USDT_BDT_RATE, 2)
        return usdt_val, f"{price_str} (~{usdt_val} USDT)"
    elif "USDT" in price_clean or "$" in price_clean or "USD" in price_clean:
        return round(val, 2), f"{val} USDT"
    else:
        # ডিফল্ট যদি শুধু সংখ্যা দেওয়া হয় তবে USDT ধরা হবে
        return round(val, 2), f"{val} USDT"


# --- Google-backed plan and payment operations ---
def add_plan_db(name, file_limit, price, duration, buy_link):
    global plans_runtime
    name = str(name).strip()
    for existing in plans_runtime:
        if str(existing.get("name", "")).strip().casefold() == name.casefold():
            return int(existing.get("plan_id", 0))
    existing_ids = [int(item.get("plan_id", 0)) for item in plans_runtime]
    plan_id = max(existing_ids or [0]) + 1
    plans_runtime.append({
        "plan_id": plan_id,
        "name": name,
        "file_limit": int(file_limit),
        "price": str(price).strip(),
        "duration": int(duration),
        "buy_link": str(buy_link).strip(),
    })
    plans_runtime = _canonicalize_plans(plans_runtime)
    trigger_google_sheets_sync()
    return plan_id


def get_all_plans():
    return [_plan_tuple(item) for item in _canonicalize_plans(plans_runtime)]


def get_plan_by_id(plan_id):
    try:
        plan_id = int(plan_id)
    except (TypeError, ValueError):
        return None
    for item in plans_runtime:
        if int(item.get("plan_id", 0)) == plan_id:
            return _plan_tuple(item)
    return None


def delete_plan_db(plan_id):
    global plans_runtime
    plans_runtime = [
        item for item in plans_runtime if int(item.get("plan_id", 0)) != int(plan_id)
    ]
    trigger_google_sheets_sync()


# --- Manual Payment Review Helpers ---
def create_payment_request(user_id, plan_id, tx_id):
    """Store a payment claim as pending and return its request ID."""
    global next_payment_request_id
    if get_payment_request_by_txid(tx_id):
        return None
    request_id = next_payment_request_id
    next_payment_request_id += 1
    payment_requests_runtime[str(request_id)] = {
        "request_id": request_id,
        "user_id": int(user_id),
        "plan_id": int(plan_id),
        "tx_id": str(tx_id).strip(),
        "status": "pending",
        "submitted_at": _now_iso(),
        "reviewed_at": "",
        "reviewer_id": "",
    }
    trigger_google_sheets_sync()
    return request_id


def get_payment_request(request_id):
    return payment_requests_runtime.get(str(request_id))


def get_payment_request_by_txid(tx_id):
    tx_id = str(tx_id).strip()
    for item in payment_requests_runtime.values():
        if str(item.get("tx_id", "")).strip() == tx_id:
            return {
                "request_id": item.get("request_id"),
                "status": item.get("status"),
            }
    return None


def mark_payment_request(request_id, status, reviewer_id):
    """Transition a pending request once; returns whether this call won."""
    request = payment_requests_runtime.get(str(request_id))
    if not request or request.get("status") != "pending":
        return False
    request.update({
        "status": str(status),
        "reviewed_at": _now_iso(),
        "reviewer_id": int(reviewer_id),
    })
    trigger_google_sheets_sync()
    return True


# --- Malware Detection Functions ---
def is_suspicious_file(file_content, file_name):
    file_lower = file_name.lower()
    suspicious_extensions = [
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".scr",
        ".com",
        ".pif",
        ".application",
        ".gadget",
        ".msi",
        ".msp",
        ".com",
        ".scr",
        ".hta",
        ".cpl",
        ".msc",
        ".jar",
        ".bin",
        ".deb",
        ".rpm",
        ".apk",
        ".app",
        ".dmg",
        ".iso",
        ".img",
    ]
    if any(file_lower.endswith(ext) for ext in suspicious_extensions):
        return True, f"Suspicious file extension: {file_name}"
    for signature in MALWARE_SIGNATURES:
        if file_content.startswith(signature):
            return True, f"Malware signature detected: {signature}"
    sample_size = min(len(file_content), 4096)
    file_sample = file_content[:sample_size]
    for indicator in ENCRYPTED_FILE_INDICATORS:
        if indicator in file_sample:
            return (
                True,
                f"Encrypted file indicator: {indicator.decode('utf-8', errors='ignore')}",
            )
    sample_text = file_sample.decode("utf-8", errors="ignore").lower()
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword.decode("utf-8").lower() in sample_text:
            return True, f"Suspicious keyword found: {keyword.decode('utf-8')}"
    return False, "File appears safe"


def scan_file_for_malware(file_content, file_name, user_id):
    if user_id == OWNER_ID:
        return True, "Owner bypassed security check"
    is_suspicious, reason = is_suspicious_file(file_content, file_name)
    if is_suspicious:
        logger.warning(
            f"🚨 Malware detected in {file_name} from user {user_id}: {reason}"
        )
        return False, f"Security violation: {reason}"
    return True, "File passed security check"


# --- Helper Functions ---
def get_user_folder(user_id):
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def get_user_file_limit(user_id):
    if user_id == OWNER_ID:
        return OWNER_LIMIT
    if user_id in admin_ids:
        return ADMIN_LIMIT
    if (
        user_id in user_subscriptions
        and user_subscriptions[user_id]["expiry"] > datetime.now()
    ):
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT


def get_user_file_count(user_id):
    return len(user_files.get(user_id, []))


def is_bot_running(script_owner_id, file_name):
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get("process"):
        try:
            proc = psutil.Process(script_info["process"].pid)
            is_running = (
                proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            )
            if not is_running:
                if (
                    "log_file" in script_info
                    and hasattr(script_info["log_file"], "close")
                    and not script_info["log_file"].closed
                ):
                    try:
                        script_info["log_file"].close()
                    except Exception:
                        pass
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            if script_key in bot_scripts:
                del bot_scripts[script_key]
            return False
        except Exception:
            return False
    return False


def kill_process_tree(process_info):
    try:
        if (
            "log_file" in process_info
            and hasattr(process_info["log_file"], "close")
            and not process_info["log_file"].closed
        ):
            try:
                process_info["log_file"].close()
            except Exception:
                pass
        process = process_info.get("process")
        if process and hasattr(process, "pid"):
            pid = process.pid
            if pid:
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    try:
                        child.terminate()
                    except Exception:
                        pass
                try:
                    parent.terminate()
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"❌ Error killing process: {e}")


# --- Module / Package Mapping ---
TELEGRAM_MODULES = {
    "telebot": "pyTelegramBotAPI",
    "telegram": "python-telegram-bot",
    "python_telegram_bot": "python-telegram-bot",
    "aiogram": "aiogram",
    "pyrogram": "pyrogram",
    "telethon": "telethon",
    "bs4": "beautifulsoup4",
    "requests": "requests",
    "pillow": "Pillow",
    "cv2": "opencv-python",
    "flask": "Flask",
    "psutil": "psutil",
}


# --- Automatic & Guided Script Running ---
def monitor_and_guide_error(
    process, log_file_path, script_owner_id, file_name, message_obj_for_reply
):
    """রানিং স্ক্রিপ্ট ব্যাকগ্রাউন্ডে চেক করে কোনো এরর থাকলে ইউজারকে বাটন দিয়ে বুঝিয়ে দেবে"""
    time.sleep(3)
    if process.poll() is not None:
        try:
            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()

            match_py = re.search(
                r"(?:ModuleNotFoundError|ImportError): No module named '(.+?)'",
                log_content,
            )
            match_js = re.search(r"Cannot find module '(.+?)'", log_content)

            missing_module = None
            if match_py:
                missing_module = match_py.group(1).split(".")[0].strip("'\"")
            elif match_js:
                missing_module = match_js.group(1).split("/")[0].strip("'\"")

            if missing_module:
                pkg_name = TELEGRAM_MODULES.get(
                    missing_module.lower(), missing_module
                )
                ext = os.path.splitext(file_name)[1].lower()
                cmd_text = (
                    f"npm install {pkg_name}"
                    if ext == ".js"
                    else f"pip install {pkg_name}"
                )

                error_msg = (
                    f"⚠️ **ফাইল রান হতে সমস্যা হয়েছে!**\n\n"
                    f"📄 **File:** `{file_name}`\n"
                    f"❌ **সমস্যা:** আপনার কোডে `{missing_module}` মডিউলটি মিসিং আছে।\n"
                    f"💻 **প্রয়োজনীয় কমান্ড:** `{cmd_text}`\n\n"
                    f"👇 *নিচের বাটনে প্রেস করে সরাসরি মডিউলটি ইনস্টল করুন:*"
                )

                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        f"📦 Install {pkg_name}",
                        callback_data=f"instmod_{script_owner_id}_{missing_module}_{file_name}",
                    )
                )
                markup.add(
                    types.InlineKeyboardButton(
                        "📄 View Error Logs",
                        callback_data=f"viewlog_{script_owner_id}_{file_name}",
                    )
                )

                if message_obj_for_reply is not None:
                    bot.reply_to(
                        message_obj_for_reply,
                        error_msg,
                        reply_markup=markup,
                        parse_mode="Markdown",
                    )
            else:
                error_msg = (
                    f"⚠️ **আপনার কোডে ভুল (Syntax/Runtime Error) পাওয়া গেছে!**\n\n"
                    f"📄 **File:** `{file_name}`\n"
                    f"সুনির্দিষ্ট এরর জানতে নিচের **View Logs** বাটনে ক্লিক করুন।"
                )
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton(
                        "📄 View Error Logs",
                        callback_data=f"viewlog_{script_owner_id}_{file_name}",
                    )
                )
                if message_obj_for_reply is not None:
                    bot.reply_to(
                        message_obj_for_reply,
                        error_msg,
                        reply_markup=markup,
                        parse_mode="Markdown",
                    )
        except Exception as e:
            logger.error(f"Error checking log file: {e}")


def run_script(
    script_path, script_owner_id, user_folder, file_name, message_obj_for_reply
):
    script_key = f"{script_owner_id}_{file_name}"
    try:
        log_file_path = os.path.join(
            user_folder, f"{os.path.splitext(file_name)[0]}.log"
        )
        log_file = open(log_file_path, "w", encoding="utf-8", errors="ignore")
        process = subprocess.Popen(
            [sys.executable, script_path],
            cwd=user_folder,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.PIPE,
        )

        bot_scripts[script_key] = {
            "process": process,
            "log_file": log_file,
            "file_name": file_name,
            "script_owner_id": script_owner_id,
            "start_time": datetime.now(),
            "user_folder": user_folder,
            "type": "py",
            "script_key": script_key,
        }

        if message_obj_for_reply is not None:
            bot.reply_to(
                message_obj_for_reply,
                f"🚀 **Python Script Started!**\n📄 File: `{file_name}`\n🆔 PID: `{process.pid}`",
                parse_mode="Markdown",
            )

        threading.Thread(
            target=monitor_and_guide_error,
            args=(
                process,
                log_file_path,
                script_owner_id,
                file_name,
                message_obj_for_reply,
            ),
        ).start()

    except Exception as e:
        if message_obj_for_reply is not None:
            bot.reply_to(message_obj_for_reply, f"❌ Error running script: {str(e)}")


def run_js_script(
    script_path, script_owner_id, user_folder, file_name, message_obj_for_reply
):
    script_key = f"{script_owner_id}_{file_name}"
    try:
        log_file_path = os.path.join(
            user_folder, f"{os.path.splitext(file_name)[0]}.log"
        )
        log_file = open(log_file_path, "w", encoding="utf-8", errors="ignore")
        process = subprocess.Popen(
            ["node", script_path],
            cwd=user_folder,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.PIPE,
        )

        bot_scripts[script_key] = {
            "process": process,
            "log_file": log_file,
            "file_name": file_name,
            "script_owner_id": script_owner_id,
            "start_time": datetime.now(),
            "user_folder": user_folder,
            "type": "js",
            "script_key": script_key,
        }

        if message_obj_for_reply is not None:
            bot.reply_to(
                message_obj_for_reply,
                f"🚀 **JS Script Started!**\n📄 File: `{file_name}`\n🆔 PID: `{process.pid}`",
                parse_mode="Markdown",
            )

        threading.Thread(
            target=monitor_and_guide_error,
            args=(
                process,
                log_file_path,
                script_owner_id,
                file_name,
                message_obj_for_reply,
            ),
        ).start()

    except Exception as e:
        if message_obj_for_reply is not None:
            bot.reply_to(
                message_obj_for_reply, f"❌ Error running JS script: {str(e)}"
            )


# --- Runtime operations mirrored to Google Sheets ---
def save_user_file(user_id, file_name, file_type="py"):
    if user_id not in user_files:
        user_files[user_id] = []
    user_files[user_id] = [
        (fn, ft) for fn, ft in user_files[user_id] if fn != file_name
    ]
    user_files[user_id].append((file_name, file_type))


def _hosted_bot_key(user_id, file_name):
    return f"{int(user_id)}:{str(file_name)}"


def save_hosted_bot(user_id, file_name, file_type="py", desired_status="active"):
    """Persist only the metadata needed to restore a hosted bot after restart."""
    user_id = int(user_id)
    file_name = str(file_name)
    file_type = "js" if str(file_type).lower() == "js" else "py"
    status = "active" if str(desired_status).lower() == "active" else "stopped"
    hosted_bot_records[_hosted_bot_key(user_id, file_name)] = {
        "owner_id": user_id,
        "file_name": file_name,
        "file_type": file_type,
        "desired_status": status,
    }
    trigger_google_sheets_sync()


def set_hosted_bot_status(user_id, file_name, desired_status):
    key = _hosted_bot_key(user_id, file_name)
    record = hosted_bot_records.get(key)
    if record:
        record["desired_status"] = (
            "active" if str(desired_status).lower() == "active" else "stopped"
        )
    else:
        file_type = "py"
        for saved_name, saved_type in user_files.get(int(user_id), []):
            if saved_name == file_name:
                file_type = saved_type
                break
        save_hosted_bot(user_id, file_name, file_type, desired_status)
        return
    trigger_google_sheets_sync()


def remove_hosted_bot(user_id, file_name):
    hosted_bot_records.pop(_hosted_bot_key(user_id, file_name), None)
    trigger_google_sheets_sync()


def remove_user_file_db(user_id, file_name):
    if user_id in user_files:
        user_files[user_id] = [
            f for f in user_files[user_id] if f[0] != file_name
        ]
    remove_hosted_bot(user_id, file_name)


def add_active_user(user_id):
    active_users.add(user_id)
    record = _ensure_runtime_user(user_id)
    record["active"] = True
    record["updated_at"] = _now_iso()
    trigger_google_sheets_sync()


def save_subscription(user_id, plan_name, expiry):
    _ensure_runtime_user(user_id)
    user_subscriptions[user_id] = {"plan_name": plan_name, "expiry": expiry}
    user_records[user_id]["updated_at"] = _now_iso()
    trigger_google_sheets_sync()


def remove_subscription_db(user_id):
    user_subscriptions.pop(user_id, None)
    if user_id in user_records:
        user_records[user_id]["updated_at"] = _now_iso()
    trigger_google_sheets_sync()


# --- Google Sheets persistence ---
GOOGLE_SHEET_NAMES = ["Users", "BotConfig", "HostedBots", "Summary"]
GOOGLE_SHEET_HEADERS = {
    "Users": [
        "user_name", "username", "user_id", "balance", "plan", "expiry",
        "banned", "active", "user_type",
    ],
    "BotConfig": ["setting", "value_json"],
    "HostedBots": ["owner_id", "file_name", "file_type", "desired_status"],
    "Summary": ["metric", "value"],
}
GOOGLE_SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
google_auth_warning_printed = False


def google_sheets_configured():
    return bool(GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON)


def _read_service_account_info():
    raw = GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        return None
    try:
        if os.path.isfile(raw):
            with open(raw, "r", encoding="utf-8") as handle:
                return json.load(handle)
        if raw.startswith("{"):
            return json.loads(raw)
        return json.loads(base64.b64decode(raw).decode("utf-8"))
    except Exception as exc:
        raise ValueError(
            f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON/base64: {exc}"
        )


def _google_access_token():
    global google_auth_warning_printed
    try:
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        if not google_auth_warning_printed:
            logger.error(
                "Google Sheets needs google-auth. Install google-auth before starting."
            )
            google_auth_warning_printed = True
        return None
    info = _read_service_account_info()
    credentials = Credentials.from_service_account_info(
        info, scopes=GOOGLE_SHEET_SCOPES
    )
    credentials.refresh(Request())
    return credentials.token


def _google_api(method, url, token, payload=None, params=None):
    response = requests.request(
        method,
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        params=params,
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(
            f"Google Sheets API {response.status_code}: {response.text[:300]}"
        )
    return response.json() if response.content else {}


def _ensure_google_sheet_tabs(token):
    global google_sheet_tabs
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
    data = _google_api(
        "GET", base_url, token, params={"fields": "sheets.properties"}
    )
    google_sheet_tabs = {
        item.get("properties", {}).get("title")
        for item in data.get("sheets", [])
        if item.get("properties", {}).get("title")
    }
    missing = [
        name for name in GOOGLE_SHEET_NAMES if name not in google_sheet_tabs
    ]
    if missing:
        _google_api(
            "POST",
            f"{base_url}:batchUpdate",
            token,
            {
                "requests": [
                    {"addSheet": {"properties": {"title": name}}}
                    for name in missing
                ]
            },
        )
        google_sheet_tabs.update(missing)


def _sheet_rows(token, sheet_name):
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{GOOGLE_SHEET_ID}/values/{sheet_name}"
    )
    data = _google_api("GET", url, token)
    values = data.get("values", []) if isinstance(data, dict) else []
    if not values:
        return []
    headers = [str(value).strip() for value in values[0]]
    rows = []
    for raw_row in values[1:]:
        if not any(str(value).strip() for value in raw_row):
            continue
        rows.append({
            header: raw_row[index] if index < len(raw_row) else ""
            for index, header in enumerate(headers)
            if header
        })
    return rows


def _dedupe_user_rows(rows):
    result = {}
    for raw in rows if isinstance(rows, list) else []:
        if not isinstance(raw, dict):
            continue
        try:
            user_id = int(str(raw.get("user_id", "")).strip())
        except (TypeError, ValueError):
            continue
        if user_id <= 0:
            continue
        row = {
            "user_name": str(raw.get("user_name", "") or "")[:120],
            "username": _normalize_username(raw.get("username", ""))[:120],
            "user_id": user_id,
            "balance": _as_number(raw.get("balance"), 0.0),
            "plan": str(raw.get("plan", "") or ""),
            "expiry": str(raw.get("expiry", "") or ""),
            "banned": _as_bool(raw.get("banned")),
            "active": _as_bool(raw.get("active")),
            "user_type": str(raw.get("user_type", "") or ""),
        }
        # Last non-empty duplicate values win; duplicates never reach runtime.
        old = result.get(user_id, {})
        for key, value in row.items():
            raw_value = raw.get(key, "")
            if key in {"banned", "active", "balance"}:
                if str(raw_value).strip() == "" and key in old:
                    continue
                old[key] = value
            elif value not in ("", None):
                old[key] = value
        result[user_id] = old
    return result


def _restore_hosted_bot_rows(rows):
    """Restore file metadata and the desired running state from Google Sheets."""
    hosted_bot_records.clear()
    user_files.clear()
    for raw in rows or []:
        try:
            owner_id = int(str(raw.get("owner_id", "")).strip())
        except (TypeError, ValueError):
            continue
        file_name = os.path.basename(str(raw.get("file_name", "")).strip())
        if owner_id <= 0 or not file_name:
            continue
        file_type = "js" if str(raw.get("file_type", "")).lower() == "js" else "py"
        desired_status = (
            "active"
            if str(raw.get("desired_status", "")).lower().strip() == "active"
            else "stopped"
        )
        key = _hosted_bot_key(owner_id, file_name)
        hosted_bot_records[key] = {
            "owner_id": owner_id,
            "file_name": file_name,
            "file_type": file_type,
            "desired_status": desired_status,
        }
        user_files.setdefault(owner_id, [])
        if not any(item[0] == file_name for item in user_files[owner_id]):
            user_files[owner_id].append((file_name, file_type))


def _restore_from_google_rows(rows_by_sheet):
    global admin_ids, bot_locked, plans_runtime
    global payment_requests_runtime, next_payment_request_id

    restored_users = _dedupe_user_rows(rows_by_sheet.get("Users", []))
    user_records.clear()
    user_subscriptions.clear()
    active_users.clear()
    for user_id, row in restored_users.items():
        record = _ensure_runtime_user(
            user_id, row.get("user_name", ""), row.get("username", "")
        )
        record.update({
            "balance": _as_number(row.get("balance"), 0.0),
            "banned": bool(row.get("banned", False)),
            "active": bool(row.get("active", False)),
        })
        if record["active"]:
            active_users.add(user_id)
        expiry = _expiry_from_value(row.get("expiry"))
        if expiry:
            user_subscriptions[user_id] = {
                "plan_name": str(row.get("plan") or "Premium"),
                "expiry": expiry,
            }

    _restore_hosted_bot_rows(rows_by_sheet.get("HostedBots", []))

    config = {}
    for row in rows_by_sheet.get("BotConfig", []) or []:
        setting = str(row.get("setting", "") or "").strip()
        if not setting:
            continue
        raw_value = row.get("value_json", "")
        try:
            config[setting] = json.loads(raw_value)
        except (TypeError, ValueError):
            config[setting] = raw_value

    restored_admins = config.get("admin_ids")
    if isinstance(restored_admins, list):
        admin_ids = {OWNER_ID, ADMIN_ID}
        for value in restored_admins:
            try:
                admin_ids.add(int(value))
            except (TypeError, ValueError):
                continue
    bot_locked = _as_bool(config.get("bot_locked", False))
    plans_runtime = _canonicalize_plans(config.get("plans", []))

    payment_requests_runtime.clear()
    stored_requests = config.get("payment_requests", [])
    if isinstance(stored_requests, list):
        for item in stored_requests:
            if not isinstance(item, dict) or not item.get("request_id"):
                continue
            marker = str(item["request_id"])
            payment_requests_runtime[marker] = item
    numeric_ids = [
        int(item.get("request_id", 0))
        for item in payment_requests_runtime.values()
        if str(item.get("request_id", "")).isdigit()
    ]
    next_payment_request_id = max(numeric_ids or [0]) + 1


def _json_cell(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return "" if value is None else value


def _summary_rows():
    total_users = len(user_records)
    premium_users = sum(1 for uid in user_records if _user_is_premium(uid))
    return [
        {"metric": "total_users", "value": total_users},
        {"metric": "active_users", "value": len(active_users)},
        {"metric": "free_users", "value": max(total_users - premium_users, 0)},
        {"metric": "premium_users", "value": premium_users},
        {"metric": "banned_users", "value": sum(
            1 for row in user_records.values() if row.get("banned", False)
        )},
        {"metric": "total_uploaded_files", "value": sum(
            len(items) for items in user_files.values()
        )},
    ]


def _rows_for_google_sheets():
    users = [_user_row(user_id) for user_id in sorted(user_records)]
    settings = {
        "admin_ids": sorted(int(value) for value in admin_ids),
        "bot_locked": bool(bot_locked),
        "plans": _canonicalize_plans(plans_runtime),
        "payment_requests": list(payment_requests_runtime.values()),
    }
    config_rows = [
        {
            "setting": key,
            "value_json": json.dumps(
                value, ensure_ascii=False, sort_keys=True, default=str
            ),
        }
        for key, value in sorted(settings.items())
    ]
    hosted_bots = [
        hosted_bot_records[key]
        for key in sorted(hosted_bot_records)
    ]
    return {
        "Users": users,
        "BotConfig": config_rows,
        "HostedBots": hosted_bots,
        "Summary": _summary_rows(),
    }


def _rows_to_matrix(rows, sheet_name):
    headers = list(GOOGLE_SHEET_HEADERS[sheet_name])
    return [headers] + [
        [_json_cell(row.get(header, "")) for header in headers]
        for row in rows
    ]


def sync_to_google_sheets(force=False):
    global google_sheet_last_signature, google_sheet_last_error
    global google_sheet_initial_sync
    if not google_sheets_configured() or not google_sheet_data_loaded:
        return False
    try:
        rows_by_sheet = _rows_for_google_sheets()
        signature = hashlib.sha256(
            json.dumps(
                rows_by_sheet, ensure_ascii=False, sort_keys=True, default=str
            ).encode("utf-8")
        ).hexdigest()
        if not force and signature == google_sheet_last_signature:
            return True
        token = _google_access_token()
        if not token:
            return False
        _ensure_google_sheet_tabs(token)
        base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
        _google_api(
            "POST",
            f"{base_url}/values:batchClear",
            token,
            {"ranges": [f"{name}!A:ZZ" for name in GOOGLE_SHEET_NAMES]},
        )
        _google_api(
            "POST",
            f"{base_url}/values:batchUpdate",
            token,
            {
                "valueInputOption": "RAW",
                "data": [
                    {
                        "range": f"{name}!A1",
                        "values": _rows_to_matrix(rows_by_sheet[name], name),
                    }
                    for name in GOOGLE_SHEET_NAMES
                ],
            },
        )
        google_sheet_last_signature = signature
        google_sheet_last_error = ""
        if google_sheet_initial_sync:
            logger.info("Google Sheets sync is active.")
            google_sheet_initial_sync = False
        return True
    except Exception as exc:
        google_sheet_last_error = str(exc)
        if google_sheet_initial_sync:
            logger.error("Google Sheets sync is not ready: %s", exc)
            google_sheet_initial_sync = False
        return False


def load_google_sheet_data():
    global google_sheet_data_loaded, google_sheet_last_error
    global google_sheet_last_signature
    if not google_sheets_configured():
        google_sheet_last_error = (
            "Set GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON."
        )
        logger.warning("Google Sheets is not configured; no persistent data loaded.")
        return False
    try:
        token = _google_access_token()
        if not token:
            return False
        _ensure_google_sheet_tabs(token)
        rows_by_sheet = {
            name: _sheet_rows(token, name) for name in GOOGLE_SHEET_NAMES
        }
        _restore_from_google_rows(rows_by_sheet)
        google_sheet_data_loaded = True
        google_sheet_last_error = ""
        google_sheet_last_signature = None
        sync_to_google_sheets(force=True)
        logger.info(
            "Google Sheets data restored: %s users, %s plans.",
            len(user_records), len(plans_runtime),
        )
        return True
    except Exception as exc:
        google_sheet_last_error = str(exc)
        logger.error("Google Sheets initial load failed: %s", exc)
        return False


def trigger_google_sheets_sync():
    global google_sync_trigger_scheduled
    if not google_sheets_configured() or not google_sheet_data_loaded:
        return
    with google_sync_trigger_lock:
        if google_sync_trigger_scheduled:
            return
        google_sync_trigger_scheduled = True

    def _run():
        global google_sync_trigger_scheduled
        try:
            time.sleep(0.5)
            with google_runtime_lock:
                sync_to_google_sheets()
        finally:
            with google_sync_trigger_lock:
                google_sync_trigger_scheduled = False

    threading.Thread(target=_run, daemon=True).start()


def google_sheets_sync_thread():
    while True:
        try:
            with google_runtime_lock:
                if not google_sheet_data_loaded:
                    load_google_sheet_data()
                else:
                    sync_to_google_sheets()
        except Exception as exc:
            logger.warning("Google Sheets background sync failed: %s", exc)
        time.sleep(GOOGLE_SYNC_INTERVAL)


def get_google_sheet_status_text():
    if not google_sheets_configured():
        return (
            "📊 **GOOGLE SHEETS SYNC**\n\n"
            "Status: **NOT CONFIGURED**\n"
            "Set `GOOGLE_SHEET_ID` and `GOOGLE_SERVICE_ACCOUNT_JSON`."
        )
    status = "READY" if google_sheet_data_loaded and not google_sheet_last_error else "ERROR"
    detail = f"\n\nLast error: `{google_sheet_last_error[:300]}`" if google_sheet_last_error else ""
    return (
        "📊 **GOOGLE SHEETS SYNC**\n\n"
        f"Status: **{status}**\n"
        f"Tabs: `Users`, `BotConfig`, `HostedBots`, `Summary`\n"
        f"Auto sync: every `{GOOGLE_SYNC_INTERVAL:g}` seconds"
        f"{detail}"
    )


# --- Menu Creation ---
def create_reply_keyboard_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    layout_to_use = (
        ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC
        if user_id in admin_ids
        else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    )
    for row in layout_to_use:
        markup.add(*[types.KeyboardButton(text) for text in row])
    return markup


def create_admin_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ 𝗔𝗱𝗱 𝗣𝗹𝗮𝗻", callback_data="add_plan_init"),
        types.InlineKeyboardButton(
            "🗑️ 𝗠𝗮𝗻𝗮𝗴𝗲 𝗣𝗹𝗮𝗻𝘀", callback_data="manage_plans"
        ),
    )
    markup.add(
        types.InlineKeyboardButton(
            "💎 𝗔𝗱𝗱 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻", callback_data="add_subscription"
        ),
        types.InlineKeyboardButton(
            "❌ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗦𝘂𝗯", callback_data="remove_subscription"
        ),
    )
    markup.add(
        types.InlineKeyboardButton("👑 𝗔𝗱𝗱 𝗔𝗱𝗺𝗶𝗻", callback_data="add_admin"),
        types.InlineKeyboardButton(
            "➖ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗔𝗱𝗺𝗶𝗻", callback_data="remove_admin"
        ),
    )
    markup.add(
        types.InlineKeyboardButton("📣 𝗕𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁", callback_data="broadcast"),
        types.InlineKeyboardButton(
            "🔐 𝗟𝗼𝗰𝗸/𝗨𝗻𝗹𝗼𝗰𝗸", callback_data="toggle_lock"
        ),
    )
    markup.add(
        types.InlineKeyboardButton(
            "⚙️ 𝗥𝘂𝗻 𝗔𝗹𝗹 𝗦𝗰𝗿𝗶𝗽𝘁𝘀", callback_data="run_all_scripts"
        ),
        types.InlineKeyboardButton("📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀", callback_data="stats"),
    )
    markup.add(
        types.InlineKeyboardButton("🚫 𝗕𝗮𝗻/𝗨𝗻𝗯𝗮𝗻", callback_data="ban_user"),
        types.InlineKeyboardButton("📊 𝗦𝗵𝗲𝗲𝘁 𝗦𝘆𝗻𝗰", callback_data="google_status"),
    )
    return markup


# --- Core User Logic ---
def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = " ".join(
        part for part in (
            message.from_user.first_name or "",
            message.from_user.last_name or "",
        ) if part
    )

    update_user_profile(user_id, user_name, message.from_user.username)
    if is_user_banned(user_id) and user_id not in admin_ids:
        bot.send_message(
            chat_id,
            "🚫 **You are banned from using this bot.**",
            parse_mode="Markdown",
        )
        return

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ **Bot is temporarily locked by Admin.**")
        return

    if user_id not in active_users:
        add_active_user(user_id)

    if user_id == OWNER_ID:
        user_status = "👑 **Owner**"
    elif user_id in admin_ids:
        user_status = "🛡️ **Admin**"
    elif (
        user_id in user_subscriptions
        and user_subscriptions[user_id]["expiry"] > datetime.now()
    ):
        sub = user_subscriptions[user_id]
        days_left = (sub["expiry"] - datetime.now()).days
        user_status = f"💎 **{sub.get('plan_name', 'Premium')} Active** ({days_left} Days left)"
    else:
        user_status = "🆓 **No Active Plan**"

    welcome_msg = (
        f"✨ **𝗪𝗲𝗹𝗰𝗼𝗺𝗲, {user_name}!** ✨\n\n"
        f"🆔 **𝗬𝗼𝘂𝗿 𝗜𝗗:** `{user_id}`\n"
        f"🔰 **𝗦𝘁𝗮𝘁𝘂𝘀:** {user_status}\n"
        f"📁 **𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗱 𝗙𝗶𝗹𝗲𝘀:** `{get_user_file_count(user_id)}` / `{get_user_file_limit(user_id)}`\n\n"
        f"💡 **𝗛𝗼𝘀𝘁 & 𝗥𝘂𝗻 𝘆𝗼𝘂𝗿 𝗣𝘆𝘁𝗵𝗼𝗻 (.𝗽𝘆) & 𝗝𝗦 (.𝗷𝘀) 𝗯𝗼𝘁𝘀 𝟮𝟰/𝟳.**\n"
        f"👇 *Select an option from the menu below:* "
    )
    bot.send_message(
        chat_id,
        welcome_msg,
        reply_markup=create_reply_keyboard_main_menu(user_id),
        parse_mode="Markdown",
    )


def _logic_view_plans(message_or_call):
    chat_id = (
        message_or_call.chat.id
        if isinstance(message_or_call, telebot.types.Message)
        else message_or_call.message.chat.id
    )
    plans = get_all_plans()

    if not plans:
        bot.send_message(
            chat_id,
            "ℹ️ **বর্তমানে কোনো প্ল্যান উপলব্ধ নেই।**",
            parse_mode="Markdown",
        )
        return

    bot.send_message(
        chat_id, "💳 **𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗛𝗼𝘀𝘁𝗶𝗻𝗴 𝗣𝗹𝗮𝗻𝘀:**", parse_mode="Markdown"
    )

    # 🆕 প্রতিটি প্ল্যান আলাদা মেসেজ কার্ডে দেখানো হবে এবং নিজস্ব বাই বাটন থাকবে
    for plan in plans:
        plan_id, name, limit, price, duration, _ = plan
        usdt_price, formatted_price = parse_price_to_usdt(price)

        card_text = (
            f"📦 **𝗣𝗹𝗮𝗻:** `{name}`\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📁 **File Limit:** `{limit} Files`\n"
            f"⏱️ **Duration:** `{duration} Days`\n"
            f"💰 **Price:** `{formatted_price}`\n"
            f"👉 **Binance Pay-তে পেমেন্ট করতে হবে:** `{usdt_price} USDT`\n"
                f"🕐 **Payment review:** Admin manually approves your submitted TxID\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                f"🛒 Buy {name} ({usdt_price} USDT)",
                callback_data=f"buy_plan_{plan_id}",
            )
        )

        bot.send_message(chat_id, card_text, reply_markup=markup, parse_mode="Markdown")


def _logic_upload_file(message):
    user_id = message.from_user.id
    if is_user_banned(user_id) and user_id not in admin_ids:
        bot.reply_to(message, "🚫 **You are banned from using this bot.**", parse_mode="Markdown")
        return
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ **Bot is locked by Admin.**")
        return

    has_active_plan = False
    plan_name = "None"

    if user_id in admin_ids or user_id == OWNER_ID:
        has_active_plan = True
        plan_name = "Admin / Owner Unlimited"
    elif user_id in user_subscriptions:
        sub = user_subscriptions[user_id]
        if sub["expiry"] > datetime.now():
            has_active_plan = True
            plan_name = sub.get("plan_name", "Premium Plan")

    if not has_active_plan:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "💳 View Plans & Buy", callback_data="view_plans_cb"
            )
        )
        bot.reply_to(
            message,
            "❌ **আপনার কোন এক্টিভ প্ল্যান নেই!**\n\n"
            "ফাইল আপলোড করতে হলে প্রথমে একটি প্ল্যান সাবস্ক্রাইব করতে হবে। "
            "নিচের বাটনে ক্লিক করে আমাদের প্ল্যানগুলো দেখুন এবং আপনার পছন্দমতো প্ল্যান কিনুন।",
            reply_markup=markup,
            parse_mode="Markdown",
        )
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            f"✅ Continue with {plan_name}", callback_data="confirm_plan_upload"
        )
    )
    bot.reply_to(
        message,
        f"🔰 **𝗔𝗰𝘁𝗶𝘃𝗲 𝗣𝗹𝗮𝗻 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱:** `{plan_name}`\n\n"
        f"ফাইল আপলোড চালু করতে নিচের বাটনে সিলেক্ট করুন:",
        reply_markup=markup,
        parse_mode="Markdown",
    )


def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.reply_to(
            message,
            "📂 **Your Uploaded Files:**\n\n*(No files uploaded yet)*",
            parse_mode="Markdown",
        )
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = "🟢 Running" if is_running else "🔴 Stopped"
        btn_text = f"📄 {file_name} ({file_type}) - {status_icon}"
        token = _file_callback_token(user_id, file_name)
        markup.add(
            types.InlineKeyboardButton(
                btn_text, callback_data=f"file_ref_{token}"
            )
        )
    bot.reply_to(
        message,
        "📁 **𝗠𝗮𝗻𝗮𝗴𝗲 𝗬𝗼𝘂𝗿 𝗙𝗶𝗹𝗲𝘀:**",
        reply_markup=markup,
        parse_mode="Markdown",
    )


# --- Document Upload Processing ---
@bot.message_handler(content_types=["document"])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    doc = message.document

    update_user_profile(
        user_id,
        " ".join(
            part for part in (
                message.from_user.first_name or "",
                message.from_user.last_name or "",
            ) if part
        ),
        message.from_user.username,
    )
    add_active_user(user_id)
    if is_user_banned(user_id) and user_id not in admin_ids:
        bot.reply_to(message, "🚫 **You are banned from using this bot.**", parse_mode="Markdown")
        return

    if user_id not in admin_ids and user_id != OWNER_ID:
        if (
            user_id not in user_subscriptions
            or user_subscriptions[user_id]["expiry"] <= datetime.now()
        ):
            bot.reply_to(
                message,
                "❌ **আপনার কোন এক্টিভ প্ল্যান নেই! ফাইল আপলোড করতে প্ল্যান ক্রয় করুন।**",
                parse_mode="Markdown",
            )
            return

    file_name = doc.file_name
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in [".py", ".js", ".zip"]:
        bot.reply_to(
            message,
            "⚠️ **Only `.py`, `.js`, and `.zip` files are supported!**",
            parse_mode="Markdown",
        )
        return

    try:
        download_wait_msg = bot.reply_to(
            message,
            f"⏳ **Downloading `{file_name}`...**",
            parse_mode="Markdown",
        )
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)

        if user_id != OWNER_ID:
            is_safe, reason = scan_file_for_malware(
                downloaded_file_content, file_name, user_id
            )
            if not is_safe:
                bot.edit_message_text(
                    f"🚨 **Security Alert:** {reason}",
                    chat_id,
                    download_wait_msg.message_id,
                    parse_mode="Markdown",
                )
                return

        user_folder = get_user_folder(user_id)
        file_path = os.path.join(user_folder, file_name)
        with open(file_path, "wb") as f:
            f.write(downloaded_file_content)

        bot.edit_message_text(
            f"✅ **File `{file_name}` uploaded successfully!**",
            chat_id,
            download_wait_msg.message_id,
            parse_mode="Markdown",
        )

        if file_ext == ".js":
            save_user_file(user_id, file_name, "js")
            save_hosted_bot(user_id, file_name, "js", "active")
            threading.Thread(
                target=run_js_script,
                args=(file_path, user_id, user_folder, file_name, message),
            ).start()
        elif file_ext == ".py":
            save_user_file(user_id, file_name, "py")
            save_hosted_bot(user_id, file_name, "py", "active")
            threading.Thread(
                target=run_script,
                args=(file_path, user_id, user_folder, file_name, message),
            ).start()

    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** {str(e)}")


# --- Callback Routing ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data

    if user_id not in admin_ids and is_user_banned(user_id):
        bot.answer_callback_query(
            call.id,
            "🚫 You are banned from using this bot.",
            show_alert=True,
        )
        return

    if data == "view_plans_cb":
        bot.answer_callback_query(call.id)
        _logic_view_plans(call)

    elif data == "confirm_plan_upload":
        bot.answer_callback_query(call.id, "✅ Plan Verified!")
        bot.send_message(
            call.message.chat.id,
            "🚀 **এখন আপনার Python (.py), JS (.js) অথবা ZIP (.zip) ফাইল মেসেজে পাঠান।**",
            parse_mode="Markdown",
        )

    # --- Interactive Module Installer Handler ---
    elif data.startswith("instmod_"):
        _, owner_id, mod_name, fname = data.split("_", 3)
        if user_id != int(owner_id) and user_id not in admin_ids:
            bot.answer_callback_query(
                call.id,
                "❌ আপনি অন্য ইউজারের ফাইল কাস্টমাইজ করতে পারবেন না!",
                show_alert=True,
            )
            return

        bot.answer_callback_query(call.id)
        pkg_name = TELEGRAM_MODULES.get(mod_name.lower(), mod_name)
        ext = os.path.splitext(fname)[1].lower()

        status_msg = bot.send_message(
            call.message.chat.id,
            f"⏳ **`{pkg_name}` মডিউলটি ইনস্টল করা হচ্ছে...**",
            parse_mode="Markdown",
        )

        def do_pip_install():
            if ext == ".js":
                cmd = ["npm", "install", pkg_name]
            else:
                cmd = [sys.executable, "-m", "pip", "install", pkg_name]

            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                bot.edit_message_text(
                    f"✅ **`{pkg_name}` মডিউলটি সফলভাবে ইনস্টল হয়েছে!**\n🚀 ফাইলটি পুনরায় চালু করা হচ্ছে...",
                    call.message.chat.id,
                    status_msg.message_id,
                    parse_mode="Markdown",
                )
                time.sleep(1)
                ufolder = get_user_folder(int(owner_id))
                fpath = os.path.join(ufolder, fname)
                if ext == ".js":
                    run_js_script(
                        fpath, int(owner_id), ufolder, fname, call.message
                    )
                else:
                    run_script(
                        fpath, int(owner_id), ufolder, fname, call.message
                    )
            else:
                bot.edit_message_text(
                    f"❌ **ইনস্টলেশন ব্যর্থ হয়েছে!**\n\n```\n{res.stderr[:300]}\n```",
                    call.message.chat.id,
                    status_msg.message_id,
                    parse_mode="Markdown",
                )

        threading.Thread(target=do_pip_install).start()

    # --- Error Log Viewer Handler ---
    elif data.startswith("viewlog_"):
        _, owner_id, fname = data.split("_", 2)
        ufolder = get_user_folder(int(owner_id))
        log_fpath = os.path.join(
            ufolder, f"{os.path.splitext(fname)[0]}.log"
        )
        if os.path.exists(log_fpath):
            with open(log_fpath, "r", encoding="utf-8", errors="ignore") as f:
                logs = f.read()[-2000:]
            bot.send_message(
                call.message.chat.id,
                f"📜 **Error Log for `{fname}`:**\n\n```\n{logs if logs else 'No logs recorded.'}\n```",
                parse_mode="Markdown",
            )
        else:
            bot.answer_callback_query(
                call.id, "No log file found!", show_alert=True
            )

    # --- Manual Payment Submission Handlers ---
    elif data.startswith("buy_plan_"):
        plan_id = int(data.split("_")[2])
        plan = get_plan_by_id(plan_id)
        if not plan:
            bot.answer_callback_query(call.id, "Plan not found!")
            return

        bot.answer_callback_query(call.id)
        _, name, limit, price, duration, _ = plan

        usdt_price, formatted_price = parse_price_to_usdt(price)

        pay_msg = (
            f"💛 **Binance Pay Payment Process**\n\n"
            f"📌 **Selected Plan:** `{name}`\n"
            f"💰 **Total Price:** `{usdt_price} USDT` ({formatted_price})\n"
            f"⏱️ **Duration:** `{duration} Days`\n\n"
        )

        pay_msg += (
            f"👇 **পেমেন্ট করার নিয়ম:**\n"
            f"1️⃣ Binance App ➔ **Pay** ➔ **Send** অপশনে যান।\n"
            f"2️⃣ ঠিক **`{usdt_price} USDT`** নিচের Binance Pay ID-তে পাঠান:\n"
            f"🔸 **Binance Pay ID:** `{BINANCE_PAY_ID}`\n\n"
            f"3️⃣ পেমেন্ট শেষ হলে প্রাপ্ত **Order ID / Transaction ID** টি জমা দিন।\n"
            f"4️⃣ একজন Admin আপনার TxID দেখে ম্যানুয়ালি Approve বা Reject করবেন।"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "🔍 Order ID / TxID জমা দিন",
                callback_data=f"submit_txid_{plan_id}",
            )
        )
        bot.send_message(
            call.message.chat.id, pay_msg, reply_markup=markup, parse_mode="Markdown"
        )

    elif data.startswith("submit_txid_"):
        plan_id = int(data.split("_")[2])
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📩 **আপনার Binance Pay এর Order ID / Transaction ID টি মেসেজে লিখুন:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(
            msg, lambda m: process_payment_txid(m, plan_id)
        )

    elif data.startswith("approve_payment_") or data.startswith("reject_payment_"):
        if user_id not in admin_ids:
            bot.answer_callback_query(
                call.id, "❌ শুধুমাত্র Admin এই অনুরোধ review করতে পারবেন।", show_alert=True
            )
            return

        action, request_id_text = data.rsplit("_", 1)
        request_id = int(request_id_text)
        approve = action == "approve_payment"
        review_payment_request(call, request_id, approve)

    # --- Admin Callbacks ---
    elif data == "add_plan_init" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📝 **Enter Plan Details in format:**\n`Name | FileLimit | Price | DurationInDays | BuyLink`\n\n*Example (টাকায়):* `Basic | 5 | 500 BDT | 30 | https://t.me/shiyam744`\n*Example (ডলারে):* `VIP | 10 | 5 USDT | 30 | https://t.me/shiyam744`",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_add_plan)

    elif data == "manage_plans" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        plans = get_all_plans()
        if not plans:
            bot.send_message(call.message.chat.id, "No plans found.")
            return
        markup = types.InlineKeyboardMarkup()
        for p in plans:
            markup.add(
                types.InlineKeyboardButton(
                    f"🗑️ Delete {p[1]}", callback_data=f"del_plan_{p[0]}"
                )
            )
        bot.send_message(
            call.message.chat.id,
            "🗑️ **Select a Plan to Delete:**",
            reply_markup=markup,
        )

    elif data.startswith("del_plan_") and user_id in admin_ids:
        pid = int(data.split("_")[2])
        delete_plan_db(pid)
        bot.answer_callback_query(call.id, "Plan Deleted!")
        bot.send_message(call.message.chat.id, "✅ Plan successfully deleted.")

    elif data == "add_subscription" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "💎 **Enter User ID, Plan Name & Days:**\nFormat: `UserID PlanName Days`\n*Example:* `123456789 VIP 30`",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_add_subscription)

    elif data == "remove_subscription" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "❌ **Enter the User ID whose subscription should be removed:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_remove_subscription)

    elif data == "add_admin" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "👑 **Send the numeric Telegram User ID to add as Admin:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_add_admin)

    elif data == "remove_admin" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "➖ **Send the numeric Telegram User ID to remove from Admins:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_remove_admin)

    elif data == "ban_user" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "🚫 **Send a User ID to toggle Ban/Unban:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_toggle_ban)

    elif data == "google_status" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, get_google_sheet_status_text(), parse_mode="Markdown")

    elif data == "stats" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        stats = get_user_stats()
        bot.send_message(
            call.message.chat.id,
            "📊 **Bot Statistics**\n\n"
            f"👥 Total users: `{stats['total_users']}`\n"
            f"🟢 Active users: `{stats['active_users']}`\n"
            f"🆓 Free users: `{stats['free_users']}`\n"
            f"💎 Premium users: `{stats['premium_users']}`\n"
            f"🚫 Banned users: `{stats['banned_users']}`\n"
            f"📁 Current files: `{stats['total_files']}`",
            parse_mode="Markdown",
        )

    elif data == "run_all_scripts" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        started = 0
        for owner_id, files in list(user_files.items()):
            for fname, file_type in list(files):
                folder = get_user_folder(owner_id)
                path = os.path.join(folder, fname)
                if not os.path.exists(path) or is_bot_running(owner_id, fname):
                    continue
                if file_type == "js":
                    run_js_script(path, owner_id, folder, fname, call.message)
                else:
                    run_script(path, owner_id, folder, fname, call.message)
                started += 1
        bot.send_message(call.message.chat.id, f"✅ Started `{started}` script(s).", parse_mode="Markdown")

    elif data == "broadcast" and user_id in admin_ids:
        bot.answer_callback_query(call.id)
        msg = bot.send_message(
            call.message.chat.id,
            "📣 **Send the broadcast message:**",
            parse_mode="Markdown",
        )
        bot.register_next_step_handler(msg, process_broadcast)

    elif data == "toggle_lock" and user_id in admin_ids:
        global bot_locked
        bot_locked = not bot_locked
        trigger_google_sheets_sync()
        bot.answer_callback_query(call.id, f"Bot Locked: {bot_locked}")
        bot.send_message(
            call.message.chat.id,
            f"🔐 **Bot status changed to:** `{'Locked' if bot_locked else 'Unlocked'}`",
            parse_mode="Markdown",
        )

    # --- File Management Callbacks ---
    elif data.startswith("file_ref_") or data.startswith("file_"):
        if data.startswith("file_ref_"):
            token = data.split("_", 2)[2]
            owner_id, fname = _file_callback_target(token)
            if owner_id is None:
                bot.answer_callback_query(
                    call.id,
                    "This file menu expired. Please open Manage Files again.",
                    show_alert=True,
                )
                return
        else:
            # Backward compatibility for buttons created by an older bot
            # process before the short-token fix.
            _, owner_id, fname = data.split("_", 2)
            token = _file_callback_token(owner_id, fname)
        is_running = is_bot_running(int(owner_id), fname)
        markup = types.InlineKeyboardMarkup(row_width=2)
        if is_running:
            markup.add(
                types.InlineKeyboardButton(
                    "🛑 Stop", callback_data=f"stop_ref_{token}"
                )
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "▶️ Start", callback_data=f"start_ref_{token}"
                )
            )
        markup.add(
            types.InlineKeyboardButton(
                "🗑️ Delete", callback_data=f"del_ref_{token}"
            )
        )
        bot.send_message(
            call.message.chat.id,
            f"📄 **File:** `{fname}`\n🚦 Status: `{'Running' if is_running else 'Stopped'}`",
            reply_markup=markup,
            parse_mode="Markdown",
        )

    elif data.startswith("start_ref_") or data.startswith("start_"):
        if data.startswith("start_ref_"):
            token = data.split("_", 2)[2]
            owner_id, fname = _file_callback_target(token)
            if owner_id is None:
                bot.answer_callback_query(
                    call.id,
                    "This file action expired. Please open Manage Files again.",
                    show_alert=True,
                )
                return
        else:
            _, owner_id, fname = data.split("_", 2)
        owner_id = int(owner_id)
        folder = get_user_folder(owner_id)
        path = os.path.join(folder, fname)
        if not os.path.exists(path):
            bot.answer_callback_query(call.id, "File is missing.", show_alert=True)
            return
        if is_bot_running(owner_id, fname):
            bot.answer_callback_query(call.id, "Already running.")
            return
        file_type = "py"
        for saved_name, saved_type in user_files.get(owner_id, []):
            if saved_name == fname:
                file_type = saved_type
                break
        bot.answer_callback_query(call.id, "Starting...")
        if file_type == "js":
            run_js_script(path, owner_id, folder, fname, call.message)
        else:
            run_script(path, owner_id, folder, fname, call.message)
        set_hosted_bot_status(owner_id, fname, "active")

    elif data.startswith("stop_ref_") or data.startswith("stop_"):
        if data.startswith("stop_ref_"):
            token = data.split("_", 2)[2]
            owner_id, fname = _file_callback_target(token)
            if owner_id is None:
                bot.answer_callback_query(
                    call.id,
                    "This file action expired. Please open Manage Files again.",
                    show_alert=True,
                )
                return
        else:
            _, owner_id, fname = data.split("_", 2)
        skey = f"{owner_id}_{fname}"
        if skey in bot_scripts:
            kill_process_tree(bot_scripts[skey])
            del bot_scripts[skey]
        set_hosted_bot_status(int(owner_id), fname, "stopped")
        bot.answer_callback_query(call.id, "Stopped!")
        bot.send_message(
            call.message.chat.id,
            f"🛑 Script `{fname}` stopped.",
            parse_mode="Markdown",
        )

    elif data.startswith("del_ref_") or data.startswith("del_"):
        if data.startswith("del_ref_"):
            token = data.split("_", 2)[2]
            owner_id, fname = _file_callback_target(token)
            if owner_id is None:
                bot.answer_callback_query(
                    call.id,
                    "This file action expired. Please open Manage Files again.",
                    show_alert=True,
                )
                return
        else:
            _, owner_id, fname = data.split("_", 2)
        skey = f"{owner_id}_{fname}"
        if skey in bot_scripts:
            kill_process_tree(bot_scripts[skey])
            del bot_scripts[skey]
        remove_user_file_db(int(owner_id), fname)
        ufolder = get_user_folder(int(owner_id))
        fpath = os.path.join(ufolder, fname)
        if os.path.exists(fpath):
            os.remove(fpath)
        bot.answer_callback_query(call.id, "Deleted!")
        bot.send_message(
            call.message.chat.id,
            f"🗑️ File `{fname}` deleted.",
            parse_mode="Markdown",
        )


# --- Manual Payment Review ---
def review_payment_request(call, request_id, approve):
    """Approve or reject a pending payment request from an admin button."""
    request = get_payment_request(request_id)
    if not request:
        bot.answer_callback_query(call.id, "Payment request not found.", show_alert=True)
        return

    if request["status"] != "pending":
        bot.answer_callback_query(
            call.id,
            f"Already reviewed: {request['status'].title()}",
            show_alert=True,
        )
        return

    plan = get_plan_by_id(request["plan_id"])
    if not plan:
        bot.answer_callback_query(call.id, "The selected plan no longer exists.", show_alert=True)
        return

    _, plan_name, _, price, duration, _ = plan
    new_status = "approved" if approve else "rejected"
    if not mark_payment_request(request_id, new_status, call.from_user.id):
        bot.answer_callback_query(
            call.id, "This request was already reviewed by another admin.", show_alert=True
        )
        return

    if approve:
        expiry = datetime.now() + timedelta(days=duration)
        save_subscription(request["user_id"], plan_name, expiry)
        user_message = (
            f"🎉 **Payment approved!**\n\n"
            f"💎 **Plan:** `{plan_name}`\n"
            f"📅 **Expiry:** `{expiry.strftime('%Y-%m-%d %H:%M')}`\n\n"
            f"🚀 আপনার subscription চালু হয়েছে। এখন আপনি ফাইল আপলোড করতে পারবেন!"
        )
        admin_result = (
            f"✅ APPROVED\n"
            f"Request: #{request_id}\n"
            f"User ID: {request['user_id']}\n"
            f"Plan: {plan_name}\n"
            f"TxID: {request['tx_id']}\n"
            f"Expiry: {expiry.strftime('%Y-%m-%d %H:%M')}"
        )
        answer = "Payment approved."
    else:
        user_message = (
            f"❌ **Payment rejected.**\n\n"
            f"আপনার `{plan_name}` plan-এর payment একজন Admin reject করেছেন। "
            f"সঠিক payment details দিয়ে আবার চেষ্টা করুন অথবা Admin-এর সাথে যোগাযোগ করুন।"
        )
        admin_result = (
            f"❌ REJECTED\n"
            f"Request: #{request_id}\n"
            f"User ID: {request['user_id']}\n"
            f"Plan: {plan_name}\n"
            f"TxID: {request['tx_id']}"
        )
        answer = "Payment rejected."

    try:
        bot.send_message(request["user_id"], user_message, parse_mode="Markdown")
    except Exception:
        logger.warning("Could not notify user %s after payment review.", request["user_id"])

    bot.answer_callback_query(call.id, answer)
    try:
        bot.edit_message_text(
            admin_result,
            call.message.chat.id,
            call.message.message_id,
        )
    except Exception:
        bot.send_message(call.message.chat.id, admin_result)


def process_payment_txid(message, plan_id):
    """Create a pending request; an admin must verify the payment manually."""
    tx_id = (message.text or "").strip()
    user_id = message.from_user.id
    update_user_profile(
        user_id,
        " ".join(
            part for part in (
                message.from_user.first_name or "",
                message.from_user.last_name or "",
            ) if part
        ),
        message.from_user.username,
    )
    add_active_user(user_id)

    if not tx_id or len(tx_id) > 200:
        bot.reply_to(
            message,
            "❌ একটি সঠিক Order ID / Transaction ID দিন (সর্বোচ্চ ২০০ অক্ষর)।",
        )
        return

    plan = get_plan_by_id(plan_id)
    if not plan:
        bot.reply_to(message, "❌ প্ল্যান পাওয়া যায়নি!")
        return

    _, name, limit, price, duration, _ = plan
    usdt_price, formatted_price = parse_price_to_usdt(price)
    existing = get_payment_request_by_txid(tx_id)
    if existing:
        status_text = existing["status"].title()
        bot.reply_to(
            message,
            f"❌ এই Order ID / Transaction ID ইতিমধ্যে জমা হয়েছে।\n"
            f"বর্তমান status: **{status_text}**",
            parse_mode="Markdown",
        )
        return

    request_id = create_payment_request(user_id, plan_id, tx_id)
    if request_id is None:
        bot.reply_to(
            message,
            "❌ এই TxID ইতিমধ্যে অন্য একটি payment request-এ জমা হয়েছে।",
        )
        return

    bot.reply_to(
        message,
        f"⏳ **Payment request Pending**\n\n"
        f"📌 **Plan:** `{name}`\n"
        f"💰 **Amount:** `{usdt_price} USDT` ({formatted_price})\n"
        f"📑 **TxID:** `{tx_id}`\n\n"
        f"একজন Admin payment দেখে সিদ্ধান্ত নিলে আপনাকে জানানো হবে।",
        parse_mode="Markdown",
    )

    user_label = message.from_user.first_name or "Unknown user"
    if message.from_user.username:
        user_label += f" (@{message.from_user.username})"
    admin_alert = (
        f"🔔 NEW PAYMENT REQUEST — PENDING\n\n"
        f"Request: #{request_id}\n"
        f"User: {user_label}\n"
        f"User ID: {user_id}\n"
        f"Plan: {name}\n"
        f"Amount: {usdt_price} USDT ({formatted_price})\n"
        f"Binance Pay TxID: {tx_id}\n\n"
        f"Check your Binance Pay app, then choose Approve or Reject."
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "✅ Approve", callback_data=f"approve_payment_{request_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Reject", callback_data=f"reject_payment_{request_id}"
        ),
    )
    for admin_id in admin_ids:
        try:
            bot.send_message(admin_id, admin_alert, reply_markup=markup)
        except Exception:
            logger.warning("Could not send payment alert to admin %s.", admin_id)


def process_add_plan(message):
    try:
        parts = [p.strip() for p in message.text.split("|")]
        name, limit, price, duration, buy_link = (
            parts[0],
            int(parts[1]),
            parts[2],
            int(parts[3]),
            parts[4],
        )
        add_plan_db(name, limit, price, duration, buy_link)
        bot.reply_to(
            message,
            f"✅ **Plan `{name}` added successfully!**",
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Invalid Format! Error: {e}")


def process_add_subscription(message):
    try:
        parts = message.text.split()
        sub_uid, pname, days = int(parts[0]), parts[1], int(parts[2])
        exp = datetime.now() + timedelta(days=days)
        save_subscription(sub_uid, pname, exp)
        bot.reply_to(
            message,
            f"✅ **Subscription active for User `{sub_uid}` under Plan `{pname}` for {days} days!**",
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")


def _parse_user_id_message(message):
    value = (message.text or "").strip()
    if not value.isdigit():
        raise ValueError("User ID must be numeric.")
    return int(value)


def process_remove_subscription(message):
    try:
        user_id = _parse_user_id_message(message)
        remove_subscription_db(user_id)
        bot.reply_to(
            message,
            f"✅ Subscription removed for User `{user_id}`.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        bot.reply_to(message, f"❌ Error: {exc}")


def process_add_admin(message):
    try:
        new_admin = _parse_user_id_message(message)
        admin_ids.add(new_admin)
        trigger_google_sheets_sync()
        bot.reply_to(
            message,
            f"✅ User `{new_admin}` is now an Admin.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        bot.reply_to(message, f"❌ Error: {exc}")


def process_remove_admin(message):
    try:
        remove_id = _parse_user_id_message(message)
        if remove_id in {OWNER_ID, ADMIN_ID}:
            raise ValueError("The configured owner/admin cannot be removed.")
        admin_ids.discard(remove_id)
        trigger_google_sheets_sync()
        bot.reply_to(
            message,
            f"✅ User `{remove_id}` was removed from Admins.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        bot.reply_to(message, f"❌ Error: {exc}")


def process_toggle_ban(message):
    try:
        target_id = _parse_user_id_message(message)
        if target_id in {OWNER_ID, ADMIN_ID}:
            raise ValueError("The configured owner/admin cannot be banned.")
        record = _ensure_runtime_user(target_id)
        new_status = not bool(record.get("banned", False))
        set_user_banned(target_id, new_status)
        status_text = "BANNED 🚫" if new_status else "UNBANNED ✅"
        bot.reply_to(
            message,
            f"✅ User `{target_id}` has been {status_text}.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        bot.reply_to(message, f"❌ Error: {exc}")


def process_broadcast(message):
    text = (message.text or "").strip()
    if not text:
        bot.reply_to(message, "❌ Broadcast message cannot be empty.")
        return
    delivered = 0
    for target_id in list(active_users):
        try:
            if not is_user_banned(target_id):
                bot.send_message(target_id, text)
                delivered += 1
        except Exception:
            continue
    bot.reply_to(message, f"✅ Broadcast sent to `{delivered}` active user(s).", parse_mode="Markdown")


# --- Text Handler Mapping ---
BUTTON_MAPPING = {
    "✨ 𝗨𝗽𝗱𝗮𝘁𝗲𝘀 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 ✨": lambda m: bot.reply_to(
        m, f"📢 **Join channel:** {UPDATE_CHANNEL}"
    ),
    "🚀 𝗨𝗽𝗹𝗼𝗮𝗱 𝗙𝗶𝗹𝗲": _logic_upload_file,
    "🚀 𝗨𝗽𝗹𝗼𝗮d 𝗙𝗶𝗹𝗲": _logic_upload_file,
    "📁 𝗠𝗮𝗻𝗮𝗴𝗲 𝗙𝗶𝗹𝗲𝘀": _logic_check_files,
    "💳 𝗩𝗶𝗲𝘄 𝗣𝗹𝗮𝗻𝘀": _logic_view_plans,
    "⚡ 𝗦𝗽𝗲𝗲𝗱 & 𝗣𝗶𝗻𝗴": lambda m: bot.reply_to(
        m, "⚡ **Bot Latency:** `12 ms` (Server Active)"
    ),
    "📊 𝗕𝗼𝘁 𝗦𝘁𝗮𝘁𝘀": lambda m: bot.reply_to(
        m, f"📊 **Active Users:** `{len(active_users)}`"
    ),
    "💻 𝗧𝗲𝗿𝗺𝗶𝗻𝗮𝗹 𝗖𝗺𝗱": lambda m: bot.reply_to(m, "💻 Terminal ready."),
    "👑 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿": lambda m: bot.reply_to(
        m, f"👑 **Owner:** {YOUR_USERNAME}"
    ),
    "🛡️ 𝗔𝗱𝗺𝗶𝗻 𝗣𝗮𝗻𝗲𝗹": lambda m: bot.reply_to(
        m,
        "🛡️ **𝗔𝗱𝗺𝗶𝗻 𝗖𝗼𝗻𝘁𝗿𝗼𝗹 𝗣𝗮𝗻𝗲𝗹:**",
        reply_markup=create_admin_panel_inline(),
        parse_mode="Markdown",
    ),
}


@bot.message_handler(func=lambda m: m.text in BUTTON_MAPPING)
def handle_main_buttons(message):
    BUTTON_MAPPING[message.text](message)


@bot.message_handler(commands=["start"])
def start_cmd(message):
    _logic_send_welcome(message)


# --- Start ---
if __name__ == "__main__":
    logger.info("🤖 Starting Bot with Google Sheets persistence...")
    load_google_sheet_data()
    threading.Thread(target=google_sheets_sync_thread, daemon=True).start()
    keep_alive()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)