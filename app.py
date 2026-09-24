# -*- coding: utf-8 -*-

# --- Host dependency bootstrap ---
# The bot uses Google Sheets as its durable store.  Keep dependency setup
# compatible with the standalone app.py entry point.
import base64
import importlib.util
import subprocess
import sys

_HOST_DEPENDENCIES = (
    ("requests", "requests"),
    ("flask", "Flask"),
    ("psutil", "psutil"),
    ("telebot", "pyTelegramBotAPI"),
    ("google.auth", "google-auth"),
)


def _ensure_host_dependencies():
    missing_packages = []
    for import_name, package_name in _HOST_DEPENDENCIES:
        try:
            installed = importlib.util.find_spec(import_name) is not None
        except (ImportError, AttributeError, ValueError):
            installed = False
        if not installed and package_name not in missing_packages:
            missing_packages.append(package_name)
    if not missing_packages:
        return

    print(
        "Installing missing bot packages: " + ", ".join(missing_packages),
        flush=True,
    )
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input", "--prefer-binary",
            "--upgrade-strategy", "only-if-needed", *missing_packages,
        ],
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="ignore",
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "unknown pip error").strip()
        raise RuntimeError(
            "Automatic bot dependency installation failed for "
            + ", ".join(missing_packages)
            + "\n"
            + details[-3000:]
        )


_ensure_host_dependencies()

import telebot
import subprocess
import ast
import importlib.util
import os
import zipfile
import io
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
import psutil
import sqlite3
import json
import logging
import signal
import threading
import re
import sys
import atexit
import requests
import hashlib
import math
import mimetypes
import struct
from html import escape as html_escape
from threading import Thread
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import secrets
from types import SimpleNamespace

# --- Flask Keep Alive ---
from flask import Flask

app = Flask('')

@app.route('/')
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
# ==========================================
# ✅ স্টাইল ডিকশনারি
# ==========================================

STYLE_MAP = {
    'primary': 'primary',    # 🔵 নীল
    'danger': 'danger',    # 🔵 নীল
    'success': 'success',      # 🔵 নীল
}

def get_method_style(method_name):
    """মেথডের নাম অনুযায়ী স্টাইল রিটার্ন করুন"""
    return get_payment_method_config(method_name)["style"]
       
# ==========================================
# ✅ GLOBAL EMOJI IDs (COMPLETE LIST)
# ==========================================

# ------------------ BASIC EMOJIS ------------------
EMOJI_REJECT = "6052869226677410910"           # ❌
EMOJI_WARNING = "6053063247530039664"          # ⚠️
EMOJI_ROCKET_GENERIC = "6052879414339837562"   # 🚀 (legacy generic icon)
EMOJI_MONEY = "6084884131945125425"            # 💸
EMOJI_GIFT = "6071123877067494706"             # 🎁
EMOJI_TRASH = "6053400522721859262"            # 🗑️
EMOJI_MEGAPHONE = "6087114684555597113"        # 📢
EMOJI_UPLOAD = "6338935574967098253"           # 📤
EMOJI_FOLDER = "6338935574967098253"           # 📂
EMOJI_BALANCE = "6073556477824472025"          # 💰
EMOJI_ID = "6246674660927215020"               # 📋
EMOJI_PREMIUM = "6246919169120408471"          # 〽️
EMOJI_LIGHTNING = EMOJI_ROCKET_GENERIC         # ⚡ (legacy generic icon)
EMOJI_STATS = "6053216517732964810"            # 📊
EMOJI_CARD = "6237975191784266396"             # 💳
EMOJI_DEFAULT = EMOJI_CARD                     # 💳 fallback emoji
EMOJI_LOCK = "6052921672523061549"             # 🔒
EMOJI_UNLOCK = "6109531476083087296"           # 🔓
# File/bot status icons are fixed by the UI contract.  Do not replace these
# with the editable emoji settings: running is always the online icon and a
# stopped/offline file is always the offline icon.
EMOJI_GREEN = "6053400449707416241"            # online
EMOJI_RED = "6053134711490878159"              # offline
EMOJI_PHONE = "6111432544572414098"            # 📞
EMOJI_USERS = "6053026611459004128"            # 👥
EMOJI_FILE = "6338935574967098253"             # 📁
# Dedicated Premium Emoji for the upload/download progress indicator.
EMOJI_DOWNLOAD_PROGRESS = "6053323501073341449"
# Requested custom emoji for every crown/mukut label.
EMOJI_CROWN = "6338946058982267602"            # 👑
EMOJI_PLUS = "6339079894458179573"             # ➕
EMOJI_MINUS = "6052869226677410910"            # ➖
EMOJI_BACK = "6088898792495520717"             # 🔙 (Back - নতুন)
# Use a cleaner bookmark-style Premium icon for every displayed User ID.
EMOJI_USER_ID = "6052914628776697272"          # 🔖
EMOJI_USERNAME = "6053323372224323095"         # ✳️
EMOJI_HEART = "6086760852264850520"            # ❤️
EMOJI_CLOCK = "5206717831361602241"            # ⏰
EMOJI_BOT = "5355051922862653659"              # 🤖 supplied premium bot emoji
EMOJI_SMILE = "6053323372224323095"            # 😊
EMOJI_PIN = "6206190608432764318"              # 📌
# Dedicated Premium Emoji for the Support Link label in the link-setup reply.
EMOJI_SUPPORT_LINK = "6052964261418769099"
EMOJI_CALENDAR = "6141069777419900736"         # 📅
EMOJI_DATE = "6141159258768545795"             # 📆
EMOJI_HOURGLASS = "5206717831361602241"        # ⏳
EMOJI_STATUS = "6053216517732964810"           # 📊
EMOJI_FREE = "6273835720574505901"             # ⭐
EMOJI_STAR = "6158917750241632037"             # 🌟
EMOJI_SHIELD = "6111432544572414098"           # 🛡️
EMOJI_FREE_USER = "6273835720574505901"        # 🆓
# Dedicated custom emoji requested for the "Free User" status label.
EMOJI_FREE_USER_STATUS = "6275794758237426356"
EMOJI_CONFETTI = "6089263598427705764"         # 🎉
EMOJI_DOLLAR = "6237610939902858402"           # 💵
EMOJI_MOBILE = "6235336389647407554"           # 📱
EMOJI_RECEIPT = "6109432142079466939"          # 🧾
EMOJI_MONEY_BAG = "6073556477824472025"        # 🤑
EMOJI_POINT_DOWN = "6053078043692374997"       # 👇
EMOJI_REFRESH = "5206717831361602241"          # 🔄
EMOJI_STOP = EMOJI_RED                         # stopped/offline
EMOJI_BULB = "6109531476083087296"             # 💡
EMOJI_SAD = "6086760852264850520"              # 😞
EMOJI_BLOCK = "6052869226677410910"            # ⛔
EMOJI_DIAMOND = "6111432544572414098"          # 🔹
EMOJI_CIRCLE = "6273835720574505901"           # 🔸
EMOJI_QUESTION = "6246674660927215020"         # ❓
EMOJI_INFO = "6053323372224323095"             # ℹ️
EMOJI_ARROW_BACK = "6053169517905845173"       # ↩️
EMOJI_TARGET = "6109531476083087296"           # 🎯
EMOJI_RUNNING = "6052879414339837562"          # 🏃
EMOJI_TIMER = "5206717831361602241"            # ⏱️
EMOJI_TRAFFIC = "6052909083973918987"          # 🚦
EMOJI_USER_ICON = "6053026611459004128"        # 👤
# Requested Premium Emoji for the admin-only bot update/restart control.
EMOJI_UPDATE_BOT = "6109451886044124125"
# Fixed Premium emojis for the two "Running All Code" status messages.
EMOJI_CHECKING_SCRIPTS = "6206118633370818254"
EMOJI_ALL_SCRIPTS_STATUS = "6086976446738208892"

# ------------------ SUCCESS & DOWNLOAD EMOJIS ------------------
EMOJI_SUCCESS = "6246867522138674062"          # ✅ (Success)
EMOJI_DOWNLOAD = "6246867522138674062"         # ✅ (Download)
# These two IDs are fixed by the UI contract.  Do not resolve them through
# the editable emoji settings or through the rotating fallback pool.
EMOJI_VERIFY_BUTTON = "5866469651780736116"
EMOJI_ALL_CHANNEL_BUTTON = "6206267591426578467"
# Fixed Premium emojis for the Force Join admin toggle buttons.
EMOJI_FORCE_JOIN_ON = "6053400449707416241"
EMOJI_FORCE_JOIN_OFF = "6053134711490878159"
# Premium Emoji requested for the inline View Logs / Logs buttons.
EMOJI_VIEW_LOGS = "6053315100117309042"
# Use one consistent green Premium check everywhere a successful action is
# shown.  The old approve ID was a different check and made the UI look mixed.
EMOJI_APPROVE = EMOJI_SUCCESS

# ------------------ DEPOSIT EMOJI ------------------
EMOJI_DEPOSIT = "6073556477824472025"          # 💰 (Deposit)

# ------------------ PAYMENT METHOD EMOJIS ------------------
# bKash uses the verified card custom-emoji ID from the original emoji
# inventory.  Do not replace this with the generic money ID.
EMOJI_BKASH = "6237975191784266396"            # 💳
EMOJI_NAGAD = "6235336389647407554"            # 📱 (Nagad এর নিজস্ব ইমোজি - অপরিবর্তিত)
EMOJI_BINANCE = "6237610939902858402"          # 💵
EMOJI_ROCKET = "6235655011796261649"           # 🚀
EMOJI_UPAY = "5456547209862482913"  # Upay app premium emoji

# ------------------ GIFT BOX EMOJI ------------------
EMOJI_GIFT_BOX = "6071123877067494706"         # 🎁

# ------------------ SUBSCRIPTION EMOJIS ------------------
EMOJI_SUB_ADD = "6339079894458179573"          # ➕
EMOJI_SUB_REMOVE = "6052869226677410910"       # ➖
EMOJI_SUB_CHECK = EMOJI_SUCCESS               # ✅

# ------------------ NUMBER EMOJIS ------------------
EMOJI_NUM_1 = "6089071630569445363"            # 1️⃣
EMOJI_NUM_2 = "6089302304672978048"            # 2️⃣
EMOJI_NUM_3 = "6089140083758208081"            # 3️⃣
EMOJI_NUM_4 = "6088982806350795765"            # 4️⃣
EMOJI_NUM_5 = "6089048841472971583"            # 5️⃣
EMOJI_NUM_6 = "6088937992662029123"            # 6️⃣
EMOJI_NUM_7 = "6088870660459729339"            # 7️⃣
EMOJI_NUM_8 = "6086687477043565464"            # 8️⃣
EMOJI_NUM_9 = "6089331218392813822"            # 9️⃣
EMOJI_NUM_10 = "6089263598427705764"           # 🔟

# ------------------ ADMIN PANEL EMOJIS ------------------
EMOJI_UPDATE_CHANNEL_ADMIN = "6109451886044124125"
EMOJI_CHECK_FILE_ADMIN = "6338935574967098253"
EMOJI_UPLOAD_FILE_ADMIN = "6338935574967098253"
EMOJI_BOT_SPEED_ADMIN = "6052879414339837562"
EMOJI_STATISTICS_ADMIN = "6053216517732964810"
EMOJI_SUBSCRIPTION_ADMIN = "6141069777419900736"
EMOJI_LOCK_BOT_ADMIN = "6052921672523061549"
EMOJI_RUNNING_ALL_ADMIN = "6053128350644311646"
EMOJI_GX_ADMIN_PANEL = "6052909083973918987"
EMOJI_BAN_UNBAN = "6052902989415324360"
EMOJI_ALL_USERS = "6053026611459004128"
EMOJI_ALL_FILES = "6338935574967098253"
EMOJI_STOP_DELETE = "6053400522721859262"
EMOJI_ADMIN_PANEL = "6052909083973918987"
EMOJI_SET_LIMIT = "6053063247530039664"
EMOJI_SET_PREMIUM = "6141159258768545795"
EMOJI_DEPOSITE_METHOD = "6053314026375485069"
EMOJI_GROUP_SET = "6052886672834566125"
EMOJI_BACK_BUTTON = "6053169517905845173"
EMOJI_SHOW_BAN = "6053376986301078841"
EMOJI_BAN_USER = "6052902989415324360"
EMOJI_UNBAN_USER = "5866469651780736116"
EMOJI_REMOVE_ADMIN = "6052869226677410910"
EMOJI_ADD_ADMIN = "6339079894458179573"
EMOJI_SHOW_ADMINS = "6053323372224323095"
EMOJI_DEPOSIT_REQUEST = "6053234303192537471"
EMOJI_BUY_PLAN = "6053234303192537471"
EMOJI_DEPOSIT_MONEY = "6084884131945125425"

# ------------------ USER INTERFACE EMOJIS ------------------
EMOJI_UPDATE_CHANNEL_USER = "6109451886044124125"
EMOJI_UPLOAD_FILE_USER = "6338935574967098253"
EMOJI_CHECK_FILE_USER = "6338935574967098253"
EMOJI_DEPOSIT_USER = "6084884131945125425"
EMOJI_PROFILE_USER = "6312024679984929396"
EMOJI_PREMIUM_PLAN_USER = "6246919169120408471"
# Telegram renders this custom emoji before the Support reply-keyboard label.
# The official blue/green button colour comes from the button's `style` field.
EMOJI_SUPPORT = EMOJI_PHONE
EMOJI_REFERRAL = EMOJI_USERS
EMOJI_FREE_HOST = EMOJI_BOT
EMOJI_REFERRAL_ADMIN = EMOJI_GIFT
EMOJI_FREE_HOST_ADMIN = EMOJI_BOT

# ------------------ PLAN EMOJIS ------------------
EMOJI_PLAN_ICON = "6052991826518873591"
EMOJI_FILE_ICON = "6338935574967098253"
EMOJI_DAY_ICON = "6141069777419900736"
EMOJI_PRICE_ICON = "6073556477824472025"
EMOJI_CURRENT_PLAN = "6246919169120408471"
EMOJI_SELECT_PLAN = "6052973985224728368"
EMOJI_BASIC_PLAN = "6052991826518873591"
EMOJI_VIP1_PLAN = "6082146339402029076"
EMOJI_VIP2_PLAN = "6163695166919022681"

# ------------------ MAIN EMOJI ------------------
CUSTOM_EMOJI_ID = "6087114684555597113"
# Dedicated Premium Emoji for the "Testing speed..." indicator.
EMOJI_BOT_SPEED = "6071051768861562054"


def free_user_status_label(expired=False):
    """Return the Free User label with its dedicated custom emoji."""
    suffix = " (Expired Sub)" if expired else ""
    return (
        f'<tg-emoji emoji-id="{EMOJI_FREE_USER_STATUS}">⭐</tg-emoji>'
        f" Free User{suffix}"
    )


def balance_emoji_tag():
    """Return the requested custom emoji for every displayed balance label."""
    return f'<tg-emoji emoji-id="{EMOJI_BALANCE}">💰</tg-emoji>'


def price_emoji_tag():
    """Return the requested custom emoji for price/value labels."""
    return f'<tg-emoji emoji-id="{EMOJI_PRICE_ICON}">💰</tg-emoji>'


EMOJI_PREMIUM_USER = "6158917750241632037"


def premium_user_status_label(bengali=False):
    """Return the Premium user status with its dedicated custom emoji."""
    label = "প্রিমিয়াম" if bengali else "Premium"
    return f'<tg-emoji emoji-id="{EMOJI_PREMIUM_USER}">🌟</tg-emoji> {label}'


def premium_plan_emoji_tag():
    """Return the fixed Premium emoji used before Premium Plan labels."""
    return f'<tg-emoji emoji-id="{EMOJI_PREMIUM}">〽️</tg-emoji>'


def pin_emoji_tag():
    """Return the dedicated Premium pin used for number/ID labels."""
    return f'<tg-emoji emoji-id="{EMOJI_PIN}">📌</tg-emoji>'


def private_channel_emoji_tag():
    """Return the Premium shield used for private-channel instructions."""
    return f'<tg-emoji emoji-id="{EMOJI_SHIELD}">🛡️</tg-emoji>'


def support_link_emoji_tag():
    """Return the dedicated Premium emoji used before Support Link."""
    return f'<tg-emoji emoji-id="{EMOJI_SUPPORT_LINK}">📞</tg-emoji>'


def status_emoji_tag():
    """Return the requested custom emoji for every displayed status label."""
    return f'<tg-emoji emoji-id="{EMOJI_STATUS}">📊</tg-emoji>'


def checking_scripts_emoji_tag():
    """Return the fixed Premium emoji before the checking status."""
    return f'<tg-emoji emoji-id="{EMOJI_CHECKING_SCRIPTS}">🟢</tg-emoji>'


def all_scripts_status_emoji_tag():
    """Return the fixed Premium emoji before the all-scripts status."""
    return f'<tg-emoji emoji-id="{EMOJI_ALL_SCRIPTS_STATUS}">🟢</tg-emoji>'


def bot_speed_emoji_tag():
    """Return the Premium Emoji shown before the speed-test status."""
    return f'<tg-emoji emoji-id="{EMOJI_BOT_SPEED}">⚡</tg-emoji>'


def download_progress_emoji_tag():
    """Return the Premium Emoji shown while a user file is downloading."""
    return f'<tg-emoji emoji-id="{EMOJI_DOWNLOAD_PROGRESS}">⏳</tg-emoji>'


def profile_emoji_tag():
    """Return the requested custom emoji for profile/name labels."""
    return f'<tg-emoji emoji-id="{EMOJI_PROFILE_USER}">👤</tg-emoji>'


def bot_emoji_tag():
    """Return the same bot icon used by the welcome message."""
    return f'<tg-emoji emoji-id="{EMOJI_BOT}">🤖</tg-emoji>'


def green_on_emoji_tag():
    """Return the Premium green-on/success indicator."""
    return f'<tg-emoji emoji-id="{EMOJI_GREEN}">🟢</tg-emoji>'


def lock_emoji_tag():
    """Return the fixed lock icon used by the access-lock heading."""
    return f'<tg-emoji emoji-id="{EMOJI_LOCK}">🔒</tg-emoji>'


# আপনার ফাইলের ইমোজি ডিকশনারির পরে বসান
# ~লাইন 400-450 এর মধ্যে (GLOBAL_EMOJI_IDS এর পরে)

# ==========================================
# ✅ পেমেন্ট মেথড কনফিগারেশন
# ==========================================

PAYMENT_METHOD_CONFIG = {
    'bkash': {
        'emoji': '💳',
        'style': 'danger',
        'emoji_id': EMOJI_BKASH,
        'label': 'bKash'
    },
    'nagad': {
        'emoji': '📱',
        'style': 'primary',
        'emoji_id': EMOJI_NAGAD,
        'label': 'Nagad'
    },
    'rocket': {
        'emoji': '🚀',
        'style': 'danger',
        'emoji_id': EMOJI_ROCKET,
        'label': 'Rocket'
    },
    'upay': {
        'emoji': '🆔',
        'style': 'primary',
        'emoji_id': EMOJI_UPAY,
        'label': 'Upay'
    },
    'binance': {
        'emoji': '💵',
        'style': 'danger',
        'emoji_id': EMOJI_BINANCE,
        'label': 'Binance'
    }
}

def get_payment_method_config(method_name):
    """মেথডের নাম অনুযায়ী কনফিগ রিটার্ন করুন"""
    method_key = str(method_name or "").strip().lower()
    for key, config in PAYMENT_METHOD_CONFIG.items():
        if key in method_key:
            return config
    return {
        'emoji': '💳',
        'style': 'success',
        'emoji_id': EMOJI_DEFAULT,
        'label': str(method_name or 'Payment')
    }


def get_payment_method_label(method_name):
    """Return one stable display label for a known payment method."""
    config = get_payment_method_config(method_name)
    return config.get("label") or str(method_name or "Payment").strip()


def get_payment_method_emoji(method_name):
    """Return the configured Premium emoji tag for a payment method."""
    config = get_payment_method_config(method_name)
    return (
        f'<tg-emoji emoji-id="{config["emoji_id"]}">'
        f'{config["emoji"]}</tg-emoji>'
    )

# ==========================================
# ✅ GLOBAL BODY EMOJIS (সম্পূর্ণ)
# ==========================================
GLOBAL_BODY_EMOJIS = {
    # Basic Emojis
    "✅": EMOJI_DOWNLOAD,
    "❌": EMOJI_REJECT,
    "⚠️": EMOJI_WARNING,
    "🚨": EMOJI_WARNING,
    "🚀": EMOJI_ROCKET,
    "💸": EMOJI_MONEY,
    "🎁": EMOJI_GIFT,
    "🗑": EMOJI_TRASH,
    "📢": EMOJI_MEGAPHONE,
    "📤": EMOJI_UPLOAD,
    "📄": EMOJI_FILE,
    "📂": EMOJI_FOLDER,
    "💰": EMOJI_DEPOSIT,
    "📋": EMOJI_ID,
    "〽️": EMOJI_PREMIUM,
    "⚡": EMOJI_LIGHTNING,
    "📊": EMOJI_STATS,
    "💳": EMOJI_CARD,
    "🔒": EMOJI_LOCK,
    "🟢": EMOJI_GREEN,
    "🔴": EMOJI_RED,
    "📞": EMOJI_PHONE,
    "👥": EMOJI_USERS,
    "📁": EMOJI_FILE,
    "👑": EMOJI_CROWN,
    "➕": EMOJI_PLUS,
    "➖": EMOJI_MINUS,
    "🔙": EMOJI_BACK,
    "🆔": EMOJI_USER_ID,
    "✳️": EMOJI_USERNAME,
    "❤️": EMOJI_HEART,
    "⏰": EMOJI_CLOCK,
    "🤖": EMOJI_BOT,
    "😊": EMOJI_SMILE,
    "📌": EMOJI_PIN,
    "📅": EMOJI_CALENDAR,
    "📆": EMOJI_DATE,
    "⏳": EMOJI_HOURGLASS,
    "🔰": EMOJI_STATUS,
    "⭐": EMOJI_FREE,
    "🌟": EMOJI_STAR,
    "🛡️": EMOJI_SHIELD,
    "🆓": EMOJI_FREE_USER,
    "🎉": EMOJI_CONFETTI,
    "💵": EMOJI_DOLLAR,
    "📱": EMOJI_MOBILE,
    "🧾": EMOJI_RECEIPT,
    "🤑": EMOJI_MONEY_BAG,
    "👇": EMOJI_POINT_DOWN,
    "🔄": EMOJI_REFRESH,
    "⏹️": EMOJI_STOP,
    "🔓": EMOJI_UNLOCK,
    "💡": EMOJI_BULB,
    "😞": EMOJI_SAD,
    "⛔": EMOJI_BLOCK,
    "🔹": EMOJI_DIAMOND,
    "🔸": EMOJI_CIRCLE,
    "❓": EMOJI_QUESTION,
    "ℹ️": EMOJI_INFO,
    "🗑": EMOJI_TRASH,  # "6053400522721859262"
    "↩️": EMOJI_ARROW_BACK,
    "🎯": EMOJI_TARGET,
    "🏃": EMOJI_RUNNING,
    "⏱️": EMOJI_TIMER,
    "🚦": EMOJI_TRAFFIC,
    "👤": EMOJI_USER_ICON,
}

# IDs supplied in the companion emoji list.  Keep the IDs already configured
# above unchanged; only emojis that were missing from the bot are added here.
SUPPLIED_PREMIUM_EMOJI_MAP = {
    '✨': '6249255481005575387',
    '👍': '6183943695746732556',
    '⭐': '6183661284467152997',
    '❤': '6185719454270231467',
    '🙂': '6186170065059058057',
    '💫': '6185739709335998839',
    '😽': '6183997331298325247',
    '😎': '6183814584734848347',
    '🦆': '6186020952384475802',
    '🦉': '6186045884669628967',
    '😊': '6183512317821457841',
    '🤑': '6186175669991379791',
    '🎆': '6183456844023862509',
    '⚡': '6183978600945947836',
    '😍': '6186026132115034887',
    '🔜': '6185915377793374304',
    '🦖': '6186233896863011865',
    '🍂': '6186176846812418718',
    '💸': '6185701917918763252',
    '🐞': '6185942006590608576',
    '🔪': '6188087407179470181',
    '😋': '6188420095346217764',
    '❌': '6188343249791358585',
    '✅': '6188038822509418008',
    '🌟': '6188404727953232658',
    '📣': '6188038212624062387',
    '🖼': '6188447235244562676',
    '😭': '6188347695082509858',
    '🎁': '6188464883265181261',
    '🙏': '6188221998569624607',
    '💀': '6190253496625796044',
    '🤩': '6190477479170282300',
    '⬇️': '6233317712068613378',
    '💎': '6233302765582424442',
    '🥷': '6233527959307688784',
    '➡️': '6233035687336089620',
    '🐼': '6233287728901921071',
    '💯': '6233437704864929299',
    '✔': '6233153665792742268',
    '😞': '6233136657722251031',
    '🥳': '6235612354181080084',
    '🏆': '6235422679835350879',
    '😓': '6260478625687018336',
    '🔥': '6260156941226480954',
    '🫦': '6260073653220675991',
    '▶️': '6260390956814573101',
    '😃': '6260540279942550766',
    '😈': '6260265754222924781',
    '😂': '6266847228963329610',
    '🦸': '6269279310029265574',
    '👎': '6337081879967044997',
    '⚡️': '6337107731375199009',
    '✔️': '6336628528989083013',
    '⭐️': '6336639073133794426',
    '👁': '6336887317948536124',
    '🍸': '6337057364293719177',
    '🗓': '6336848409839801489',
    '📌': '6111410240807245099',
    '🚬': '6109170716010091984',
    '🗿': '6109238713932323725',
    '❤️‍🔥': '6109348016555038383',
    '☠️': '6109451886044124125',
    '👆': '6111443144551699001',
    '🪶': '6109275865399432385',
    '🐦': '6109491532887235167',
    '🤡': '6109353007307037236',
    '🦁': '6109269040696400224',
    '😶': '6109210444457581233',
    '👑': '6109401652106630836',
    '🎤': '6109651730872408665',
    '🎯': '6109432142079466939',
    '🌐': '6111896830537111232',
    '☄️': '6109464955629606843',
    '1️⃣': '6109333310587018875',
    '2️⃣': '6111445103056786552',
    '3️⃣': '6111929373504312169',
    '🎈': '6111622644119902458',
    '🧁': '6109669018115773789',
    '🌚': '6109305698242271469',
    '🤭': '6109215430914610696',
    '😨': '6109587113089439675',
    '📈': '6109418703126796249',
    '🤦‍♂️': '6109264367771980661',
    '⛓': '6111396350883010682',
    '❄️': '6109347707317393978',
    '🎄': '6109166803294885045',
    '😄': '6109169599318594868',
    '🚦': '6116255930284775416',
    '🌹': '6116430525000324744',
    '💕': '6116373672518227890',
    '🌕': '6115935547199329919',
    '📍': '6161188739969194553',
    '👀': '6053362469311617342',
    '🛍': '6339201691140758295',
    '⛔️': '6053376986301078841',
    '🚫': '6052902989415324360',
    '❗️': '6053062818033309122',
    '‼️': '6053178490092525561',
    '⁉️': '6053354746960419401',
    '❓': '6339378519239303549',
    '⚠️': '6052867933892254014',
    '💬': '6052964261418769099',
    '💭': '6053074925546118479',
    '📊': '6053234303192537471',
    '🔼': '6053325330729409422',
    '🔽': '6053078043692374997',
    '🕯': '6339230892623403884',
    '📉': '6053183296160930683',
    '🆒': '6053030717447739471',
    '🔔': '6053142399482339205',
    '🥸': '6053117209499146201',
    '💵': '6053104294532487625',
    '💱': '6053387526150823179',
    '🔴': '6053134711490878159',
    '🟢': '6053400449707416241',
    '💥': '6052973985224728368',
    '🎙': '6053125112238971301',
    '🤫': '6053364784298991089',
    '🗣️': '6338899694810307622',
    '🔍': '6053117952528493140',
    '🛡': '6052869252447215120',
    '🔗': '6052886672834566125',
    '🖥': '6338935574967098253',
    '©': '6338890095558400290',
    'ℹ️': '6053028307971085979',
    '⏸': '6052878855994089809',
    '🔄': '6053225373955530616',
    '🔝': '6052871610384260126',
    '🆕': '6339306810465327721',
    '➕': '6339079894458179573',
    '🗑': '6053400522721859262',
    '🔖': '6052914628776697272',
    '✉️': '6053193097276298985',
    '🔒': '6052921672523061549',
    '😮': '6053388733036631565',
    '📎': '6339251525646293192',
    '⚙️': '6053063247530039664',
    '🎮': '6052909083973918987',
    '🔈': '6053318901163365600',
    '⌛': '6053323501073341449',
    '☀️': '6053077996447734125',
    '🌧': '6053247261108873398',
    '🌛': '6053100162773946866',
    '😀': '5451709985765468632',
    '😁': '5219675837887956268',
    '😅': '5393596088953349309',
    '🙃': '5456174445355875099',
    '🫠': '5222202120471591480',
    '😉': '5458394638505223612',
    '😇': '5341350410252723241',
    '🥰': '5456149049214249060',
    '😘': '5458421812763307254',
    '🥲': '5202204379079260712',
    '🤪': '5361761791355398330',
    '😝': '5237695957293875263',
    '🤗': '5210905596273905344',
    '🫢': '5201817814842755281',
    '🤔': '5449875850046481967',
    '🫡': '5382224089295365367',
    '🤐': '5447621198374511640',
    '🤨': '5456304325166900944',
    '😐': '5438274168422409988',
    '😑': '5335071013447158323',
    '🫥': '5283276370737119006',
    '😶‍🌫️': '5238020759900668600',
    '😏': '5445091140514620351',
    '🙄': '5226962730941955595',
    '😬': '5219860366862862672',
    '🤥': '5235516089592463902',
    '🫨': '5330188279876700094',
    '😔': '5458779239941681169',
    '🤤': '5404654779337034132',
    '😴': '5346167851730348282',
    '🤒': '5463232030105945136',
    '🤕': '5467629518271299429',
    '🤢': '5474215257914232160',
    '🤮': '5339216460046673964',
    '🤧': '5303081830738571591',
    '🥵': '5321160408944360420',
    '🥶': '5305555542922510469',
    '🥴': '5379743075667035082',
    '😵': '5386757912607599167',
    '😵‍💫': '5314329894820258428',
    '🤯': '5456384164313966322',
    '🧐': '5402461597237004802',
    '🫤': '5344061947660748948',
    '☹️': '5436062865855359364',
    '😳': '5438239044179863743',
    '🥺': '5321259601214062502',
    '🥹': '5404737650731007282',
    '😢': '5456218262612223748',
    '😱': '5449701482964198097',
    '🥱': '5404723975555138856',
    '😤': '5379725114113805128',
    '😡': '5314766512605634930',
    '😠': '5334549028891796220',
    '🤬': '5220139887629453156',
    '👿': '5226469187660038941',
    '💩': '5372829526940197440',
    '👻': '5305388752162539722',
    '👽': '5307670152890826839',
    '👾': '5337037846475720165',
    '🤖': '5355051922862653659',
    '💔': '5445040416950856638',
    '❤️': '5442678635909621223',
    '👋': '5458904472598095631',
    '👌': '5382026293166489702',
    '🐶': '5337047059180566409',
    '🐱': '5336985572428757981',
    '🍄': '5364160968676883257',
    '✈️': '5372849966689566579',
    '🚀': '5372917041193828849',
    '🌝': '5346030490086291331',
    '🎃': '5368309348739074032',
    '🔙': '5352759161945867747',
    '🤟': '5463412289883353404',
    '🤝': '5463256910851546817',
    '🗡': '5463277406435422003',
    '🌡': '5463054218459884779',
    '👉': '5463392464314315076',
    '💊': '5463081281048818043',
    '⚰️': '5463186335948878489',
    '⬆️': '5463122435425448565',
    '🔓': '5465443379917629504',
    '🪙': '5463046637842608206',
    '🛠': '5462921117423384478',
    '💪': '5463413771647069835',
    '🎣': '5463406036410969564',
    '⏫': '5462995330163289902',
    '🙈': '5463345378587849154',
    '🖕': '5462957817918926146',
    '📦': '5463172695132745432',
    '🔮': '5463092727136661235',
    '📀': '5462956611033117422',
    '🔇': '5462990730253319917',
    '🎂': '5454089058345042483',
    '⌛️': '5454415424319931791',
    '☝️': '5453958478454341679',
    '🧙‍♀️': '5454136337345037322',
    '👥': '5453957997418004470',
    '🍽': '5454246314277619140',
    '⚔️': '5454014806950429357',
    '👏': '5454092060527181056',
    '🔋': '5454125707300978880',
    '🔫': '5454177848203951217',
    '🕹': '5453921696354419743',
    '🚑': '5453870826761765894',
    '🪖': '5454168390685965478',
    '✋': '5454380420336466255',
    '🎖': '5229045747130843073',
    '🧠': '5226639745106330551',
    '💣': '5226813248900187912',
    '🌜': '5226662903569989373',
    '🛒': '5226656353744862682',
    '0️⃣': '5226929552319594190',
    '💋': '5253922906378881072',
    '🙅‍♂️': '5258160767789711124',
    '⏱': '5373236586760651455',
    '🤙': '5373110220232870002',
    '💰': '5375312095346704820',
    '🚩': '5373304760776541441',
    '😧': '5375331860786200544',
    '🤜': '5375161616872520280',
    '🥂': '6311803154161737307',
    '🆗': '6314082948572256406',
    '☃️': '6312287879875796575',
    '🍪': '6314402846326397461',
    '🛷': '6314165253030550051',
    '🪩': '6311906495369845385',
    '🧝': '6314087325143933468',
    '💙': '6314514038734725052',
    '🐦‍⬛️': '6314073984975510060',
    '😥': '6314499586169773517',
    '🍾': '6312090680747366910',
    '🪅': '6312248752723729881',
    '🧹': '6314192620562161224',
    '🍲': '6311853542718053364',
    '🎉': '6314309731435420506',
    '🍃': '6314447153209023665',
    '🌈': '6314395557766896547',
    '🍑': '6312322475837366163',
    '🍭': '6312130327590477773',
    '💍': '6314596630955826336',
    '⛸': '6311819402023017547',
    '💌': '6314258015734211084',
    '🪦': '6314068925504036336',
    '💐': '6312269115163680485',
    '💃': '6311821931758755346',
    '🌺': '6314124738604048014',
    '🌩': '6312068995457490518',
    '🦋': '6311921171273096723',
    '❗': '6314179022695702286',
    '👅': '6314440938391347325',
    '💡': '6314080328642207844',
    '💝': '6312092570532978030',
    '🎏': '6314493388531965543',
    '🧶': '6311947392048438021',
    '🪟': '6314178253896555770',
    '🧩': '6314333572798881885',
    '🏡': '6311837926216965770',
    '☕️': '6312355444006329952',
    '🚗': '6314436368546143087',
    '🦌': '6314445186114002130',
    '☕': '6314177120025189721',
    '🌲': '6312028261987654273',
    '🍨': '6311828554598325497',
    '🕷': '6314365325492100536',
    '🧤': '6312140231785061712',
    '🎀': '6314150817645468807',
    '🫐': '6311836465928087993',
    '🦄': '6312094202620550804',
    '🌙': '6314463585753897853',
    '🎩': '6312053597999733930',
    '🧦': '6311825715624942781',
    '💖': '6311984612235024757',
    '🍰': '6314195571204693274',
    '🧸': '6314279894297615173',
    '👈': '6314279705319053709',
    '🦴': '6312004704092036467',
    '🧪': '6312032745933512047',
    '👼': '6312079616911613132',
    '🐸': '6314457766073212399',
    '🐈‍⬛': '6314541754158685304',
    '🍬': '6314223673175711097',
    '🃏': '6312154014335116067',
    '🎶': '6314229845043715676',
    '🔵': '5814168568001990143',
    '⚫️': '5816736812416110227',
    '🟤': '5816626367332093115',
    '🟡': '5816693463311191266',
    '⚪️': '5816698539962535289',
    '🟠': '5816876665141202258',
    '🟣': '5816503140425406028',
    '🔘': '5821294429847162088',
    '🎵': '5364123430662713141',
    '🎧': '5366243392160282909',
    '🔌': '5364078217541987860',
    '📺': '5366484756437414565',
    '✍️': '5366470114893902248',
    '👓': '5364136100816236855',
    '♥️': '5364053976746571579',
    '💨': '5366579782588837985',
    '🌬️': '5366290052684984457',
    '🚛': '5364300546524067436',
    '🎪': '5402498456646331504',
    '🔠': '5415685427879229352',
    '☎️': '5274098845964321778',
    '📱': '5294076156197221006',
    '⌚️': '5278361107084364385',
    '🗣': '5192860609007339609',
    '☎': '5192712943736734041',
    '🔚': '5192957327375881296',
    '🛑': '5192719154259445948',
    '📲': '5197584360068367665',
    '🟧': '5197410985123530380',
    '🍩': '5197510512400680804',
    '💿': '5278580412409464815',
    '🍆': '5276090632752874054',
    '🪗': '5458440929662752982',
    '⚪': '4902595693962593676',
    '🤛': '5071389270200026186',
    '🏀': '5071338791449396331',
    '⚫': '5068842152730035147',
    '🎥': '5071309770355377294',
    '🔞': '5071213868030624467',
    '📖': '5843735535184517527',
    '🖼️': '5796328712668453697',
}

for _supplied_emoji, _supplied_id in SUPPLIED_PREMIUM_EMOJI_MAP.items():
    GLOBAL_BODY_EMOJIS.setdefault(_supplied_emoji, _supplied_id)

# Prefer the supplied premium IDs over the older, conflicting IDs.  The
# supplied list contains the IDs intended for the current bot, while the
# legacy map above has several duplicate/wrong assignments.
PREMIUM_BODY_EMOJI_MAP = dict(GLOBAL_BODY_EMOJIS)
PREMIUM_BODY_EMOJI_MAP.update(SUPPLIED_PREMIUM_EMOJI_MAP)

# The supplied inventory contains duplicate Unicode entries with unrelated
# IDs.  Keep the IDs configured for this bot as the canonical payment and
# success icons.
PREMIUM_BODY_EMOJI_MAP.update({
    "✅": EMOJI_SUCCESS,
    "💳": EMOJI_BKASH,
    "📱": EMOJI_NAGAD,
    "🚀": EMOJI_ROCKET,
    "🆔": EMOJI_USER_ID,
    "💵": EMOJI_BINANCE,
    "❌": EMOJI_REJECT,
    "👑": EMOJI_CROWN,
    "🔰": EMOJI_STATUS,
    "🤖": EMOJI_BOT,
    "🎉": "6314309731435420506",
    "💡": "6314080328642207844",
})

# ------------------ PROFESSIONAL UI EMOJI THEME ------------------
# Keep the existing Premium Emoji inventory, but use the most meaningful
# icon for each area of the bot instead of reusing generic icons everywhere.
# Only the requested numbered main-menu buttons use this refreshed theme.
EMOJI_SEARCH = SUPPLIED_PREMIUM_EMOJI_MAP['🔍']
EMOJI_DIAMOND_UI = SUPPLIED_PREMIUM_EMOJI_MAP['💎']
EMOJI_CHAT = SUPPLIED_PREMIUM_EMOJI_MAP['💬']
EMOJI_SETTINGS = SUPPLIED_PREMIUM_EMOJI_MAP['⚙️']
EMOJI_NOTIFICATION = SUPPLIED_PREMIUM_EMOJI_MAP['🔔']
EMOJI_TOOLS = SUPPLIED_PREMIUM_EMOJI_MAP['🛠']
EMOJI_PLAY = SUPPLIED_PREMIUM_EMOJI_MAP['▶️']
EMOJI_SHIELD_UI = SUPPLIED_PREMIUM_EMOJI_MAP['🛡']
EMOJI_CALENDAR_UI = SUPPLIED_PREMIUM_EMOJI_MAP['🗓']
EMOJI_RECEIPT_UI = SUPPLIED_PREMIUM_EMOJI_MAP['🧾'] if '🧾' in SUPPLIED_PREMIUM_EMOJI_MAP else EMOJI_RECEIPT
EMOJI_CHECK_UI = SUPPLIED_PREMIUM_EMOJI_MAP['✔️']
EMOJI_RATE_UI = SUPPLIED_PREMIUM_EMOJI_MAP['💱']
# Best-fit Premium icons for generic replies and admin notifications.
EMOJI_REPLY_MESSAGE = EMOJI_CHAT
EMOJI_NOTIFICATION_MESSAGE = EMOJI_NOTIFICATION

# User menu — requested buttons 2–9
EMOJI_UPDATE_CHANNEL_USER = "6109451886044124125"
EMOJI_CHECK_FILE_USER = EMOJI_SEARCH
EMOJI_PREMIUM_PLAN_USER = "6246919169120408471"  # Premium Plans button
EMOJI_SUPPORT = EMOJI_CHAT
EMOJI_PROFILE_USER = "6312024679984929396"  # My Profile and Name labels
EMOJI_REFERRAL = EMOJI_GIFT
EMOJI_FREE_HOST = EMOJI_BOT  # Bot emoji before Free Bot Host

# Admin menu — requested buttons 11–13 use the refreshed theme.
EMOJI_UPDATE_CHANNEL_ADMIN = "6109451886044124125"
EMOJI_CHECK_FILE_ADMIN = EMOJI_SEARCH
EMOJI_BOT_SPEED_ADMIN = "6052879414339837562"  # button 10: unchanged
EMOJI_STATISTICS_ADMIN = SUPPLIED_PREMIUM_EMOJI_MAP['📊']
EMOJI_SUBSCRIPTION_ADMIN = EMOJI_CALENDAR_UI
EMOJI_RUNNING_ALL_ADMIN = EMOJI_PLAY
EMOJI_GX_ADMIN_PANEL = "6052909083973918987"  # unchanged
EMOJI_BAN_UNBAN = "6052902989415324360"  # unchanged
EMOJI_SHOW_BAN = "6053376986301078841"  # unchanged
EMOJI_BAN_USER = "6052902989415324360"  # unchanged
EMOJI_UNBAN_USER = "5866469651780736116"
EMOJI_ADMIN_PANEL = "6052909083973918987"  # unchanged
EMOJI_SET_LIMIT = "6053063247530039664"  # unchanged
EMOJI_SET_PREMIUM = "6141159258768545795"  # unchanged
EMOJI_DEPOSITE_METHOD = "6053314026375485069"  # unchanged
EMOJI_GROUP_SET = "6052886672834566125"  # unchanged
EMOJI_DEPOSIT_REQUEST = "6053234303192537471"  # unchanged
EMOJI_BUY_PLAN = EMOJI_DIAMOND_UI
EMOJI_DEPOSIT_MONEY = "6084884131945125425"  # unchanged
EMOJI_FREE_HOST_ADMIN = EMOJI_BOT  # Bot emoji before Free Bot Host

# Every outgoing message is rendered with Telegram premium custom emojis.
# The Unicode character remains inside the tag as its fallback/accessible
# value, but Telegram displays the premium emoji instead of a normal emoji.

# ==========================================
# ✅ RENDER FUNCTION - 100% FIXED
# ==========================================
GX_MESSAGE_NAME = "GX"


def ensure_gx_message_prefix(text):
    """Put the bot name at the start of every outgoing body message once."""
    if not text:
        return str(text)
    text = str(text)
    if re.match(r'^\s*(?:<b>)?GX(?:</b>)?(?:\s|$)', text, flags=re.IGNORECASE):
        return text
    return f"<b>{GX_MESSAGE_NAME}</b>\n{text}"


def render_body_text(text):
    """Convert every emoji in every outgoing message to a premium emoji tag."""
    if not text:
        return str(text)
    
    text = ensure_gx_message_prefix(text)
    preserved_tags = []

    def preserve_custom_emoji(match):
        original_id = match.group(1)
        visible_emoji = match.group(2)
        emoji_id = PREMIUM_BODY_EMOJI_MAP.get(
            visible_emoji,
            _clean_emoji_id(original_id) or EMOJI_DEFAULT
        )
        # Explicit tags are intentional.  Do not replace a method-specific
        # or success-specific ID with another ID for the same Unicode emoji.
        if _clean_emoji_id(original_id):
            emoji_id = original_id
        preserved_tags.append(
            f'<tg-emoji emoji-id="{emoji_id}">{visible_emoji}</tg-emoji>'
        )
        return f'\x00TG_EMOJI_{len(preserved_tags) - 1}\x00'

    text = _TG_EMOJI_TAG_RE.sub(preserve_custom_emoji, text)

    # Longest first prevents a shorter sequence (❤️) from consuming part of
    # a compound emoji (❤️‍🔥).
    for normal_emoji, emoji_id in sorted(
        PREMIUM_BODY_EMOJI_MAP.items(),
        key=lambda item: len(item[0]),
        reverse=True
    ):
        if normal_emoji in text:
            text = text.replace(
                normal_emoji,
                f'<tg-emoji emoji-id="{emoji_id}">{normal_emoji}</tg-emoji>'
            )

    # Future messages may introduce an emoji not yet listed above.  Use the
    # valid premium fallback rather than allowing a normal emoji through.
    text = _convert_unmapped_emojis(text)

    for index, tag in enumerate(preserved_tags):
        text = text.replace(f'\x00TG_EMOJI_{index}\x00', tag)
    text = _PLAIN_USER_EMOJI_TOKEN_RE.sub(
        lambda match: chr(int(match.group(1), 16)),
        text,
    )
    return text

# ==========================================
# ✅ SEND MESSAGE - 100% FIXED
# ==========================================
def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    """Send message with 100% premium emoji support"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    rendered_text = render_body_text(text)
    
    payload = {
        "chat_id": chat_id,
        "text": rendered_text,
        "parse_mode": parse_mode,
    }
    
    if reply_markup:
        # The legacy helper uses requests directly, so convert TeleBot
        # markup to a real JSON-compatible dictionary instead of passing the
        # Python object (which silently prevents button fields from arriving).
        reply_markup = _sanitize_reply_markup(reply_markup)
        if hasattr(reply_markup, "to_dict"):
            payload["reply_markup"] = reply_markup.to_dict()
        elif hasattr(reply_markup, "to_json"):
            payload["reply_markup"] = json.loads(reply_markup.to_json())
        else:
            payload["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

# ==========================================
# ✅ BOT REPLY - সব Reply এ Premium Emoji
# ==========================================
def bot_reply(message, text, reply_markup=None, parse_mode='HTML'):
    """Reply to message with premium emojis"""
    return send_message(message.chat.id, render_body_text(text), reply_markup, parse_mode)

# --- Configuration ---
# Keep credentials out of the source tree. Set BOT_TOKEN in Replit
# Secrets/environment before starting the bot.
# ==========================================================
# ✅ BOT CONFIG — environment only
# ==========================================================
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError(
        "Missing TELEGRAM_BOT_TOKEN environment variable. "
        "Set it in the hosting environment before starting the bot."
    )


def required_int_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name} environment variable.")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a numeric Telegram user ID.") from exc


OWNER_ID = required_int_env("OWNER_ID")
ADMIN_ID = required_int_env("ADMIN_ID")

YOUR_USERNAME = os.environ.get("OWNER_USERNAME", "@iamGuruX")
UPDATE_CHANNEL = os.environ.get(
    "UPDATE_CHANNEL", "https://t.me/GxHostingUpdate"
)
BINANCE_PAY_ID = os.environ.get("BINANCE_PAY_ID", "SET_YOUR_BINANCE_PAY_ID")

# --- Centralized configurable links (editable from Admin Panel) ---
DEFAULT_LINKS = {
    'admin_link': f'https://t.me/{YOUR_USERNAME.lstrip("@")}',
    'support_link': f'https://t.me/{YOUR_USERNAME.lstrip("@")}',
    'channel_link': UPDATE_CHANNEL,
    'update_channel_link': UPDATE_CHANNEL,
    'owner_link': f'https://t.me/{YOUR_USERNAME.lstrip("@")}',
    'group_link': UPDATE_CHANNEL,
}

LINK_FIELDS = [
    ('admin_link', '👤 Admin Link'),
    ('support_link', 'Support Link'),
    ('channel_link', '📢 Channel Link'),
    ('update_channel_link', '☠️ Update Channel Link'),
    ('owner_link', '👑 Owner Link'),
    ('group_link', '👥 Group Link'),
]

# --- Binance Pay Integration Config ---
USDT_BDT_RATE = 120.0
# Binance deposits are manual review only.  No Binance API credentials are
# read or used by this bot.
BINANCE_PAY_ID = os.environ.get("BINANCE_PAY_ID", "SET_YOUR_BINANCE_PAY_ID")

# --- Google Sheets primary-storage configuration ---
# The sheet ID and service-account JSON are read only from environment
# variables. No credential is stored in this source file.
#
# Recommended Secrets:
#   GOOGLE_SHEET_ID
#   GOOGLE_SERVICE_ACCOUNT_JSON  (the complete JSON as one secret)
#
# Alternative local setup:
#   GOOGLE_SERVICE_ACCOUNT_JSON may also point to a local JSON file.
# ==========================================================
# ✅ GOOGLE SHEETS — SECRET-BACKED CREDENTIALS
# ==========================================================
# The old inline values were removed. Set GOOGLE_SHEET_ID and
# GOOGLE_SERVICE_ACCOUNT_JSON in the host secrets/environment.
GOOGLE_SHEET_ID_SOURCE = ""
GOOGLE_SERVICE_ACCOUNT_JSON_SOURCE = ""
# Removed exposed legacy service-account key; revoke it and configure a new secret.

GOOGLE_SHEET_ID = (
    os.environ.get("GOOGLE_SHEET_ID")
    or os.environ.get("SHEET_ID")
    or GOOGLE_SHEET_ID_SOURCE
).strip()
GOOGLE_SERVICE_ACCOUNT_JSON = (
    os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    or os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    or os.environ.get("GOOGLE_CREDENTIALS_JSON")
    or GOOGLE_SERVICE_ACCOUNT_JSON_SOURCE
).strip()
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "").strip()
GOOGLE_SYNC_INTERVAL = max(
    5.0, float(os.environ.get("GOOGLE_SYNC_INTERVAL", "30"))
)
GOOGLE_SHEETS_SYNC_INTERVAL_SECONDS = GOOGLE_SYNC_INTERVAL
GOOGLE_SHEET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]
GOOGLE_SHEETS_SYNC_ENABLED = not (
    os.environ.get("DISABLE_GOOGLE_SHEETS", "0").strip().lower()
    in {"1", "true", "yes", "on"}
)

# Every durable schema table is mirrored to its own worksheet. Files
# themselves and Telegram credentials are never uploaded to Sheets.
GOOGLE_SHEETS_SYNC_TABLES = (
    "active_users",
    "user_profiles",
    "admins",
    "subscriptions",
    "user_files",
    "hosted_bot_backups",
    "user_file_action_quota",
    "free_user_settings",
    "premium_plans",
    "user_premium",
    "payment_methods",
    "deposits_new",
    "user_balances",
    "settings",
    "plans",
    "pending_payments",
    "used_txids",
    "banned_users",
    "referrals",
    "referral_strikes",
    "referral_codes",
    "free_host_plans",
    "free_host_grants",
    "free_host_plan_claims",
    "group_settings",
    "file_forward_group",
    "force_join_channels",
)

# Folder setup. On Render, set BOT_DATA_DIR to the mount path of a persistent
# disk (for example /var/data); on other hosts the local data/ directory is used.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BOT_DATA_DIR = os.path.abspath(
    os.environ.get("BOT_DATA_DIR") or os.path.join(BASE_DIR, "data")
)
os.makedirs(BOT_DATA_DIR, exist_ok=True)
DATABASE_PATH = os.path.abspath(
    os.environ.get("BOT_DATABASE_PATH")
    or os.path.join(BOT_DATA_DIR, "gxhosting.sqlite3")
)
UPLOAD_BOTS_DIR = os.path.abspath(
    os.environ.get("BOT_UPLOAD_DIR")
    or os.path.join(BOT_DATA_DIR, "upload_bots")
)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
DB_LOCK = threading.RLock()
LOCAL_DATABASE_EXISTED_AT_START = os.path.isfile(DATABASE_PATH)


def get_db_connection():
    """Return a connection to the durable local cache/database."""
    connection = sqlite3.connect(
        DATABASE_PATH, check_same_thread=False, timeout=30
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


IROTECH_DIR = BOT_DATA_DIR

# File upload limits
SUBSCRIBED_USER_LIMIT = 1
ADMIN_LIMIT = 999
OWNER_LIMIT = float('inf')

# Separate lifetime upload/delete quota for regular users.  This is
# intentionally independent from FREE_USER_LIMIT_SETTINGS, which controls
# how many files a user may keep hosted at the same time.
FILE_ACTION_SIZE_LIMIT_BYTES = 1 * 1024 * 1024
FILE_ACTION_COUNT_LIMIT = 3

# Free user limit settings
FREE_USER_LIMIT_SETTINGS = {
    "limit": 1,
    "time": 1,
    "host_time": 1
}

# Create necessary directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# ==========================================
# ✅ MESSAGE TEXT CLEANER
# Legacy messages were written with Markdown markers ("*text*", "`code`")
# but are sent with parse_mode='HTML', so the markers used to show up as
# raw characters.  Everything is normalised here, in one place, so the
# whole bot sends clean and professional looking messages.
# ==========================================
_MD_BOLD_DOUBLE_RE = re.compile(r'\*\*(.+?)\*\*', re.DOTALL)
_MD_BOLD_SINGLE_RE = re.compile(r'\*(?!\s)([^\*\n]+?)(?<!\s)\*')
_MD_CODE_RE = re.compile(r'`([^`\n]+)`')
_HTML_TAG_RE = re.compile(r'<[^>]+>')
_TG_EMOJI_TAG_RE = re.compile(
    r'<tg-emoji\s+emoji-id="([^"]+)">(.*?)</tg-emoji>',
    re.DOTALL
)

_EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2300, 0x23FF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0x3030, 0x303D),
    (0x3297, 0x3299),
)
_EMOJI_MODIFIERS = range(0x1F3FB, 0x1F400)
_EMOJI_VARIATION_SELECTORS = {0xFE0E, 0xFE0F}


def _is_emoji_base(char):
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in _EMOJI_RANGES)


def _emoji_cluster_end(text, start):
    """Return the end of an emoji grapheme cluster, or start if not one."""
    if start >= len(text):
        return start
    char = text[start]
    is_keycap = (
        char in "0123456789#*" and start + 1 < len(text)
        and (ord(text[start + 1]) in _EMOJI_VARIATION_SELECTORS
             or ord(text[start + 1]) == 0x20E3)
    )
    if not _is_emoji_base(char) and not is_keycap:
        return start

    end = start + 1
    while end < len(text):
        current = ord(text[end])
        if current in _EMOJI_VARIATION_SELECTORS or current in _EMOJI_MODIFIERS:
            end += 1
            continue
        if current == 0x20E3:
            end += 1
            continue
        if current == 0x200D and end + 1 < len(text) and _is_emoji_base(text[end + 1]):
            end += 2
            while end < len(text):
                current = ord(text[end])
                if current in _EMOJI_VARIATION_SELECTORS or current in _EMOJI_MODIFIERS:
                    end += 1
                else:
                    break
            continue
        break
    return end


def strip_normal_emojis(text):
    """Remove Unicode emoji from labels; buttons use a Premium Emoji icon."""
    if text is None:
        return text
    text = str(text)
    output = []
    index = 0
    while index < len(text):
        end = _emoji_cluster_end(text, index)
        if end == index:
            output.append(text[index])
            index += 1
        else:
            index = end
    return "".join(output).strip()


_PLAIN_USER_EMOJI_TOKEN_RE = re.compile(
    r"\x00TG_PLAIN_USER_EMOJI_([0-9A-F]+)\x00"
)


def keep_user_name_emojis_normal(value):
    """Keep emojis that belong to a user's display name unconverted.

    The renderer converts normal emojis in bot copy to Premium emojis.  User
    names are user-authored content, so their original emojis must remain
    ordinary Unicode characters.
    """
    if value is None:
        return ""
    value = str(value)
    output = []
    index = 0
    while index < len(value):
        end = _emoji_cluster_end(value, index)
        if end == index:
            output.append(value[index])
            index += 1
            continue
        for character in value[index:end]:
            output.append(
                f"\x00TG_PLAIN_USER_EMOJI_{ord(character):X}\x00"
            )
        index = end
    return "".join(output)


def _convert_unmapped_emojis(text):
    """Wrap any newly introduced emoji with a premium fallback ID."""
    protected_tags = []

    def protect_tag(match):
        protected_tags.append(match.group(0))
        return f"\x00TG_EMOJI_PROTECTED_{len(protected_tags) - 1}\x00"

    text = _TG_EMOJI_TAG_RE.sub(protect_tag, text)
    output = []
    index = 0
    while index < len(text):
        end = _emoji_cluster_end(text, index)
        if end == index:
            output.append(text[index])
            index += 1
        else:
            visible_emoji = text[index:end]
            output.append(
                f'<tg-emoji emoji-id="{PREMIUM_BODY_EMOJI_MAP.get(visible_emoji, EMOJI_DEFAULT)}">{visible_emoji}</tg-emoji>'
            )
            index = end

    text = "".join(output)
    for index, tag in enumerate(protected_tags):
        text = text.replace(f"\x00TG_EMOJI_PROTECTED_{index}\x00", tag)
    return text


def clean_message_text(text):
    """Convert leftover Markdown markers to HTML and drop stray asterisks."""
    if text is None:
        return text
    text = str(text)
    if '*' not in text and '`' not in text:
        return text
    text = _MD_BOLD_DOUBLE_RE.sub(r'<b>\1</b>', text)
    text = _MD_BOLD_SINGLE_RE.sub(r'<b>\1</b>', text)
    text = _MD_CODE_RE.sub(r'<code>\1</code>', text)
    # Remove any asterisk/backtick left over from unbalanced markers.
    text = text.replace('*', '').replace('`', '')
    return text


def strip_formatting(text):
    """Plain-text version used as a fallback when Telegram rejects HTML."""
    if text is None:
        return text
    return _HTML_TAG_RE.sub('', str(text))


_INLINE_BUTTON_ICON_CACHE = {}
_INLINE_BUTTON_USED_IDS = set()
_PREMIUM_BUTTON_META = {}
_INLINE_BUTTON_POOL = tuple(dict.fromkeys(
    str(value) for value in SUPPLIED_PREMIUM_EMOJI_MAP.values()
    if str(value).strip().isdigit()
))


def _inline_button_key(text):
    """Return a stable key while ignoring the decorative emoji in a label."""
    cleaned = strip_normal_emojis(str(text or ""))
    return re.sub(r"\s+", " ", cleaned).strip().lower() or "inline-button"


def _is_update_channel_label(text):
    """Recognize every Update Channel label used by this bot.

    The menu uses mathematical-bold Unicode letters, which do not become
    ASCII when `.lower()` is called. Keep the exact styled variants here so
    reply and inline keyboards always resolve the same Premium Emoji ID.
    """
    raw = str(text or "")
    lowered = raw.lower()
    return (
        "update channel" in lowered
        or "updates channel" in lowered
        or "𝙐𝙋𝘿𝘼𝙏𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇" in raw
        or "𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇" in raw
    )


def _is_channel_join_button(text):
    """Recognize force-join buttons independently of their channel name."""
    return str(text or "").lstrip().startswith("📢")


def _inline_button_special_id(text):
    raw = str(text or "").lower()
    if "update bot" in raw:
        return EMOJI_UPDATE_BOT
    # Force-join channel buttons must all look identical, regardless of the
    # configured channel name (Main channel, @username, or a custom label).
    if raw.lstrip().startswith("📢"):
        return EMOJI_ALL_CHANNEL_BUTTON
    # The main-menu label uses mathematical-bold Unicode characters
    # (𝙐𝙋𝘿𝘼𝙏𝙀...), so a normal ASCII substring check does not match it.
    # Recognize both styled labels and ordinary labels so the inline button
    # receives the exact same Premium Emoji as the reply-keyboard button.
    if _is_update_channel_label(text):
        return get_update_channel_button_emoji_id(EMOJI_UPDATE_CHANNEL_USER)
    if _inline_button_key(text) in ("view logs", "logs"):
        return EMOJI_VIEW_LOGS
    if "verify" in raw or "ভেরিফাই" in raw:
        return EMOJI_VERIFY_BUTTON
    if "unban" in raw or "আনবান" in raw:
        return EMOJI_UNBAN_USER
    if "❌" in raw or any(word in raw for word in (
        "reject", "cancel", "delete", "remove", "বাতিল", "ডিলিট",
        "রিমুভ", "মুছুন", "ব্যান",
    )):
        return EMOJI_REJECT
    if "✅" in raw or any(word in raw for word in (
        "approve", "confirm", "success", "verify", "save", "submit",
        "done", "approved", "অনুমোদন", "সম্পন্ন", "ভেরিফাই",
    )):
        return EMOJI_SUCCESS
    return ""


def get_inline_button_emoji_id(text):
    """Choose a Premium icon for every inline button.

    Success and reject actions intentionally share their two canonical IDs.
    Other button labels receive a stable, non-repeated ID.
    """
    special_id = _inline_button_special_id(text)
    if special_id:
        return special_id

    key = _inline_button_key(text)
    if key in _INLINE_BUTTON_ICON_CACHE:
        return _INLINE_BUTTON_ICON_CACHE[key]

    # Prefer a meaningful icon for the first button in each functional area.
    hints = (
        (("upload", "ফাইল আপলোড"), EMOJI_UPLOAD),
        (("download", "ডাউনলোড"), EMOJI_DOWNLOAD),
        (("search", "সার্চ"), EMOJI_SEARCH),
        (("support", "সাপোর্ট", "টিকিট"), EMOJI_SUPPORT),
        (("profile", "প্রোফাইল"), EMOJI_PROFILE_USER),
        (("deposit", "ডিপোজিট"), EMOJI_DEPOSIT),
        (("bkash", "বিকাশ"), EMOJI_BKASH),
        (("nagad", "নগদ"), EMOJI_NAGAD),
        (("rocket", "রকেট"), EMOJI_ROCKET),
        (("upay", "উপায়"), EMOJI_UPAY),
        (("binance",), EMOJI_BINANCE),
        (("withdraw", "উইথড্র", "উত্তোলন"), EMOJI_MONEY),
        (("refer", "রেফার"), EMOJI_REFERRAL),
        (("subscription", "সাবস্ক্রিপশন", "plan"), EMOJI_PREMIUM_PLAN_USER),
        (("admin", "এডমিন"), EMOJI_ADMIN_PANEL),
        (("statistic", "analytics", "এনালিটিক্স"), EMOJI_STATS),
        (("setting", "সেটিং", "কনফিগ"), EMOJI_SETTINGS),
        (("channel", "চ্যানেল"), EMOJI_MEGAPHONE),
        (("share", "শেয়ার"), EMOJI_GIFT),
        (("back", "home", "মেইন মেনু", "ফিরুন"), EMOJI_BACK),
        (("add", "যোগ", "যুক্ত"), EMOJI_PLUS),
        (("start", "শুরু"), EMOJI_RUNNING),
        (("stop", "বন্ধ"), EMOJI_STOP),
        (("lock", "লক"), EMOJI_LOCK),
        (("unlock", "আনলক"), EMOJI_UNLOCK),
    )
    raw = str(text or "").lower()
    preferred_id = ""
    for words, candidate in hints:
        if any(word in raw for word in words):
            candidate = _clean_emoji_id(candidate)
            if candidate and candidate not in _INLINE_BUTTON_USED_IDS:
                preferred_id = candidate
                break

    if not preferred_id:
        for candidate in _INLINE_BUTTON_POOL:
            if candidate in (EMOJI_SUCCESS, EMOJI_REJECT):
                continue
            if candidate not in _INLINE_BUTTON_USED_IDS:
                preferred_id = candidate
                break

    # The supplied inventory is large enough for the bot's current buttons.
    # Keep a valid fallback for any unusually large user-created button list.
    preferred_id = preferred_id or EMOJI_DEFAULT
    _INLINE_BUTTON_ICON_CACHE[key] = preferred_id
    _INLINE_BUTTON_USED_IDS.add(preferred_id)
    return preferred_id


def get_inline_button_style(text):
    raw = str(text or "").lower()
    if _inline_button_special_id(raw) == EMOJI_REJECT:
        return "danger"
    if _inline_button_special_id(raw) in (EMOJI_SUCCESS, EMOJI_VERIFY_BUTTON):
        return "success"
    if any(word in raw for word in (
        "buy", "deposit", "withdraw", "upload", "add", "share",
        "কিনুন", "ডিপোজিট", "উইথড্র", "আপলোড", "যোগ",
    )):
        return "success"
    return "primary"


def _remember_premium_button(button, emoji_id="", style=""):
    """Remember fields even when an older TeleBot class drops new fields."""
    if button is None:
        return button
    meta = _PREMIUM_BUTTON_META.setdefault(id(button), {})
    if emoji_id:
        meta["icon_custom_emoji_id"] = str(emoji_id)
    if style:
        meta["style"] = str(style)
    return button


def _install_markup_premium_serializer(markup_class, output_key):
    """Force Premium button fields into TeleBot's final JSON payload.

    pyTelegramBotAPI versions released before Telegram Bot API 9.4 do not
    know the new button fields.  They may keep the Python attributes but omit
    them from to_dict(); this wrapper adds them after the original serializer.
    """
    original_to_dict = getattr(markup_class, "to_dict", None)
    if original_to_dict is None or getattr(
        markup_class, "_premium_serializer_installed", False
    ):
        return

    def premium_to_dict(self):
        payload = original_to_dict(self)
        rows = getattr(self, "keyboard", None) or []
        output_rows = payload.setdefault(output_key, [])
        for row_index, row in enumerate(rows):
            if row_index >= len(output_rows):
                continue
            for button_index, button in enumerate(row):
                if button_index >= len(output_rows[row_index]):
                    continue
                meta = dict(_PREMIUM_BUTTON_META.get(id(button), {}))
                for field in ("icon_custom_emoji_id", "style"):
                    value = getattr(button, field, None)
                    if value:
                        meta[field] = str(value)
                if meta:
                    output_rows[row_index][button_index].update(meta)
        return payload

    markup_class.to_dict = premium_to_dict
    markup_class._premium_serializer_installed = True


def _install_button_constructor_compatibility():
    """Accept new fields on old TeleBot releases and serialize them later."""
    original_class = getattr(types, "InlineKeyboardButton", None)
    if original_class is not None and not getattr(
        original_class, "_premium_constructor_installed", False
    ):
        class PremiumInlineKeyboardButton(original_class):
            def __init__(self, text, *args, **kwargs):
                emoji_id = kwargs.get("icon_custom_emoji_id", "")
                style = kwargs.get("style", "")
                try:
                    super().__init__(text, *args, **kwargs)
                except TypeError:
                    # Old pyTelegramBotAPI: retry without Bot API 9.4 fields.
                    kwargs.pop("icon_custom_emoji_id", None)
                    kwargs.pop("style", None)
                    super().__init__(text, *args, **kwargs)
                _remember_premium_button(self, emoji_id, style)

        PremiumInlineKeyboardButton._premium_constructor_installed = True
        types.InlineKeyboardButton = PremiumInlineKeyboardButton

    _install_markup_premium_serializer(
        types.InlineKeyboardMarkup, "inline_keyboard"
    )
    if hasattr(types, "ReplyKeyboardMarkup"):
        _install_markup_premium_serializer(types.ReplyKeyboardMarkup, "keyboard")


def _sanitize_reply_markup(markup):
    """Give every inline button a Premium icon and preserve its style.

    Reply keyboards are deliberately left alone.  Inline buttons are
    normalized at send time, including keyboards edited onto a message.
    """
    if markup is None:
        return markup
    # pyTelegramBotAPI calls the inline rows `keyboard`; the Bot API JSON
    # calls them `inline_keyboard`.  The previous check only handled the
    # latter and silently skipped every real TeleBot InlineKeyboardMarkup.
    inline_rows = getattr(markup, "inline_keyboard", None)
    is_inline = isinstance(markup, types.InlineKeyboardMarkup)
    if inline_rows is not None:
        is_inline = True
    rows = (
        getattr(markup, "keyboard", None)
        if is_inline
        else getattr(markup, "keyboard", None)
    )
    for row in rows or []:
        for button in row:
            if not is_inline or not hasattr(button, "text"):
                continue

            original_text = str(button.text)
            explicit_emoji_id = getattr(button, "icon_custom_emoji_id", "")
            if not explicit_emoji_id:
                explicit_emoji_id = _PREMIUM_BUTTON_META.get(
                    id(button), {}
                ).get("icon_custom_emoji_id", "")
            emoji_id = (
                _clean_emoji_id(explicit_emoji_id)
                or get_inline_button_emoji_id(original_text)
            )
            button.text = strip_normal_emojis(original_text)

            # Every inline button receives a Premium custom emoji ID.
            if emoji_id:
                try:
                    button.icon_custom_emoji_id = emoji_id
                except (AttributeError, TypeError):
                    pass
            _remember_premium_button(
                button, emoji_id, get_inline_button_style(original_text)
            )

            # Preserve an explicitly requested colour; otherwise choose a
            # sensible colour from the button's action.
            try:
                if not getattr(button, "style", None):
                    button.style = get_inline_button_style(original_text)
            except (AttributeError, TypeError):
                # Older pyTelegramBotAPI versions may not expose style.
                # Their normal button behaviour remains usable.
                pass
    return markup


_install_button_constructor_compatibility()


def _install_clean_text_layer():
    """Wrap the bot senders so every outgoing text is cleaned once."""
    original_send_message = bot.send_message
    original_reply_to = bot.reply_to
    original_send_photo = bot.send_photo
    original_send_document = bot.send_document
    original_edit_message_text = bot.edit_message_text
    original_edit_message_reply_markup = bot.edit_message_reply_markup
    original_answer_callback_query = bot.answer_callback_query
    original_register_next_step_handler = bot.register_next_step_handler

    def _prepare(text, kwargs):
        cleaned = clean_message_text(text)
        # Prefix even strings that already contain an explicit custom emoji
        # tag, because those strings intentionally skip the second renderer.
        cleaned = ensure_gx_message_prefix(cleaned)
        # Run the central premium-emoji renderer, even if a future handler
        # passes Markdown or another parse mode by mistake.
        # Handlers in this legacy bot sometimes call render_body_text()
        # themselves before passing text to bot.reply_to/send_message.  Do
        # not render those strings a second time: a user's normal name emoji
        # would otherwise be converted on the second pass.
        if '<tg-emoji ' not in str(cleaned):
            cleaned = render_body_text(cleaned)
        if '<tg-emoji ' in str(cleaned):
            # Premium custom emoji tags require HTML parse mode.
            kwargs['parse_mode'] = 'HTML'
        if 'reply_markup' in kwargs:
            kwargs['reply_markup'] = _sanitize_reply_markup(kwargs['reply_markup'])
        return cleaned

    def send_message_clean(chat_id, text=None, **kwargs):
        cleaned = _prepare(text, kwargs)
        try:
            return original_send_message(chat_id, cleaned, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            logger.warning(f"send_message fallback for {chat_id}: {e}")
            kwargs.pop('parse_mode', None)
            return original_send_message(chat_id, strip_formatting(cleaned), **kwargs)

    def reply_to_clean(message, text=None, **kwargs):
        cleaned = _prepare(text, kwargs)
        try:
            return original_reply_to(message, cleaned, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            logger.warning(f"reply_to fallback: {e}")
            kwargs.pop('parse_mode', None)
            return original_reply_to(message, strip_formatting(cleaned), **kwargs)

    def send_photo_clean(chat_id, photo, caption=None, **kwargs):
        cleaned = _prepare(caption, kwargs) if caption is not None else caption
        try:
            return original_send_photo(chat_id, photo, caption=cleaned, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            logger.warning(f"send_photo fallback for {chat_id}: {e}")
            kwargs.pop('parse_mode', None)
            return original_send_photo(
                chat_id, photo, caption=strip_formatting(cleaned), **kwargs
            )

    def send_document_clean(chat_id, document, **kwargs):
        caption = kwargs.get("caption")
        if caption is not None:
            kwargs["caption"] = _prepare(caption, kwargs)
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = _sanitize_reply_markup(
                kwargs["reply_markup"]
            )
        try:
            return original_send_document(chat_id, document, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            logger.warning(f"send_document fallback for {chat_id}: {e}")
            kwargs.pop("parse_mode", None)
            if caption is not None:
                kwargs["caption"] = strip_formatting(kwargs["caption"])
            return original_send_document(chat_id, document, **kwargs)

    def edit_message_text_clean(text=None, chat_id=None, message_id=None, **kwargs):
        cleaned = _prepare(text, kwargs)
        try:
            return original_edit_message_text(cleaned, chat_id, message_id, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            if 'message is not modified' in str(e).lower():
                return None
            logger.warning(f"edit_message_text fallback: {e}")
            kwargs.pop('parse_mode', None)
            try:
                return original_edit_message_text(
                    strip_formatting(cleaned), chat_id, message_id, **kwargs)
            except telebot.apihelper.ApiTelegramException as inner:
                logger.warning(f"edit_message_text failed: {inner}")
                return None

    def edit_message_reply_markup_clean(*args, **kwargs):
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = _sanitize_reply_markup(
                kwargs["reply_markup"]
            )
        return original_edit_message_reply_markup(*args, **kwargs)

    def answer_callback_query_clean(callback_query_id, text=None, **kwargs):
        if text is not None:
            text = strip_normal_emojis(strip_formatting(
                ensure_gx_message_prefix(clean_message_text(text))
            ))
        try:
            return original_answer_callback_query(callback_query_id, text, **kwargs)
        except telebot.apihelper.ApiTelegramException as e:
            logger.warning(f"answer_callback_query failed: {e}")
            return None

    def register_next_step_handler_guarded(message, callback, *args, **kwargs):
        """Prevent pending multi-step flows from bypassing Force Join.

        pyTelegramBotAPI processes next-step handlers before normal message
        handlers.  Without this wrapper, a user could start a deposit or
        admin-like flow, leave a required channel, and still complete that
        flow without passing the gate.
        """
        def is_control_message(next_message):
            """Detect a command/reply button that should cancel text input."""
            if getattr(next_message, "content_type", None) != "text":
                return False
            text = (getattr(next_message, "text", None) or "").strip()
            if not text:
                return False
            if text.startswith("/"):
                return True

            control_texts = {
                "BACK",
                "BACK TO MAIN",
                "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉",
                "Cancel",
                "না, বাতিল করুন",
                "bKash",
                "Nagad",
                "Rocket",
                "Upay",
                "Binance",
                RESTART_BOT_BUTTON_TEXT,
                UPDATE_CONFIRM_YES_TEXT,
                UPDATE_CONFIRM_NO_TEXT,
            }
            control_texts.update(
                globals().get("BUTTON_TEXT_TO_LOGIC", {}).keys()
            )

            # Collect labels from reply-keyboard layout constants, including
            # admin/premium/deposit submenus that are defined later in the
            # module but already exist when messages arrive.
            layout_names = (
                "COMMAND_BUTTONS_LAYOUT_USER_SPEC",
                "ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC",
                "OTP_ADMIN_BUTTONS",
                "OTP_USER_BUTTONS",
                "UPLOAD_MODE_BUTTONS",
                "PREMIUM_PLAN_ADMIN_BUTTONS",
                "ADMIN_PANEL_BUTTONS",
                "OTP_BAN_BUTTONS",
                "OTP_DEPOSITE_BUTTONS",
            )
            for layout_name in layout_names:
                layout = globals().get(layout_name, ())
                for row in layout if isinstance(layout, (list, tuple)) else ():
                    if not isinstance(row, (list, tuple)):
                        continue
                    for button in row:
                        if isinstance(button, dict) and button.get("text"):
                            control_texts.add(str(button["text"]))

            return (
                text in control_texts
                or text.startswith(("কিনুন", "DELETE ", "✅ হ্যাঁ"))
                # Styled reply-keyboard labels use mathematical sans-serif
                # letters; ordinary user-entered amounts/IDs do not.
                or (
                    len(text) < 100
                    and text[0] in "𝘼𝘽𝘾𝘿𝙀𝙁𝙂𝙃𝙄𝙅𝙆𝙇𝙈𝙉𝙊𝙋𝙌𝙍𝙎𝙏𝙐𝙑𝙒𝙓𝙔𝙕𝙂"
                    and " " in text
                )
            )

        def guarded_callback(next_message):
            user_id = getattr(getattr(next_message, 'from_user', None), 'id', None)
            if user_id is not None:
                if is_restart_required(user_id):
                    if (getattr(next_message, 'content_type', None) == 'text'
                            and (getattr(next_message, 'text', None) or '').strip()
                            == RESTART_BOT_BUTTON_TEXT):
                        return handle_bot_restart(next_message)
                    send_restart_required_notice(next_message.chat.id)
                    return
                if is_user_banned(user_id):
                    send_banned_user_notice(next_message.chat.id, user_id)
                    return
                missing = get_missing_force_channels(user_id, use_cache=False)
                if missing:
                    send_force_join_prompt(
                        next_message.chat.id,
                        missing,
                        getattr(next_message.from_user, 'first_name', None)
                    )
                    return

                # A command or keyboard button is a new action, not input for
                # the previous amount/TXID/screenshot prompt.  Since
                # pyTelegramBotAPI consumes next-step handlers first, clear
                # the stale handler and feed this same message back through
                # the normal command/button router.
                if is_control_message(next_message):
                    chat_id = getattr(
                        getattr(next_message, "chat", None),
                        "id",
                        user_id,
                    )
                    try:
                        bot.clear_step_handler_by_chat_id(chat_id)
                    except Exception as exc:
                        logger.debug(
                            "Could not clear interrupted step handler for %s: %s",
                            chat_id,
                            exc,
                        )
                    try:
                        return bot.process_new_messages([next_message])
                    except Exception as exc:
                        logger.error(
                            "Could not route interrupted command/button: %s",
                            exc,
                            exc_info=True,
                        )
                    return

            return callback(next_message, *args, **kwargs)

        return original_register_next_step_handler(
            message, guarded_callback
        )

    bot.send_message = send_message_clean
    bot.reply_to = reply_to_clean
    bot.send_photo = send_photo_clean
    bot.send_document = send_document_clean
    bot.edit_message_text = edit_message_text_clean
    bot.edit_message_reply_markup = edit_message_reply_markup_clean
    bot.answer_callback_query = answer_callback_query_clean
    bot.register_next_step_handler = register_next_step_handler_guarded


_install_clean_text_layer()

# --- Data structures ---
bot_scripts = {}
user_subscriptions = {}
user_files = {}
active_users = set()
admin_ids = {ADMIN_ID, OWNER_ID}
bot_locked = False

# --- OTP GURU Bot Data ---
all_users = []
banned_users = []
all_files = []
# ADMIN_ID and OWNER_ID can be the same person.  Keep this list unique so
# one admin never receives the same notification twice.
admin_list = list(dict.fromkeys([ADMIN_ID, OWNER_ID]))
user_limits = {}
user_upload_times = {}
file_stop_status = {}
# A file is accepted only after the user presses Upload File and chooses a
# dependency mode.  This is intentionally in-memory: a bot restart clears
# unfinished upload flows.
pending_upload_modes = {}
referral_bot_username = None
# During an update, every known user/admin/owner must press this button
# before any existing command, menu, callback, or upload is accepted.
RESTART_BOT_BUTTON_TEXT = "𝙍𝙀𝙎𝙏𝘼𝙍𝙏 𝘽𝙊𝙏"
UPDATE_CONFIRM_YES_TEXT = "𝙔𝙀𝙎"
UPDATE_CONFIRM_NO_TEXT = "𝙉𝙊"
DELETE_ALL_DATA_BUTTON_TEXT = "𝘿𝙀𝙇𝙀𝙏𝙀 𝘼𝙇𝙇 𝘿𝘼𝙏𝘼"
GOOGLE_SYNC_STATUS_BUTTON_TEXT = "𝙂𝙊𝙊𝙂𝙇𝙀 𝙎𝙔𝙉𝘾 𝙎𝙏𝘼𝙏𝙐𝙎"
DELETE_ALL_DATA_CONFIRM_TEXT = "𝙔𝙀𝙎, 𝘿𝙀𝙇𝙀𝙏𝙀 𝙀𝙑𝙀𝙍𝙔𝙏𝙃𝙄𝙉𝙂"
DELETE_ALL_DATA_CANCEL_TEXT = "𝙉𝙊, 𝙆𝙀𝙀𝙋 𝘿𝘼𝙏𝘼"
_restart_required_users = set()
_restart_state_lock = threading.RLock()
bot_update_mode = False
# ======================================================


def is_restart_required(user_id):
    with _restart_state_lock:
        return user_id in _restart_required_users


def build_update_confirmation_keyboard():
    """Ask the admin to confirm before notifying every bot user."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        make_keyboard_button(UPDATE_CONFIRM_YES_TEXT, EMOJI_SUCCESS, "success"),
        make_keyboard_button(UPDATE_CONFIRM_NO_TEXT, EMOJI_REJECT, "danger"),
    )
    return markup


def show_update_confirmation(message):
    """Show only Yes/No until the admin confirms the bot update."""
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    bot.reply_to(
        message,
        render_body_text(
            "⚙️ *UPDATE BOT*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "সব user, admin এবং owner-এর কাছে restart notification পাঠাবো?\n"
            "Yes চাপলে update mode চালু হবে, No চাপলে কিছু পরিবর্তন হবে না।"
        ),
        reply_markup=build_update_confirmation_keyboard(),
        parse_mode='HTML'
    )


def cancel_bot_update(message):
    """Leave update mode off and restore the normal admin menu."""
    with _restart_state_lock:
        if not _restart_required_users:
            global bot_update_mode
            bot_update_mode = False
    bot.reply_to(
        message,
        render_body_text(
            "❌ *UPDATE BOT cancelled.*\n"
            "Update mode বন্ধ আছে।"
        ),
        reply_markup=create_reply_keyboard_main_menu(message.from_user.id),
        parse_mode='HTML'
    )


def build_restart_only_keyboard():
    """Show exactly one reply-keyboard action while an update is active."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(make_keyboard_button(
        RESTART_BOT_BUTTON_TEXT, EMOJI_REFRESH, "success"
    ))
    return markup


def send_restart_required_notice(chat_id):
    """Remind a user that the only available action is Restart Bot."""
    bot.send_message(
        chat_id,
        render_body_text(
            "🔄 *Bot update চলছে*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "বট ব্যবহার করতে চাইলে নিচের *RESTART BOT* বাটনে ক্লিক করুন।\n"
            "Restart করলে আপনার জন্য আবার সবগুলো button চালু হবে।"
        ),
        reply_markup=build_restart_only_keyboard(),
        parse_mode='HTML'
    )


def handle_bot_restart(message):
    """Unlock one user after they press the update notification button."""
    user_id = message.from_user.id
    with _restart_state_lock:
        was_required = user_id in _restart_required_users
        if was_required:
            _restart_required_users.discard(user_id)
            if not _restart_required_users:
                global bot_update_mode
                bot_update_mode = False

    if not was_required:
        return bot.reply_to(
            message,
            render_body_text(
                "ℹ️ *এই মুহূর্তে আপনার restart করার প্রয়োজন নেই।*"
            ),
            reply_markup=create_reply_keyboard_main_menu(user_id),
            parse_mode='HTML'
        )

    bot.reply_to(
        message,
        render_body_text(
            "✅ *Bot restart success!*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "Use the bot now."
        ),
        reply_markup=create_reply_keyboard_main_menu(user_id),
        parse_mode='HTML'
    )

# The restart button must be registered before all other normal text handlers.
@bot.message_handler(func=lambda message: (
    getattr(message, 'content_type', None) == 'text'
    and (getattr(message, 'text', None) or '').strip() == RESTART_BOT_BUTTON_TEXT
))
def handle_restart_button(message):
    """Process the one-tap restart button before other text handlers."""
    handle_bot_restart(message)


@bot.message_handler(
    content_types=[
        'text', 'audio', 'document', 'photo', 'video', 'voice', 'location',
        'contact', 'sticker', 'animation', 'video_note', 'venue', 'poll'
    ],
    func=lambda message: (
        is_restart_required(message.from_user.id)
        and not (
            message.content_type == 'text'
            and (message.text or '').strip() == RESTART_BOT_BUTTON_TEXT
        )
    )
)
def handle_restart_required_message(message):
    """Block every command, upload, and old reply button until restart."""
    send_restart_required_notice(message.chat.id)


def get_bot_update_targets():
    """Return all reachable users plus every admin/owner, without duplicates."""
    try:
        targets = set(get_broadcast_targets())
    except Exception:
        targets = set(active_users)
    targets.update(
        user.get("id") for user in all_users
        if isinstance(user, dict) and user.get("id") is not None
    )
    targets.update(admin_ids)
    targets.update(admin_list)
    banned = set(banned_users)
    return [uid for uid in targets if uid not in banned]


def _send_restart_notifications(targets):
    """Deliver the update notice and restart-only keyboard to each target."""
    for user_id in targets:
        try:
            send_restart_required_notice(user_id)
        except Exception as e:
            logger.info(f"Update notification skipped {user_id}: {e}")
        time.sleep(0.05)


def activate_bot_update(message):
    """Put every known user, admin, and owner into restart-required mode."""
    global bot_update_mode
    targets = get_bot_update_targets()
    with _restart_state_lock:
        bot_update_mode = True
        _restart_required_users.update(targets)

    notice = (
        "🔄 *Bot update available*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "বট ব্যবহার করতে চাইলে নিচের *RESTART BOT* বাটনে ক্লিক করুন।\n"
        "Restart করলে সব button আবার চালু হবে।"
    )
    # The admin who clicked gets the same experience immediately; the
    # background delivery handles everyone else like a broadcast.
    try:
        bot.reply_to(
            message,
            render_body_text(notice),
            reply_markup=build_restart_only_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Could not notify update initiator: {e}")

    other_targets = [uid for uid in targets if uid != message.from_user.id]
    if other_targets:
        threading.Thread(
            target=_send_restart_notifications,
            args=(other_targets,),
            daemon=True
        ).start()
    logger.warning(
        f"Bot update mode enabled by {message.from_user.id}; "
        f"{len(targets)} users require restart."
    )


# The actual banned-user message handler is registered before all other
# message handlers below.  The function it calls is defined after database
# setup; that is safe because handlers run only after module initialization.
@bot.message_handler(
    content_types=[
        'text', 'audio', 'document', 'photo', 'video', 'voice', 'location',
        'contact', 'sticker', 'animation', 'video_note', 'venue', 'poll'
    ],
    func=lambda message: (
        is_user_banned(message.from_user.id)
        and not (
            message.content_type == 'text'
            and message.text == BANNED_SUPPORT_BUTTON_TEXT
        )
    )
)
def handle_banned_user_message(message):
    """Stop banned users before any command, button, or upload handler."""
    send_banned_user_notice(message.chat.id, message.from_user.id)


# Force Join is enforced right after the ban check and before every other
# handler, so no command or button can bypass it.
@bot.message_handler(
    content_types=[
        # Keep this list in sync with every user-facing message type.  In
        # particular, "document" must be present or a user can bypass the
        # gate by uploading a file directly.
        'text', 'audio', 'document', 'photo', 'video', 'voice', 'location',
        'contact', 'sticker', 'animation', 'video_note', 'venue', 'poll'
    ],
    func=lambda message: (
        force_join_blocked(message.from_user.id)
        and not (
            is_user_banned(message.from_user.id)
            and message.content_type == 'text'
            and message.text == BANNED_SUPPORT_BUTTON_TEXT
        )
    )
)
def handle_force_join_gate(message):
    """Block bot usage until every required channel has been joined."""
    if (message.content_type == 'text'
            and (message.text or '').strip().lower().startswith('/fjstatus')
            and is_bot_admin_user(message.from_user.id)):
        send_force_join_status(message)
        return
    missing = get_missing_force_channels(message.from_user.id, use_cache=False)
    if not missing:
        return
    send_force_join_prompt(message.chat.id, missing, message.from_user.first_name)


@bot.message_handler(commands=['fjstatus'])
def command_force_join_status(message):
    """Admin diagnostic: why is (or isn't) force join blocking users?"""
    if not is_bot_admin_user(message.from_user.id):
        return
    send_force_join_status(message)

# --- Malware Detection Configuration ---
MALWARE_SIGNATURES = [
    b'MZ',
    b'\x7fELF',
    b'\xfe\xed\xfa',
    b'\xce\xfa\xed\xfe',
    b'Rar!',
]

ENCRYPTED_FILE_INDICATORS = [
    b'openssl',
    b'encrypted',
    b'cipher',
    b'AES',
    b'DES',
    b'RSA',
    b'GPG',
    b'PGP',
]

SUSPICIOUS_KEYWORDS = [
    b'ransomware',
    b'trojan',
    b'virus',
    b'malware',
    b'backdoor',
    b'exploit',
    b'payload',
    b'botnet',
    b'keylogger',
    b'rootkit',
]

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# ✅ USER COMMAND BUTTONS (Premium Emoji + Style)
# ==========================================
COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    [{"text": "𝙐𝙋𝘿𝘼𝙏𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_UPDATE_CHANNEL_USER, "style": "primary"}],
    [{"text": "𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀", "icon_custom_emoji_id": EMOJI_UPLOAD_FILE_USER, "style": "success"},
     {"text": "𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀", "icon_custom_emoji_id": EMOJI_CHECK_FILE_USER, "style": "primary"}],
    [{"text": "𝘿𝙀𝙋𝙊𝙎𝙄𝙏", "icon_custom_emoji_id": EMOJI_DEPOSIT, "style": "success"},
     {"text": "𝙈𝙔 𝙋𝙍𝙊𝙁𝙄𝙇𝙀", "icon_custom_emoji_id": EMOJI_PROFILE_USER, "style": "primary"}],
    [{"text": "𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙋𝙇𝘼𝙉𝙎", "icon_custom_emoji_id": EMOJI_PREMIUM_PLAN_USER, "style": "success"},
     {"text": "𝙎𝙐𝙋𝙋𝙊𝙍𝙏", "icon_custom_emoji_id": EMOJI_SUPPORT, "style": "primary"}],
    [{"text": "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏", "icon_custom_emoji_id": EMOJI_FREE_HOST, "style": "primary"}]
]

# ==========================================
# ✅ ADMIN COMMAND BUTTONS (Premium Emoji + Style)
# ==========================================
ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC = [
    [{"text": "𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_UPDATE_CHANNEL_ADMIN, "style": "primary"}],
    [{"text": "𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀", "icon_custom_emoji_id": EMOJI_UPLOAD_FILE_ADMIN, "style": "success"},
     {"text": "𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀𝙎", "icon_custom_emoji_id": EMOJI_CHECK_FILE_ADMIN, "style": "primary"}],
    [{"text": "𝘽𝙊𝙏 𝙎𝙋𝙀𝙀𝘿", "icon_custom_emoji_id": EMOJI_BOT_SPEED_ADMIN, "style": "primary"},
     {"text": "𝙎𝙏𝘼𝙏𝙄𝙎𝙏𝙄𝘾𝙎", "icon_custom_emoji_id": EMOJI_STATISTICS_ADMIN, "style": "primary"}],
    [{"text": "𝙎𝙐𝘽𝙎𝘾𝙍𝙄𝙋𝙏𝙄𝙊𝙉𝙎", "icon_custom_emoji_id": EMOJI_SUBSCRIPTION_ADMIN, "style": "success"},
     {"text": "𝙇𝙊𝘾𝙆 𝘽𝙊𝙏", "icon_custom_emoji_id": EMOJI_LOCK_BOT_ADMIN, "style": "primary"}],
    [{"text": "𝙍𝙐𝙉𝙉𝙄𝙉𝙂 𝘼𝙇𝙇 𝘾𝙊𝘿𝙀", "icon_custom_emoji_id": EMOJI_RUNNING_ALL_ADMIN, "style": "success"}],
    [{"text": "𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_GX_ADMIN_PANEL, "style": "primary"}]
]

# ==========================================
# ✅ OTP GURU USER BUTTONS (Premium Emoji + Style)
# ==========================================
OTP_USER_BUTTONS = [
    [{"text": "𝙈𝙔 𝙋𝙍𝙊𝙁𝙄𝙇𝙀", "icon_custom_emoji_id": EMOJI_PROFILE_USER, "style": "primary"},
     {"text": "𝘿𝙀𝙋𝙊𝙎𝙄𝙏", "icon_custom_emoji_id": EMOJI_DEPOSIT, "style": "success"}],
    [{"text": "𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙋𝙇𝘼𝙉𝙎", "icon_custom_emoji_id": EMOJI_PREMIUM_PLAN_USER, "style": "success"},
     {"text": "𝙎𝙐𝙋𝙋𝙊𝙍𝙏", "icon_custom_emoji_id": EMOJI_SUPPORT, "style": "primary"}],
    # 🔥 Back Button Emoji পরিবর্তন
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

# ==========================================
# ✅ OTP GURU ADMIN BUTTONS (Premium Emoji + Style)
# ==========================================
OTP_ADMIN_BUTTONS = [
    [{"text": "𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉", "icon_custom_emoji_id": EMOJI_BAN_UNBAN, "style": "primary"},
     {"text": "𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎", "icon_custom_emoji_id": EMOJI_ALL_USERS, "style": "primary"}],
    [{"text": "𝘼𝙇𝙇 𝙁𝙄𝙇𝙀𝙎", "icon_custom_emoji_id": EMOJI_ALL_FILES, "style": "primary"},
     {"text": "𝙎𝙏𝙊𝙋 & 𝘿𝙀𝙇𝙀𝙏𝙀", "icon_custom_emoji_id": EMOJI_STOP_DELETE, "style": "primary"}],
    [{"text": "𝘿𝙀𝙇𝙀𝙏𝙀 𝘼𝙇𝙇 𝘿𝘼𝙏𝘼", "icon_custom_emoji_id": EMOJI_STOP_DELETE, "style": "danger"}],
    [{"text": "𝙂𝙊𝙊𝙂𝙇𝙀 𝙎𝙔𝙉𝘾 𝙎𝙏𝘼𝙏𝙐𝙎", "icon_custom_emoji_id": EMOJI_STATUS, "style": "primary"}],
    [{"text": "𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_ADMIN_PANEL, "style": "success"}],
    [{"text": "𝙎𝙀𝙏 𝙇𝙄𝙈𝙄𝙏", "icon_custom_emoji_id": EMOJI_SET_LIMIT, "style": "primary"},
     {"text": "𝙁𝙍𝙀𝙀 𝙐𝙎𝙀𝙍 𝙇𝙄𝙈𝙄𝙏", "icon_custom_emoji_id": EMOJI_SET_LIMIT, "style": "primary"}],
    [{"text": "𝙎𝙚𝙩 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙋𝙡𝙖𝙣", "icon_custom_emoji_id": EMOJI_SET_PREMIUM, "style": "success"}],
    [{"text": "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙎𝙔𝙎𝙏𝙀𝙈", "icon_custom_emoji_id": EMOJI_DEPOSITE_METHOD, "style": "success"}],
    [{"text": "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙂𝙍𝙐𝙋𝙀", "icon_custom_emoji_id": EMOJI_GROUP_SET, "style": "primary"}],
    [{"text": "𝙁𝙄𝙇𝙀 𝙁𝙊𝙍𝙒𝘼𝙍𝘿 𝙂𝙍𝙊𝙐𝙋", "icon_custom_emoji_id": EMOJI_GROUP_SET, "style": "primary"}],
    [{"text": "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏", "icon_custom_emoji_id": EMOJI_FREE_HOST_ADMIN, "style": "success"}],
     [{"text": "𝙁𝙊𝙍𝘾𝙀 𝙅𝙊𝙄𝙉", "icon_custom_emoji_id": EMOJI_LOCK, "style": "primary"},
     {"text": "𝘼𝙇𝙇 𝙇𝙄𝙉𝙆 𝙎𝙀𝙏𝙐𝙋", "icon_custom_emoji_id": EMOJI_PIN, "style": "primary"}],
    [{"text": "𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏", "icon_custom_emoji_id": EMOJI_MEGAPHONE, "style": "success"}],
    # 🔥 Back Button Emoji পরিবর্তন
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

# ==========================================
# ✅ UPLOAD MODULE INSTALL MODE BUTTONS
# ==========================================
UPLOAD_MODE_BUTTONS = [
    [{"text": "𝘼𝙐𝙏𝙊 𝙈𝙊𝘿𝙐𝙇𝙀 𝙄𝙉𝙎𝙏𝘼𝙇𝙇",
      "icon_custom_emoji_id": EMOJI_REFRESH, "style": "success"}],
    [{"text": "𝙈𝘼𝙉𝙐𝘼𝙇 𝙈𝙊𝘿𝙐𝙇𝙀 𝙄𝙉𝙎𝙏𝘼𝙇𝙇",
      "icon_custom_emoji_id": EMOJI_FILE, "style": "primary"}],
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉",
      "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}],
]
BANNED_SUPPORT_BUTTON_TEXT = "𝙎𝙐𝙋𝙋𝙊𝙍𝙏"

REFERRAL_ADMIN_BUTTONS = [
    [{"text": "𝙎𝙀𝙏 𝙍𝙀𝙁𝙁𝙀𝙍 𝘽𝙊𝙉𝙐𝙎",
      "icon_custom_emoji_id": EMOJI_REFERRAL_ADMIN, "style": "success"}],
    [{"text": "𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
      "icon_custom_emoji_id": EMOJI_FREE_HOST_ADMIN, "style": "primary"}],
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
      "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}],
]

FREE_HOST_PLAN_ADMIN_BUTTONS = [
    [{"text": "𝘼𝘿𝘿 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
      "icon_custom_emoji_id": EMOJI_PLUS, "style": "success"}],
    [{"text": "𝙍𝙀𝙈𝙊𝙑𝙀 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
      "icon_custom_emoji_id": EMOJI_MINUS, "style": "danger"}],
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙍𝙀𝙁𝙁𝙀𝙍 𝙎𝙀𝙏𝙏𝙄𝙉𝙂𝙎",
      "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}],
]

# ==========================================
# ✅ OTP BAN SUB-MENU BUTTONS (Premium Emoji + Style)
# ==========================================
OTP_BAN_BUTTONS = [
    [{"text": "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "icon_custom_emoji_id": EMOJI_SHOW_BAN, "style": "primary"}],
    [{"text": "𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "icon_custom_emoji_id": EMOJI_BAN_USER, "style": "primary"}],
    [{"text": "𝙐𝙉𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "icon_custom_emoji_id": EMOJI_UNBAN_USER, "style": "success"}],
    # 🔥 Back Button Emoji সেট করুন
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

@bot.message_handler(func=lambda message: message.text in [
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇"
])
def handle_ban_back_to_admin(message):
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    handle_otp_admin_panel(message)

# ==========================================
# ✅ OTP DEPOSITE SUB-MENU BUTTONS (Premium Emoji + Style)
# ==========================================
OTP_DEPOSITE_BUTTONS = [
    [{"text": "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙍𝙀𝙌𝙐𝙀𝙎𝙏", "icon_custom_emoji_id": EMOJI_DEPOSIT_REQUEST, "style": "primary"}],
    [{"text": "𝙎𝙀𝙏 𝘿𝙀𝙋𝙊𝙎𝙄𝙏 𝙉𝙐𝙈𝘽𝙀𝙍 𝘼𝙉𝘿 𝙄𝘿", "icon_custom_emoji_id": EMOJI_DEPOSITE_METHOD, "style": "primary"}],
    [{"text": "𝘿𝙀𝙇𝙀𝙏𝙀 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙈𝙀𝙏𝙃𝙊𝘿", "icon_custom_emoji_id": EMOJI_STOP_DELETE, "style": "primary"}],
    # 🔥 Back Button Emoji পরিবর্তন
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

# ==========================================
# ✅ PREMIUM PLAN ADMIN BUTTONS (Premium Emoji + Style)
# ==========================================
PREMIUM_PLAN_ADMIN_BUTTONS = [
    [{"text": "Add Plan", "icon_custom_emoji_id": EMOJI_ADD_ADMIN, "style": "success"}],
    [{"text": "Remove Plan", "icon_custom_emoji_id": EMOJI_REMOVE_ADMIN, "style": "danger"}],
    [{"text": "Reset All Plans", "icon_custom_emoji_id": EMOJI_STOP_DELETE, "style": "danger"}],
    [{"text": "Show All Plans", "icon_custom_emoji_id": EMOJI_FILE, "style": "primary"}],
    [{"text": "BACK TO ADMIN PANEL", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

@bot.message_handler(func=lambda message: message.text in [
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇"
])
def handle_premium_back_to_admin(message):
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    handle_premium_plan_admin(message)

# ==========================================
# ✅ PREMIUM PLAN USER BUTTONS (Premium Emoji + Style)
# ==========================================
PREMIUM_PLAN_USER_BUTTONS = [
    [{"text": "Buy Plan", "icon_custom_emoji_id": EMOJI_BUY_PLAN, "style": "success"}],
    [{"text": "Deposit", "icon_custom_emoji_id": EMOJI_DEPOSIT, "style": "success"}],
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

# ==========================================
# ✅ ADMIN PANEL BUTTONS (Premium Emoji + Style)
# ==========================================
ADMIN_PANEL_BUTTONS = [
    [{"text": "𝙎𝙃𝙊𝙒 𝘼𝘿𝙈𝙄𝙉𝙎", "icon_custom_emoji_id": EMOJI_SHOW_ADMINS, "style": "primary"}],
    [{"text": "𝘼𝘿𝘿 𝘼𝘿𝙈𝙄𝙉", "icon_custom_emoji_id": EMOJI_ADD_ADMIN, "style": "success"}],
    [{"text": "𝙍𝙀𝙈𝙊𝙑𝙀 𝘼𝘿𝙈𝙄𝙉", "icon_custom_emoji_id": EMOJI_REMOVE_ADMIN, "style": "primary"}],
    [{"text": "𝙏𝙍𝘼𝙉𝙎𝙁𝙀𝙍 𝙊𝙒𝙉𝙀𝙍𝙎𝙃𝙄𝙋", "icon_custom_emoji_id": EMOJI_ADMIN_PANEL, "style": "success"}],
    # 🔥 Back Button Emoji পরিবর্তন
    [{"text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", "icon_custom_emoji_id": EMOJI_BACK, "style": "primary"}]
]

# ==========================================
# ✅ KEYBOARD BUILDING FUNCTIONS
# ==========================================

def build_reply_keyboard(button_layout):
    """Build an official Telegram coloured reply keyboard.

    `style` and `icon_custom_emoji_id` are Bot API fields supported by
    pyTelegramBotAPI 4.36+.  Keep a plain-text fallback so an older local
    library does not take the whole bot down while it is being upgraded.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for row in button_layout:
        buttons = []
        for btn in row:
            text = btn.get("text", "")
            buttons.append(make_keyboard_button(
                text,
                btn.get("icon_custom_emoji_id", CUSTOM_EMOJI_ID),
                btn.get("style", "primary")
            ))
        markup.add(*buttons)
    return markup

def create_reply_keyboard_main_menu(user_id):
    """Create main menu reply keyboard with premium emoji"""
    if user_id in admin_ids or user_id in admin_list or user_id == OWNER_ID:
        return build_reply_keyboard(ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC)
    else:
        return build_reply_keyboard(COMMAND_BUTTONS_LAYOUT_USER_SPEC)


def create_picture_reply_keyboard(user_id):
    """Main-menu keyboard used alongside the user's profile picture."""
    layout = (
        ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC
        if user_id in admin_ids or user_id in admin_list or user_id == OWNER_ID
        else COMMAND_BUTTONS_LAYOUT_USER_SPEC
    )
    return build_reply_keyboard(layout + [[{
        "text": "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉",
        "icon_custom_emoji_id": EMOJI_BACK,
        "style": "primary",
    }]])


def create_otp_reply_keyboard(user_id):
    """Create OTP reply keyboard with premium emoji"""
    if user_id in admin_ids or user_id in admin_list:
        return build_reply_keyboard(OTP_ADMIN_BUTTONS)
    else:
        return build_reply_keyboard(OTP_USER_BUTTONS)

def create_upload_mode_keyboard():
    """Create the Auto/Manual dependency selection keyboard."""
    return build_reply_keyboard(UPLOAD_MODE_BUTTONS)

def create_banned_support_keyboard():
    """Give banned users exactly one usable reply-keyboard button."""
    return build_reply_keyboard([[
        {
            "text": BANNED_SUPPORT_BUTTON_TEXT,
            "icon_custom_emoji_id": EMOJI_SUPPORT,
            "style": "primary",
        }
    ]])

def create_otp_ban_keyboard():
    """Create OTP ban sub-menu keyboard with premium emoji"""
    return build_reply_keyboard(OTP_BAN_BUTTONS)

def create_otp_deposite_keyboard():
    """Create OTP deposite sub-menu keyboard with premium emoji"""
    return build_reply_keyboard(OTP_DEPOSITE_BUTTONS)

def create_premium_admin_keyboard():
    """Create premium plan admin keyboard with premium emoji"""
    return build_reply_keyboard(PREMIUM_PLAN_ADMIN_BUTTONS)

def create_premium_user_keyboard():
    """Create premium plan user keyboard with colors"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Buy Plan - Green
    markup.add(
        types.InlineKeyboardButton(
            "💎 Buy Plan",
            callback_data='buy_plan',
            style="success"
        )
    )
    
    # Deposit - Blue
    markup.add(
        types.InlineKeyboardButton(
            "💰 Deposit",
            callback_data='deposit',
            style="primary"
        )
    )
    
    # Back - Red
    markup.add(
        types.InlineKeyboardButton(
            "🔙 BACK TO MAIN",
            callback_data='back_to_main',
            style="danger"
        )
    )
    
    return markup
    build_reply_keyboard(PREMIUM_PLAN_USER_BUTTONS)

def create_admin_panel_keyboard():
    """Create admin panel keyboard with premium emoji"""
    return build_reply_keyboard(ADMIN_PANEL_BUTTONS)

# ==========================================
# ✅ ADMIN PANEL - COMPLETE FIX
# ==========================================

def gx_admin_panel_callback(call):
    """Open the admin panel from the main inline menu."""
    bot.answer_callback_query(call.id)
    if not is_otp_admin(call.from_user.id):
        bot.send_message(call.message.chat.id, "⛔ Unauthorized!", parse_mode='HTML')
        return
    bot.send_message(
        call.message.chat.id,
        render_body_text(
            "👑 *ADMIN PANEL*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=create_admin_panel_keyboard(),
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == "𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇")
def admin_panel_main(message):
    """Handle admin panel main - COMPLETE FIX"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    markup = create_admin_panel_keyboard()
    
    bot.reply_to(message, 
        render_body_text(
            "👑 *ADMIN PANEL*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

# ==========================================
@bot.message_handler(func=lambda message: message.text in ["bKash", "Nagad", "Rocket", "Upay", "Binance"])
def handle_deposit_method_click(message):
    """Handle deposit method selection from reply keyboard"""
    user_id = message.from_user.id
    method_name = message.text
    
    # pending চেক
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'", (user_id,))
        if c.fetchone():
            conn.close()
            bot.reply_to(message, 
                render_body_text(
                    f"⏳ *আপনার ইতিমধ্যে একটি pending ডিপোজিট রিকোয়েস্ট আছে!*\n"
                    f"📌 *দয়া করে অ্যাডমিনের অ্যাপ্রুভের জন্য অপেক্ষা করুন।*"
                ),
                parse_mode='HTML'
            )
            return
        conn.close()
    except Exception as e:
        logger.error(f"Error checking pending deposit: {e}")
    
    method = get_payment_method(method_name)
    if not method:
        bot.reply_to(message, "❌ *মেথড পাওয়া যায়নি!*", parse_mode='HTML')
        return
    
    method_name = get_payment_method_label(method_name)
    method_emoji = get_payment_method_emoji(method_name)
    
    unit = "USDT" if method_name.lower() == 'binance' else "BDT"
    
    bot.reply_to(message,
        render_body_text(
            f"{method_emoji} *পেমেন্ট মেথড:* {method_name}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 নম্বর/আইডি: `{method['number']}`\n"
            f"💰 *ন্যূনতম:* {method['min_deposit']} {unit}\n\n"
            f"📌 *আপনি কত {unit} ডিপোজিট করতে চান?*\n"
            f"💡 *শুধু সংখ্যা লিখুন:*"
        ),
        parse_mode='HTML'
    )
    
    bot.register_next_step_handler(message, process_deposit_amount, method_name)
#hamdellar back buttun#
@bot.message_handler(func=lambda message: message.text in (
    "BACK TO MAIN",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉",
))
def handle_back_to_main_from_deposit(message):
    """Handle every reply-keyboard back button that returns to the main menu."""
    go_back_to_main(message)
# ✅ ADMIN PANEL BUTTON HANDLERS - COMPLETE FIX
# ==========================================

@bot.message_handler(func=lambda message: message.text == "𝙎𝙃𝙊𝙒 𝘼𝘿𝙈𝙄𝙉𝙎")
def show_admins(message):
    """Show all admins"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    if not admin_list:
        bot.reply_to(message, 
            render_body_text(
                "📌 *কোনো অ্যাডমিন নেই!*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "💡 *এখনো কোনো অ্যাডমিন যোগ করা হয়নি।*"
            ),
            parse_mode='HTML'
        )
        return
    
    admin_text = render_body_text("👑 *অ্যাডমিন লিস্ট*\n")
    admin_text += "━━━━━━━━━━━━━━━━━\n\n"
    
    for i, uid in enumerate(admin_list, 1):
        try:
            chat = bot.get_chat(uid)
            name = chat.first_name or "Unknown"
            username = f"@{chat.username}" if chat.username else "@unknown"
        except:
            name = "Unknown"
            username = "@unknown"
        
        role = "👑 ওনার" if uid == OWNER_ID else "🔹 অ্যাডমিন"
        admin_text += f"{i}. *{keep_user_name_emojis_normal(name)}*\n"
        admin_text += f"   🆔 `{uid}`\n"
        admin_text += f"   📌 {keep_user_name_emojis_normal(username)}\n"
        admin_text += f"   👑 {role}\n\n"
    
    owner_count = 1 if OWNER_ID in admin_list else 0
    admin_count = len(admin_list) - owner_count
    
    admin_text += f"━━━━━━━━━━━━━━━━━\n"
    admin_text += f"📊 *মোট অ্যাডমিন:* {len(admin_list)} জন\n"
    admin_text += f"👑 *ওনার:* {owner_count} জন\n"
    admin_text += f"🔹 *অ্যাডমিন:* {admin_count} জন"
    
    # ✅ render_body_text() এর ভিতরে পুরো মেসেজ দিন
    bot.reply_to(message, render_body_text(admin_text), parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "𝘼𝘿𝘿 𝘼𝘿𝙈𝙄𝙉")
def add_admin_button(message):
    """Handle add admin"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            "➕ *Add Admin*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Send the User ID to add as admin:*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_add_admin_from_button)

def process_add_admin_from_button(message):
    """Process add admin"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, render_body_text("❌ *Invalid User ID!*"), parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user in admin_list:
        bot.reply_to(message, render_body_text(f"⚠️ *User `{target_user}` is already an admin!*"), parse_mode='HTML')
        return
    
    admin_list.append(target_user)
    add_admin_db(target_user)
    bot.reply_to(message, 
        render_body_text(
            f"✅ *Admin Added!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User ID: `{target_user}`\n"
            f"✅ *সফলভাবে অ্যাডমিন যোগ করা হয়েছে!*"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"🎉 *আপনাকে অ্যাডমিন করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 অ্যাডমিন: {user_id}\n"
                f"✅ এখন থেকে আপনি বট পরিচালনা করতে পারবেন!"
            ),
            parse_mode='HTML'
        )
    except:
        pass

@bot.message_handler(func=lambda message: message.text == "𝙍𝙀𝙈𝙊𝙑𝙀 𝘼𝘿𝙈𝙄𝙉")
def remove_admin_button(message):
    """Handle remove admin"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            "➖ *Remove Admin*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Send the User ID to remove from admin:*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_remove_admin_from_button)

def process_remove_admin_from_button(message):
    """Process remove admin"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, render_body_text("❌ *Invalid User ID!*"), parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user == OWNER_ID:
        bot.reply_to(message, render_body_text("❌ *Cannot remove Owner!*"), parse_mode='HTML')
        return
    
    if target_user not in admin_list:
        bot.reply_to(message, render_body_text(f"⚠️ *User `{target_user}` is not an admin!*"), parse_mode='HTML')
        return
    
    admin_list.remove(target_user)
    remove_admin_db(target_user)
    bot.reply_to(message, 
        render_body_text(
            f"✅ *Admin Removed!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User ID: `{target_user}`\n"
            f"✅ সফলভাবে অ্যাডমিন রিমুভ করা হয়েছে!"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"⚠️ *আপনাকে অ্যাডমিন থেকে রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 অ্যাডমিন: {user_id}\n"
                f"❌ এখন থেকে আপনি বট পরিচালনা করতে পারবেন না!"
            ),
            parse_mode='HTML'
        )
    except:
        pass

@bot.message_handler(func=lambda message: message.text == "𝙏𝙍𝘼𝙉𝙎𝙁𝙀𝙍 𝙊𝙒𝙉𝙀𝙍𝙎𝙃𝙄𝙋")
def transfer_ownership_button(message):
    """Handle transfer ownership"""
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        bot.reply_to(message, render_body_text("⛔ *Only Owner Can Transfer Ownership!*"), parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            "👑 *Transfer Ownership*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Send the User ID to transfer ownership:*\n\n"
            "⚠️ *Warning: After transfer, you will lose Owner access!*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_transfer_ownership_from_button)

# ==========================================
def create_premium_plans_reply_keyboard():
    """Create premium plans reply keyboard with premium emojis"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # 🔥 নতুন ইমোজি আইডি সেট করুন
    NEW_EMOJI_ID = "6237596959784309794"
    
    for plan in premium_plans:
        # 🔥 সব প্ল্যানের জন্য একই নতুন ইমোজি ব্যবহার করুন
        btn = make_keyboard_button(
            f"কিনুন {plan.get('plan_name', 'Basic')} - {plan['days']} days - ৳{plan['price']}",
            NEW_EMOJI_ID,
            "primary"
        )
        markup.add(btn)
    
    # 🔥 BACK বাটন (আগের মতো)
    back_btn = make_keyboard_button("BACK TO MAIN", EMOJI_BACK, "danger")
    markup.add(back_btn)
    
    return markup
@bot.message_handler(func=lambda message: message.text.startswith("কিনুন"))
def handle_buy_plan_from_reply(message):
    """Handle buy plan from reply keyboard"""
    user_id = message.from_user.id
    text = (message.text or "").strip()

    # The button is generated as:
    # ``কিনুন <full plan name> - <days> days - ৳<price>``.
    # The old regex stopped at the first hyphen, so ``VIP-1`` became
    # ``VIP`` and every hyphenated plan was reported as missing.
    plan_label = re.sub(r"^কিনুন\s+", "", text, count=1).strip()
    plan_name = plan_label.split(" - ", 1)[0].strip()
    if not plan_name:
        bot.reply_to(message, "❌ *প্লান পাওয়া যায়নি!*", parse_mode='HTML')
        return

    # Match the complete stored name, including names such as VIP-1, VIP-2,
    # or names containing spaces.
    plan = None
    for p in premium_plans:
        stored_name = str(p.get("plan_name", "")).strip()
        if stored_name.casefold() == plan_name.casefold():
            plan = p
            break
    
    if not plan:
        bot.reply_to(message, f"❌ *'{plan_name}' প্লান পাওয়া যায়নি!*", parse_mode='HTML')
        return
    
    # 🔥 ব্যালেন্স চেক
    balance = get_user_balance_db(user_id)
    
    if balance < plan['price']:
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *{balance_emoji_tag()} ব্যালেন্স কম!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"{balance_emoji_tag()} *প্রয়োজন:* ৳{plan['price']}\n"
                f"{balance_emoji_tag()} *আছে:* ৳{balance}\n\n"
                f"💡 *ডিপোজিট করে আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )
        return
    
    # Deduct only when the balance update succeeds.  If activation fails,
    # refund the balance so a database error cannot charge the user without
    # giving the plan.
    if not update_user_balance_db(user_id, -plan["price"]):
        bot.reply_to(
            message,
            render_body_text("❌ *ব্যালেন্স আপডেট করা যায়নি। আবার চেষ্টা করুন।*"),
            parse_mode="HTML",
        )
        return
    
    expiry = datetime.now() + timedelta(days=plan['days'])
    if not save_user_premium_plan(
        user_id, plan["id"], expiry, plan["file_limit"]
    ):
        update_user_balance_db(user_id, plan["price"])
        bot.reply_to(
            message,
            render_body_text(
                "❌ *প্লান অ্যাক্টিভেট করা যায়নি। আপনার টাকা ফেরত দেওয়া হয়েছে।*"
            ),
            parse_mode="HTML",
        )
        return
    
    # 🔥 সাকসেস মেসেজ
    bot.reply_to(
        message,
        render_body_text(
            f"🎉 *প্লান সফলভাবে অ্যাক্টিভেটেড!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *প্ল্যান:* {plan.get('plan_name', 'Basic')}\n"
            f"📁 *ফাইল লিমিট:* {plan['file_limit']} টি\n"
            f"📅 *মেয়াদ:* {plan['days']} দিন\n"
            f"{price_emoji_tag()} *মূল্য:* ৳{plan['price']}\n"
            f"📅 *শেষ তারিখ:* {expiry.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"{balance_emoji_tag()} *বর্তমান ব্যালেন্স:* ৳{get_user_balance_db(user_id):.2f}\n\n"
            f"💡 *এখন থেকে {plan['file_limit']} টি ফাইল আপলোড করতে পারবেন!*"
        ),
        parse_mode='HTML'
    )
# ✅ SUBSCRIPTION BUTTON HANDLERS (শুধু বাটন)
# ==========================================

def _subscription_cancel_requested(message):
    """Return True for every cancel control used by subscription flows."""
    text = (getattr(message, "text", "") or "").strip().lower()
    return text in {"/cancel", "cancel", "🔙 cancel"}

@bot.message_handler(func=lambda message: message.text in ["𝘼𝙙𝙙 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", "➕ Add Subscription"])
def handle_add_subscription_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Admin permissions required."), parse_mode='HTML')
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        make_keyboard_button("Cancel", EMOJI_REJECT, "danger", use_override=False)
    )
    
    msg = bot.reply_to(
        message, 
        render_body_text(
            f"<tg-emoji emoji-id=\"{EMOJI_GIFT_BOX}\">🎁</tg-emoji> *Add Subscription*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Enter User ID & days:*\n"
            "Example: `12345678 30`\n\n"
            "💡 *Type /cancel to abort*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_add_subscription_details)


@bot.message_handler(func=lambda message: message.text in ["𝙍𝙚𝙢𝙤𝙫𝙚 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", "➖ Remove Subscription"])
def handle_remove_subscription_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Admin permissions required."), parse_mode='HTML')
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        make_keyboard_button("Cancel", EMOJI_REJECT, "danger", use_override=False)
    )
    
    msg = bot.reply_to(
        message, 
        render_body_text(
            f"<tg-emoji emoji-id=\"{EMOJI_SUB_REMOVE}\">➖</tg-emoji> *Remove Subscription*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Enter User ID to remove sub:*\n"
            "Example: `12345678`\n\n"
            "💡 *Type /cancel to abort*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_remove_subscription_id)


@bot.message_handler(func=lambda message: message.text in ["𝘾𝙝𝙚𝙘𝙠 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", "✅ Check Subscription"])
def handle_check_subscription_button(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Admin permissions required."), parse_mode='HTML')
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        make_keyboard_button("Cancel", EMOJI_REJECT, "danger", use_override=False)
    )
    
    msg = bot.reply_to(
        message, 
        render_body_text(
            f"<tg-emoji emoji-id=\"{EMOJI_SUB_CHECK}\">✅</tg-emoji> *Check Subscription*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 *Enter User ID to check sub:*\n"
            "Example: `12345678`\n\n"
            "💡 *Type /cancel to abort*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_check_subscription_id)


@bot.message_handler(func=lambda message: message.text in ["𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "BACK TO MAIN", "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "BACK TO MAIN"])
def handle_back_to_main_from_subscription(message):
    go_back_to_main(message)


@bot.message_handler(func=lambda message: message.text == "Cancel")
def handle_cancel_from_subscription(message):
    _logic_subscriptions_panel(message)

def process_transfer_ownership_from_button(message):
    """Process transfer ownership"""
    global OWNER_ID
    
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id != OWNER_ID:
        bot.reply_to(message, render_body_text("⛔ *Only Owner can transfer!*"), parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, render_body_text("❌ *Invalid User ID!*"), parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user == OWNER_ID:
        bot.reply_to(message, render_body_text("⚠️ *You are already the Owner!*"), parse_mode='HTML')
        return
    
    old_owner = OWNER_ID
    OWNER_ID = target_user
    
    if old_owner not in admin_list:
        admin_list.append(old_owner)
    
    bot.reply_to(message, 
        render_body_text(
            f"👑 *Ownership Transferred!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"✅ New Owner: `{target_user}`\n"
            f"👤 Previous Owner: `{old_owner}`\n"
            f"✅ সফলভাবে ওনারশিপ ট্রান্সফার করা হয়েছে!"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"👑 *আপনি এখন বটের নতুন ওনার!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"✅ আপনি এখন বট সম্পূর্ণভাবে পরিচালনা করতে পারবেন!"
            ),
            parse_mode='HTML'
        )
    except:
        pass

@bot.message_handler(func=lambda message: message.text == "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾")
def back_to_admin_panel(message):
    """Go back to admin panel"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    admin_panel_main(message)

# ==========================================
# ✅ DATABASE SETUP
# ==========================================

def init_db():
    """Initialize the persistent SQLite schema."""
    logger.info("Initializing durable SQLite schema at %s.", DATABASE_PATH)
    
    try:
        conn = sqlite3.connect(
            DATABASE_PATH, check_same_thread=False, timeout=30
        )
        c = conn.cursor()
        
        c.execute("PRAGMA journal_mode = WAL")
        c.execute("PRAGMA busy_timeout = 30000")
        c.execute('PRAGMA foreign_keys = ON')
        
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT, upload_time TEXT, is_stopped INTEGER DEFAULT 0,
                      PRIMARY KEY (user_id, file_name))''')

        c.execute('''CREATE TABLE IF NOT EXISTS hosted_bot_backups
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      drive_file_id TEXT DEFAULT '',
                      desired_status TEXT DEFAULT 'stopped',
                      backup_pending INTEGER NOT NULL DEFAULT 0,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute("PRAGMA table_info(hosted_bot_backups)")
        hosted_backup_columns = [col[1] for col in c.fetchall()]
        if "backup_pending" not in hosted_backup_columns:
            c.execute(
                "ALTER TABLE hosted_bot_backups "
                "ADD COLUMN backup_pending INTEGER NOT NULL DEFAULT 0"
            )

        # Lifetime upload/delete quota.  Deleting a file never decrements
        # action_count; only an admin reset can make the quota available again.
        c.execute('''CREATE TABLE IF NOT EXISTS user_file_action_quota
                     (user_id INTEGER PRIMARY KEY,
                      action_count INTEGER NOT NULL DEFAULT 0,
                      limit_notified INTEGER NOT NULL DEFAULT 0,
                      updated_at TEXT NOT NULL)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')

        # Telegram profile details used by the consolidated Google Sheets
        # "Users" view.  Keeping this in the durable schema means names and
        # usernames survive restarts instead of existing only in all_users.
        c.execute('''CREATE TABLE IF NOT EXISTS user_profiles
                     (user_id INTEGER PRIMARY KEY,
                      name TEXT DEFAULT '',
                      username TEXT DEFAULT '',
                      joined_at TEXT DEFAULT '')''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS free_user_settings
                     (id INTEGER PRIMARY KEY, limit_value INTEGER, time_value INTEGER, host_time INTEGER)''')
        
        c.execute('INSERT OR IGNORE INTO free_user_settings (id, limit_value, time_value, host_time) VALUES (1, ?, ?, ?)', 
                  (FREE_USER_LIMIT_SETTINGS["limit"], FREE_USER_LIMIT_SETTINGS["time"], FREE_USER_LIMIT_SETTINGS["host_time"]))
        
        c.execute('''CREATE TABLE IF NOT EXISTS premium_plans (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     plan_name TEXT,
                     file_limit INTEGER,
                     days INTEGER,
                     price INTEGER
                     )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_premium
                     (user_id INTEGER PRIMARY KEY, plan_id INTEGER, expiry TEXT, file_limit INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS payment_methods (
                     name TEXT PRIMARY KEY,
                     number_or_address TEXT,
                     min_deposit REAL DEFAULT 10.0,
                     icon_key TEXT DEFAULT 'card'
                     )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS deposits_new (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     amount REAL,
                     method TEXT,
                     trx_id TEXT UNIQUE,
                     status TEXT DEFAULT 'pending',
                     approved_by INTEGER,
                     approved_at TIMESTAMP,
                     screenshot_file_id TEXT DEFAULT '',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        # Older databases predate the manual-payment screenshot requirement.
        c.execute("PRAGMA table_info(deposits_new)")
        deposit_columns = [col[1] for col in c.fetchall()]
        if 'screenshot_file_id' not in deposit_columns:
            c.execute(
                "ALTER TABLE deposits_new ADD COLUMN screenshot_file_id TEXT DEFAULT ''"
            )
        
        c.execute('''CREATE TABLE IF NOT EXISTS user_balances
                     (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS settings
                     (key TEXT PRIMARY KEY, value TEXT)''')
        
        # --- NEW TABLES FOR BINANCE PAY INTEGRATION ---
        c.execute('''CREATE TABLE IF NOT EXISTS plans (
                     plan_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT, 
                     file_limit INTEGER, 
                     price TEXT, 
                     duration INTEGER, 
                     buy_link TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS pending_payments
                     (user_id INTEGER, plan_id INTEGER, paid_amount REAL,
                      PRIMARY KEY (user_id, plan_id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS used_txids
                     (tx_id TEXT PRIMARY KEY)''')

        c.execute('''CREATE TABLE IF NOT EXISTS banned_users (
                     user_id INTEGER PRIMARY KEY,
                     reason TEXT DEFAULT '',
                     banned_by INTEGER,
                     transaction_id TEXT DEFAULT '',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')

        # --- REFERRAL AND FREE HOSTING TABLES ---
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     referrer_id INTEGER NOT NULL,
                     referred_id INTEGER NOT NULL UNIQUE,
                     referral_code TEXT NOT NULL,
                     referred_username TEXT DEFAULT '',
                     referred_name TEXT DEFAULT '',
                     status TEXT DEFAULT 'verified',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS referral_strikes (
                     user_id INTEGER PRIMARY KEY,
                     strike_count INTEGER DEFAULT 0,
                     last_reason TEXT DEFAULT '',
                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS referral_codes (
                     user_id INTEGER PRIMARY KEY,
                     code TEXT NOT NULL UNIQUE,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS free_host_plans (
                     id INTEGER PRIMARY KEY,
                     plan_name TEXT NOT NULL,
                     referral_target INTEGER NOT NULL,
                     host_hours INTEGER NOT NULL,
                     file_limit INTEGER NOT NULL,
                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS free_host_grants (
                     user_id INTEGER PRIMARY KEY,
                     plan_id INTEGER NOT NULL,
                     plan_name TEXT NOT NULL,
                     host_hours INTEGER NOT NULL,
                     file_limit INTEGER NOT NULL,
                     activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     expiry TEXT NOT NULL
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS free_host_plan_claims (
                     user_id INTEGER NOT NULL,
                     plan_id INTEGER NOT NULL,
                     claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     PRIMARY KEY (user_id, plan_id)
                     )''')
        # Preserve one-time claim behaviour for grants created by older
        # versions that activated a plan automatically.
        c.execute(
            """INSERT OR IGNORE INTO free_host_plan_claims (user_id, plan_id)
               SELECT user_id, plan_id FROM free_host_grants"""
        )
        
        # --- GROUP SETTINGS TABLE ---
        c.execute('''CREATE TABLE IF NOT EXISTS group_settings
                     (id INTEGER PRIMARY KEY, group_id TEXT)''')
        c.execute('INSERT OR IGNORE INTO group_settings (id, group_id) VALUES (1, "")')
        
        # --- FILE FORWARD GROUP TABLE ---
        c.execute('''CREATE TABLE IF NOT EXISTS file_forward_group
                     (id INTEGER PRIMARY KEY, group_id TEXT)''')
        c.execute('INSERT OR IGNORE INTO file_forward_group (id, group_id) VALUES (1, "")')
        # --- END NEW TABLES ---
        
        default_methods = [
            ('bKash', '01700000000', 10.0, 'bkash'),
            ('Nagad', '01700000000', 10.0, 'nagad'),
            ('Rocket', '01700000000', 10.0, 'rocket'),
            ('Upay', '01700000000', 10.0, 'upay'),
            ('Binance', 'binance_pay_id_here', 0.1, 'binance')
        ]
        for m_name, m_num, m_min, m_icon in default_methods:
            c.execute("INSERT OR IGNORE INTO payment_methods (name, number_or_address, min_deposit, icon_key) VALUES (?, ?, ?, ?)", 
                      (m_name, m_num, m_min, m_icon))
        
        # --- FORCE JOIN CHANNELS TABLE ---
        c.execute('''CREATE TABLE IF NOT EXISTS force_join_channels (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     button_name TEXT NOT NULL,
                     channel_url TEXT NOT NULL,
                     chat_ref TEXT DEFAULT '',
                     chat_id INTEGER,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                     )''')

        # Older installs created the table without chat_id.
        c.execute("PRAGMA table_info(force_join_channels)")
        if 'chat_id' not in [col[1] for col in c.fetchall()]:
            c.execute("ALTER TABLE force_join_channels ADD COLUMN chat_id INTEGER")

        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('force_join_enabled', '1')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('force_join_admin_bypass', '1')")

        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('referral_commission', '10')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('referral_bonus', '0')")
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('usdt_rate', '120')")

        for _lk, _lv in DEFAULT_LINKS.items():
            c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (_lk, _lv))
        
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Runtime schema initialized successfully.")
        
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        logger.info(f"📊 Tables: {[t[0] for t in tables]}")
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
        # Never delete or recreate the database automatically.  That old
        # recovery path could destroy users, subscriptions, files, and
        # settings after a transient SQLite error.
        logger.critical(
            "Database was not initialized; existing data was preserved. "
            "Fix the storage error before restarting the bot."
        )

def load_data():
    """Load data from database into memory"""
    global plan_id_counter
    logger.info("Loading data from database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"⚠️ Invalid expiry date format for user {user_id}: {expiry}. Skipping.")

        c.execute('SELECT user_id, file_name, file_type, upload_time, is_stopped FROM user_files')
        for user_id, file_name, file_type, upload_time, is_stopped in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))
            if is_stopped:
                if user_id not in file_stop_status:
                    file_stop_status[user_id] = []
                file_stop_status[user_id].append(file_name)

        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())

        c.execute(
            'SELECT user_id, name, username, joined_at FROM user_profiles'
        )
        for user_id, name, username, joined_at in c.fetchall():
            all_users.append({
                "id": user_id,
                "name": name or "Unknown",
                "username": username or "@unknown",
                "joined": joined_at or "",
                "balance": 0,
                "files_count": 0,
            })

        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall())

        c.execute('SELECT user_id FROM banned_users')
        banned_users.extend(
            user_id for (user_id,) in c.fetchall()
            if user_id not in banned_users
        )

        c.execute('SELECT limit_value, time_value, host_time FROM free_user_settings WHERE id = 1')
        row = c.fetchone()
        if row:
            FREE_USER_LIMIT_SETTINGS["limit"] = row[0]
            FREE_USER_LIMIT_SETTINGS["time"] = row[1]
            FREE_USER_LIMIT_SETTINGS["host_time"] = row[2]

        c.execute('SELECT id, plan_name, file_limit, days, price FROM premium_plans')
        for row in c.fetchall():
            premium_plans.append({
                "id": row[0],
                "plan_name": row[1] or "Basic",
                "file_limit": row[2],
                "days": row[3],
                "price": row[4]
            })
            if row[0] >= plan_id_counter:
                plan_id_counter = row[0] + 1

        c.execute('SELECT user_id, plan_id, expiry, file_limit FROM user_premium')
        for row in c.fetchall():
            try:
                user_premium_plans[row[0]] = {
                    "plan_id": row[1],
                    "expiry": datetime.fromisoformat(row[2]),
                    "file_limit": row[3]
                }
            except ValueError:
                logger.warning(f"⚠️ Invalid expiry date for user {row[0]}")

        c.execute('SELECT plan_id, name, file_limit, price, duration, buy_link FROM plans')
        for row in c.fetchall():
            binance_plans.append({
                "id": row[0],
                "name": row[1],
                "file_limit": row[2],
                "price": row[3],
                "duration": row[4],
                "buy_link": row[5]
            })

        conn.close()
        logger.info(f"Data loaded: {len(active_users)} users, {len(user_subscriptions)} subscriptions, {len(admin_ids)} admins.")
        logger.info(f"Free user limit: {FREE_USER_LIMIT_SETTINGS['limit']} files per {FREE_USER_LIMIT_SETTINGS['time']} hours")
        logger.info(f"Free user host time: {FREE_USER_LIMIT_SETTINGS['host_time']} hours")
        logger.info(f"Premium plans: {len(premium_plans)}")
        logger.info(f"Binance plans: {len(binance_plans)}")
        logger.info(f"Banned users: {len(banned_users)}")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}", exc_info=True)

# --- Premium Plan Variables ---
premium_plans = []
user_premium_plans = {}
plan_id_counter = 1
binance_plans = []

# Startup initialization is performed after all storage functions have been
# defined, so Google Sheets can be restored before the in-memory cache is
# projected into the bot's runtime collections.
# --- End Database Setup ---

# --- OTP GURU Bot Database Functions ---
def normalize_txid(tx_id):
    """Normalize transaction IDs for reliable duplicate matching."""
    # Transaction IDs are compared case-insensitively and surrounding
    # whitespace is ignored.  Do not remove characters from the middle:
    # changing an ID could accidentally make two different IDs identical.
    return str(tx_id or "").strip().casefold()


def get_txid_status(tx_id):
    """Return the current lifecycle state of a transaction ID.

    ``pending`` and ``approved`` are real deposit records.  ``used`` covers
    legacy Binance records stored in ``used_txids``.  A rejected request is
    deliberately not treated as a used transaction: an admin may reject a
    typo and the user must be able to submit a corrected request without
    being banned.
    """
    normalized = normalize_txid(tx_id)
    if not normalized:
        return None

    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """SELECT status FROM deposits_new
               WHERE LOWER(TRIM(trx_id)) = ?
               ORDER BY CASE status
                   WHEN 'approved' THEN 1
                   WHEN 'pending' THEN 2
                   WHEN 'rejected' THEN 3
                   ELSE 4
               END
               LIMIT 1""",
            (normalized,)
        )
        row = c.fetchone()
        if row and row[0] in ("pending", "approved"):
            conn.close()
            return row[0]

        c.execute(
            "SELECT 1 FROM used_txids WHERE LOWER(TRIM(tx_id)) = ? LIMIT 1",
            (normalized,)
        )
        used = c.fetchone() is not None
        conn.close()
        return "used" if used else (row[0] if row else None)
    except Exception as e:
        logger.error(f"Error checking transaction status for {normalized}: {e}")
        return None

def get_unique_admin_ids():
    """Return admin IDs without duplicates, preserving their order."""
    return list(dict.fromkeys(
        [uid for uid in ([OWNER_ID] + list(admin_list) + list(admin_ids))
         if uid is not None]
    ))

def is_user_banned(user_id):
    """Check both the in-memory and persistent ban state."""
    try:
        if user_id in banned_users:
            return True
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
        result = c.fetchone() is not None
        conn.close()
        if result and user_id not in banned_users:
            banned_users.append(user_id)
        return result
    except Exception as e:
        logger.error(f"Error checking ban status for {user_id}: {e}")
        return user_id in banned_users

def clear_pending_upload_state(user_id):
    """Remove an unfinished upload and its temporary files."""
    state = pending_upload_modes.pop(user_id, None)
    if not state:
        return
    pending_dir = state.get("pending_dir")
    if pending_dir and os.path.exists(pending_dir):
        try:
            shutil.rmtree(pending_dir)
        except Exception as e:
            logger.warning(f"Could not remove pending upload dir {pending_dir}: {e}")

def get_banned_notice_username(user_id):
    """Resolve a username/name without exposing the numeric Telegram ID."""
    try:
        chat = bot.get_chat(user_id)
        username = str(getattr(chat, "username", "") or "").strip()
        if username:
            return username if username.startswith("@") else f"@{username}"
        display_name = " ".join(
            part for part in (
                getattr(chat, "first_name", ""),
                getattr(chat, "last_name", ""),
            ) if str(part or "").strip()
        ).strip()
        if display_name:
            return display_name
    except Exception:
        pass

    # Use the locally stored profile when Telegram cannot return the chat.
    user_data = get_otp_user_data(user_id) if "get_otp_user_data" in globals() else None
    if user_data:
        username = str(user_data.get("username", "") or "").strip()
        if username and username.lower() not in ("@unknown", "unknown"):
            return username if username.startswith("@") else f"@{username}"
        name = str(user_data.get("name", "") or "").strip()
        if name:
            return name
    return "Unknown"


def send_banned_user_notice(chat_id, user_id, admin_id=None):
    """Tell a banned user that only Support remains available."""
    admin_id = admin_id or OWNER_ID
    user_name = get_banned_notice_username(user_id)
    admin_name = get_banned_notice_username(admin_id)
    try:
        bot.send_message(
            chat_id,
            render_body_text(
                f"⛔ *You are banned from this bot!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *Your Username:* `{user_name}`\n"
                f"👤 *Admin Username:* `{admin_name}`\n\n"
                f"🚫 *আপনি কোনো command, button বা file ব্যবহার করতে পারবেন না।*\n"
                f"💬 *শুধু Support button ব্যবহার করে Admin-এর সাথে যোগাযোগ করুন।*"
            ),
            reply_markup=create_banned_support_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to notify banned user {user_id}: {e}")

def stop_all_user_files(user_id):
    """Stop every running file owned by a banned user."""
    for file_name, _file_type in list(user_files.get(user_id, [])):
        try:
            stop_user_file(user_id, file_name)
        except Exception as e:
            logger.error(f"Failed stopping {file_name} for banned user {user_id}: {e}")

def ban_user(user_id, reason="ম্যানুয়ালি ব্যান করা হয়েছে", banned_by=None,
             transaction_id="", notify=True):
    """Persist a ban, stop files, and notify the user and admins."""
    if banned_by is None:
        banned_by = OWNER_ID
    normalized_txid = normalize_txid(transaction_id) if transaction_id else ""
    already_banned = is_user_banned(user_id)
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute(
                """INSERT OR IGNORE INTO banned_users
                   (user_id, reason, banned_by, transaction_id)
                   VALUES (?, ?, ?, ?)""",
                (user_id, reason, banned_by, normalized_txid)
            )
            conn.commit()
            conn.close()
        if user_id not in banned_users:
            banned_users.append(user_id)
    except Exception as e:
        logger.error(f"Failed to persist ban for {user_id}: {e}", exc_info=True)
        return False

    # A user may be in the middle of amount/transaction/admin input.  Clear
    # that pending flow so it cannot bypass the first message handler.
    try:
        bot.clear_step_handler_by_chat_id(user_id)
    except Exception as e:
        logger.warning(f"Could not clear step handler for banned user {user_id}: {e}")

    clear_pending_upload_state(user_id)
    stop_all_user_files(user_id)

    if notify and not already_banned:
        send_banned_user_notice(user_id, user_id, banned_by)
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton(
                "🔓 UNBAN USER",
                callback_data=f"unban_user_{user_id}"
            )
        )
        for admin_id in get_unique_admin_ids():
            try:
                bot.send_message(
                    admin_id,
                    render_body_text(
                        f"🔔 *USER AUTO-BANNED*\n"
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"👤 *User ID:* `{user_id}`\n"
                        f"🧾 *Transaction ID:* `{normalized_txid or 'N/A'}`\n"
                        f"📌 *Reason:* {reason}\n"
                        f"👤 *Ban Admin ID:* `{banned_by}`\n\n"
                        f"⛔ *এই ইউজারের সব command, button ও file access বন্ধ করা হয়েছে।*"
                    ),
                    reply_markup=admin_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed ban notification to admin {admin_id}: {e}")
    return True

def unban_user(user_id, unbanned_by=None, notify=True):
    """Remove a persistent ban and notify the user."""
    if unbanned_by is None:
        unbanned_by = OWNER_ID
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
            changed = c.rowcount > 0
            conn.commit()
            conn.close()
        if user_id in banned_users:
            banned_users.remove(user_id)
        if changed and notify:
            try:
                bot.send_message(
                    user_id,
                    render_body_text(
                        f"✅ *আপনাকে আনবান করা হয়েছে!*\n"
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"🆔 *User ID:* `{user_id}`\n"
                        f"👤 *Unban Admin ID:* `{unbanned_by}`\n\n"
                        f"🎉 এখন আপনি আবার বটের command ও button ব্যবহার করতে পারবেন।"
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed notifying unbanned user {user_id}: {e}")
        return changed
    except Exception as e:
        logger.error(f"Failed to unban {user_id}: {e}", exc_info=True)
        return False

def add_otp_user(user_id, name, username):
    """Add user to OTP GURU bot"""
    normalized_name = str(name or "Unknown").strip() or "Unknown"
    normalized_username = str(username or "").strip()
    if normalized_username and not normalized_username.startswith("@"):
        normalized_username = f"@{normalized_username}"
    normalized_username = normalized_username or "@unknown"
    joined_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    user_exists = False
    for u in all_users:
        if u["id"] == user_id:
            user_exists = True
            # Refresh the profile when Telegram provides a newer name or
            # username, while preserving the original join timestamp.
            u["name"] = normalized_name
            u["username"] = normalized_username
            break
    
    if not user_exists:
        new_user = {
            "id": user_id,
            "name": normalized_name,
            "username": normalized_username,
            "joined": joined_at,
            "balance": 0,
            "files_count": 0
        }
        all_users.append(new_user)
        logger.info(f"✅ New OTP user added: {name} ({user_id})")

    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.execute(
            """INSERT INTO user_profiles (user_id, name, username, joined_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   name = excluded.name,
                   username = excluded.username""",
            (
                user_id,
                normalized_name,
                normalized_username,
                next(
                    (
                        item.get("joined", "")
                        for item in all_users
                        if item.get("id") == user_id
                    ),
                    joined_at,
                ),
            ),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        logger.warning("Could not persist user profile %s: %s", user_id, exc)
    return not user_exists

def get_otp_user_data(user_id):
    """Get user data from OTP GURU bot"""
    for user in all_users:
        if user["id"] == user_id:
            return user
    return None

# ==================== GET/SET FUNCTIONS ====================

def get_setting(key):
    """Get setting from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        res = c.fetchone()
        conn.close()
        return res[0] if res else ""
    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return ""

def set_setting(key, value):
    """Set setting in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")
        return False


# ==========================================
# ✅ LIVE BOT BUTTON / REPLY EMOJI SETTINGS
# ==========================================
def _emoji_setting_key(scope, label):
    """Return a compact, stable settings key for a Unicode label."""
    digest = hashlib.sha256(str(label).encode('utf-8')).hexdigest()[:32]
    return f"emoji_override:{scope}:{digest}"


def _clean_emoji_id(value):
    """Accept Telegram custom emoji IDs, which are numeric strings."""
    value = str(value or "").strip()
    if value.isdigit() and 1 <= len(value) <= 40:
        return value
    return ""


def _get_emoji_override(scope, label, default_id):
    stored = _clean_emoji_id(get_setting(_emoji_setting_key(scope, label)))
    return stored or str(default_id or "")


def get_button_emoji_id(button_text, default_id):
    """Read a button emoji override without changing the original layout."""
    return _get_emoji_override("button", button_text, default_id)


def get_update_channel_button_emoji_id(default_id=EMOJI_UPDATE_CHANNEL_USER):
    """Use one configured Premium Emoji for every Update Channel button."""
    for label in (
        "𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇",
        "𝙐𝙋𝘿𝘼𝙏𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇",
    ):
        stored = _clean_emoji_id(
            get_setting(_emoji_setting_key("button", label))
        )
        if stored:
            return stored
    return str(default_id or "")


def get_body_emoji_id(normal_emoji, default_id):
    """Read a reply/body emoji override without changing existing messages."""
    return _get_emoji_override("body", normal_emoji, default_id)


def make_keyboard_button(text, default_id="", style="primary", use_override=True):
    """Create a reply button using the selected Premium Emoji ID."""
    original_text = str(text)
    text = strip_normal_emojis(original_text)
    if _is_channel_join_button(original_text):
        # Channel buttons are deliberately not editable: changing the
        # configured channel name must never change their custom emoji.
        emoji_id = EMOJI_ALL_CHANNEL_BUTTON
    elif use_override and _is_update_channel_label(original_text):
        emoji_id = get_update_channel_button_emoji_id(
            default_id or EMOJI_UPDATE_CHANNEL_USER
        )
    else:
        emoji_id = (
            get_button_emoji_id(original_text, default_id or CUSTOM_EMOJI_ID)
            if use_override
            else str(default_id or CUSTOM_EMOJI_ID)
        )
    try:
        button = types.KeyboardButton(
            text=text,
            icon_custom_emoji_id=emoji_id,
            style=style
        )
        return _remember_premium_button(button, emoji_id, style)
    except TypeError:
        # Keep button behaviour on older pyTelegramBotAPI versions.  Newer
        # versions will include the live custom emoji and button colour.
        logger.warning(
            "KeyboardButton Premium Emoji fields are unavailable; "
            "upgrade pyTelegramBotAPI to 4.36+."
        )
        button = types.KeyboardButton(text=text)
        return _remember_premium_button(button, emoji_id, style)


EDITABLE_EXTRA_BUTTONS = [
    ("Deposit Methods", "bKash", EMOJI_BKASH),
    ("Deposit Methods", "Nagad", EMOJI_NAGAD),
    ("Deposit Methods", "Rocket", EMOJI_ROCKET),
    ("Deposit Methods", "Upay", EMOJI_UPAY),
    ("Deposit Methods", "Binance", EMOJI_BINANCE),
    ("Deposit Methods", "BACK TO MAIN", EMOJI_BACK),
    ("Delete Payment Method", "DELETE bKash", EMOJI_TRASH),
    ("Delete Payment Method", "DELETE Nagad", EMOJI_TRASH),
    ("Delete Payment Method", "DELETE Rocket", EMOJI_TRASH),
    ("Delete Payment Method", "DELETE Upay", EMOJI_TRASH),
    ("Delete Payment Method", "DELETE Binance", EMOJI_TRASH),
    ("Force Join", "Add Channel", EMOJI_PLUS),
    ("Force Join", "Force Join চালু", EMOJI_LOCK),
    ("Force Join", "Force Join বন্ধ", EMOJI_UNLOCK),
    ("Force Join", "Admin Bypass: ON", EMOJI_SHIELD),
    ("Force Join", "Admin Bypass: OFF", EMOJI_SHIELD),
    ("Force Join", "Back", EMOJI_BACK),
    ("Broadcast", "Single User", EMOJI_USER_ICON),
    ("Broadcast", "All Users", EMOJI_MEGAPHONE),
    ("Broadcast", "Back", EMOJI_BACK),
    ("Link Setup", "Admin Link", EMOJI_PIN),
    ("Link Setup", "Support Link", EMOJI_PIN),
    ("Link Setup", "Channel Link", EMOJI_PIN),
        ("Link Setup", "Update Channel Link", EMOJI_PIN),
    ("Link Setup", "Owner Link", EMOJI_PIN),
    ("Link Setup", "Group Link", EMOJI_PIN),
    ("Link Setup", "USDT → BDT Rate", EMOJI_DOLLAR),
    ("Link Setup", "Back", EMOJI_BACK),
]


def get_editable_button_specs():
    """Collect every reply-keyboard button used by this bot."""
    layouts = [
        ("User Main Menu", COMMAND_BUTTONS_LAYOUT_USER_SPEC),
        ("Admin Main Menu", ADMIN_COMMAND_BUTTONS_LAYOUT_USER_SPEC),
        ("Referral User Menu", COMMAND_BUTTONS_LAYOUT_USER_SPEC),
        ("Referral Admin Menu", REFERRAL_ADMIN_BUTTONS),
        ("Free Host Plan Menu", FREE_HOST_PLAN_ADMIN_BUTTONS),
        ("Upload Module Mode", UPLOAD_MODE_BUTTONS),
        ("User OTP Menu", OTP_USER_BUTTONS),
        ("GX Admin Panel", OTP_ADMIN_BUTTONS),
        ("Ban/Unban Menu", OTP_BAN_BUTTONS),
        ("Deposite Menu", OTP_DEPOSITE_BUTTONS),
        ("Premium Plan Menu", PREMIUM_PLAN_ADMIN_BUTTONS),
        ("Premium User Menu", PREMIUM_PLAN_USER_BUTTONS),
        ("Admin Panel Menu", ADMIN_PANEL_BUTTONS),
    ]
    specs = []
    seen = set()
    for category, layout in layouts:
        for row in layout:
            for button in row:
                label = str(button.get("text", "")).strip()
                if not label or label in seen:
                    continue
                seen.add(label)
                default_id = button.get("icon_custom_emoji_id", CUSTOM_EMOJI_ID)
                specs.append({
                    "label": label,
                    "category": category,
                    "default_id": str(default_id or ""),
                    "current_id": get_button_emoji_id(label, default_id),
                })
    for category, label, default_id in EDITABLE_EXTRA_BUTTONS:
        label = str(label).strip()
        if not label or label in seen:
            continue
        seen.add(label)
        specs.append({
            "label": label,
            "category": category,
            "default_id": str(default_id or ""),
            "current_id": get_button_emoji_id(label, default_id),
        })
    return specs


def get_editable_body_emoji_specs():
    """Collect every normal emoji converted in outgoing reply messages."""
    return [
        {
            "label": emoji,
            "default_id": str(emoji_id or ""),
            "current_id": get_body_emoji_id(emoji, emoji_id),
        }
        for emoji, emoji_id in GLOBAL_BODY_EMOJIS.items()
    ]

# ==========================================
# ✅ CENTRALIZED LINK / RATE SETTINGS
# ==========================================
def get_link(key):
    """Return a configurable link, falling back to the built-in default."""
    value = (get_setting(key) or "").strip()
    return value or DEFAULT_LINKS.get(key, "")


def set_link(key, value):
    """Store a configurable link after validating it."""
    value = (value or "").strip()
    if not is_valid_link(value):
        return False
    return set_setting(key, value)


def is_valid_link(value):
    """Accept only http(s) links or @usernames."""
    value = (value or "").strip()
    if not value or len(value) > 512 or ' ' in value:
        return False
    if value.startswith('@'):
        return bool(re.fullmatch(r'@[A-Za-z0-9_]{4,32}', value))
    return bool(re.match(r'^https?://[^\s]+$', value))


def normalize_link(value):
    """Convert an @username into a full t.me link."""
    value = (value or "").strip()
    if value.startswith('@'):
        return f"https://t.me/{value.lstrip('@')}"
    return value


def get_usdt_rate():
    """Current USDT -> BDT conversion rate (always a positive number)."""
    raw = get_setting('usdt_rate')
    try:
        rate = float(str(raw).strip())
        if rate > 0:
            return rate
    except (TypeError, ValueError):
        pass
    return float(USDT_BDT_RATE)


def set_usdt_rate(value):
    """Persist a new USDT -> BDT rate."""
    try:
        rate = float(str(value).strip())
    except (TypeError, ValueError):
        return False, "শুধু সংখ্যা লিখুন (উদাহরণ: 120)"
    if rate <= 0 or rate > 100000:
        return False, "রেট অবশ্যই 0 এর বেশি এবং 100000 এর কম হতে হবে"
    rate = round(rate, 4)
    if not set_setting('usdt_rate', str(rate)):
        return False, "ডাটাবেজে সেভ করা যায়নি"
    return True, rate


def usdt_to_bdt(amount_usdt, rate=None):
    """Convert USDT to BDT with 2-decimal precision (no float drift)."""
    if rate is None:
        rate = get_usdt_rate()
    try:
        converted = Decimal(str(amount_usdt)) * Decimal(str(rate))
    except (InvalidOperation, TypeError, ValueError):
        return 0.0
    return float(converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# ==========================================
# ✅ FORCE JOIN - DATABASE LAYER
# ==========================================
def parse_force_join_input(text):
    """Parse 'Button Name / Channel URL [/ -100xxxxxxxxxx]' admin input."""
    raw = (text or "").strip()
    if '/' not in raw:
        return None, ("ফরম্যাট ভুল!\n"
                      "উদাহরণ: Join Channel / https://t.me/example")

    name_part, _, rest = raw.partition('/')
    button_name = name_part.strip()
    rest = rest.strip()

    # An optional numeric chat id may follow the link, which is the only way
    # to use a private channel that has no public username.
    chat_id = None
    tokens = [t for t in re.split(r'[\s/]+', rest) if t]
    if tokens and re.fullmatch(r'-100\d{5,}', tokens[-1]):
        chat_id = int(tokens[-1])
        rest = rest[:rest.rfind(tokens[-1])].strip().rstrip('/').strip()

    channel_url = normalize_link(rest)

    if not button_name:
        return None, "Button Name খালি রাখা যাবে না"
    if len(button_name) > 40:
        return None, "Button Name সর্বোচ্চ 40 অক্ষর হতে পারে"
    if not is_valid_link(channel_url):
        return None, ("Channel URL সঠিক নয়!\n"
                      "উদাহরণ: Join Channel / https://t.me/example")

    return {
        "button_name": button_name,
        "channel_url": channel_url,
        "chat_ref": extract_chat_ref(channel_url),
        "chat_id": chat_id,
    }, None


def extract_chat_ref(channel_url):
    """Return the @username used for membership checks, '' for invite links."""
    url = (channel_url or "").strip()
    match = re.match(r'^https?://(?:www\.)?t\.me/(?:s/)?([A-Za-z0-9_]{4,32})/?$', url)
    if match:
        return f"@{match.group(1)}"
    if url.startswith('@'):
        return url
    return ""


def get_bot_id():
    """Cached bot user id, used to check the bot's own admin rights."""
    global _BOT_USER_ID
    if _BOT_USER_ID is None:
        try:
            _BOT_USER_ID = bot.get_me().id
        except Exception as e:
            logger.error(f"Cannot read bot id: {e}")
    return _BOT_USER_ID


_BOT_USER_ID = None
ADMIN_STATUSES = ('administrator', 'creator')


def resolve_force_channel(chat_ref, chat_id=None):
    """Resolve a channel and make sure the bot can verify members there.

    Returns (info_dict, error_text).  Verification is impossible unless the
    bot itself is an administrator of the channel, so this is checked while
    the admin is adding the channel instead of silently failing later.
    """
    target = chat_id if chat_id is not None else chat_ref
    if not target:
        return None, ("এই channel-এর public username নেই।\n"
                      "Private channel হলে শেষে channel ID দিন:\n"
                      "Join Channel / https://t.me/+abc123 / -1001234567890")

    try:
        chat = bot.get_chat(target)
    except Exception as e:
        logger.warning(f"Force join resolve failed for {target}: {e}")
        return None, ("Channel টি পাওয়া যায়নি!\n"
                      "🤖 প্রথমে বটকে ওই channel-এ Admin বানান, তারপর আবার চেষ্টা করুন।")

    bot_id = get_bot_id()
    if not bot_id:
        return None, "বটের তথ্য পাওয়া যায়নি, একটু পরে আবার চেষ্টা করুন।"

    try:
        me = bot.get_chat_member(chat.id, bot_id)
    except Exception as e:
        logger.warning(f"Force join admin check failed for {chat.id}: {e}")
        return None, ("🤖 বট ওই channel-এ Admin নয়!\n"
                      "প্রথমে বটকে Admin বানান, তারপর channel টি add করুন।")

    if getattr(me, 'status', '') not in ADMIN_STATUSES:
        return None, ("🤖 বট ওই channel-এ Admin নয়!\n"
                      "প্রথমে বটকে Admin বানান, তারপর channel টি add করুন।")

    return {
        "chat_id": chat.id,
        "title": getattr(chat, 'title', '') or '',
        "chat_ref": f"@{chat.username}" if getattr(chat, 'username', None) else "",
    }, None


def add_force_channel(button_name, channel_url, chat_ref, chat_id=None):
    """Insert a new force-join channel."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT id FROM force_join_channels WHERE LOWER(channel_url) = ? OR (chat_id IS NOT NULL AND chat_id = ?)",
            (channel_url.lower(), chat_id)
        )
        if c.fetchone():
            conn.close()
            return None, "এই channel আগেই যোগ করা আছে"
        c.execute(
            "INSERT INTO force_join_channels (button_name, channel_url, chat_ref, chat_id) VALUES (?, ?, ?, ?)",
            (button_name, channel_url, chat_ref, chat_id)
        )
        channel_id = c.lastrowid
        conn.commit()
        conn.close()
        return channel_id, None
    except Exception as e:
        logger.error(f"Error adding force join channel: {e}")
        return None, "ডাটাবেজ এরর"


def update_force_channel(channel_id, button_name, channel_url, chat_ref, chat_id=None):
    """Update an existing force-join channel."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """UPDATE force_join_channels
               SET button_name = ?, channel_url = ?, chat_ref = ?, chat_id = ?
               WHERE id = ?""",
            (button_name, channel_url, chat_ref, chat_id, channel_id)
        )
        updated = c.rowcount
        conn.commit()
        conn.close()
        return updated > 0
    except Exception as e:
        logger.error(f"Error updating force join channel {channel_id}: {e}")
        return False


def delete_force_channel(channel_id):
    """Delete a force-join channel."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("DELETE FROM force_join_channels WHERE id = ?", (channel_id,))
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return deleted > 0
    except Exception as e:
        logger.error(f"Error deleting force join channel {channel_id}: {e}")
        return False


def get_force_channels():
    """Return every configured force-join channel."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT id, button_name, channel_url, chat_ref, chat_id FROM force_join_channels ORDER BY id"
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": r[0],
                "button_name": r[1],
                "channel_url": r[2],
                "chat_ref": r[3] or "",
                "chat_id": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Error loading force join channels: {e}")
        return []


def get_force_channel(channel_id):
    """Return a single force-join channel or None."""
    for channel in get_force_channels():
        if channel["id"] == channel_id:
            return channel
    return None


# ==========================================
# ✅ FORCE JOIN - MEMBERSHIP CHECK
# ==========================================
JOINED_STATUSES = ('member', 'administrator', 'creator')
FORCE_JOIN_CACHE_SECONDS = 300
_force_join_cache = {}
_force_join_cache_lock = threading.Lock()
_force_join_alerts = {}


def is_force_join_enabled():
    """Force join can be switched off from the admin panel."""
    return (get_setting('force_join_enabled') or '1').strip() != '0'


def set_force_join_enabled(enabled):
    ok = set_setting('force_join_enabled', '1' if enabled else '0')
    clear_force_join_cache()
    return ok


def is_admin_bypass_enabled():
    """Admin/owner bypass can be switched off (useful for testing)."""
    return (get_setting('force_join_admin_bypass') or '1').strip() != '0'


def set_admin_bypass_enabled(enabled):
    ok = set_setting('force_join_admin_bypass', '1' if enabled else '0')
    clear_force_join_cache()
    return ok


def is_bot_admin_user(user_id):
    return user_id == OWNER_ID or user_id in admin_ids or user_id in admin_list


def force_join_exempt(user_id):
    """Admins and the owner skip force join unless bypass is switched off."""
    return is_bot_admin_user(user_id) and is_admin_bypass_enabled()


def alert_owner_force_join_issue(channel, error):
    """Tell the owner when a channel cannot be verified (max once an hour)."""
    key = channel.get('id')
    now = time.time()
    if _force_join_alerts.get(key, 0) > now:
        return
    _force_join_alerts[key] = now + 3600
    try:
        bot.send_message(
            OWNER_ID,
            render_body_text(
                f"🔔 *Force Join Alert*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🔘 Channel: {channel.get('button_name')}\n"
                f"🔗 {channel.get('channel_url')}\n"
                f"⚠️ বট সম্ভবত ওই channel-এ Admin নেই।\n"
                f"💡 ঠিক না করা পর্যন্ত ইউজাররা bot ব্যবহার করতে পারবে না।\n\n"
                f"🧾 {error}"
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Could not alert owner about force join issue: {e}")


def is_user_in_channel(channel, user_id):
    """True only when the membership check succeeds and the user is inside.

    Any failure returns False (fail closed), so the requirement can never be
    bypassed by a deleted channel or a temporary API error.
    """
    target = channel.get('chat_id') or channel.get('chat_ref')
    if not target:
        alert_owner_force_join_issue(channel, "Channel ID/username নেই")
        return False
    try:
        member = bot.get_chat_member(target, user_id)
    except telebot.apihelper.ApiTelegramException as e:
        description = str(e).lower()
        if 'user not found' in description or 'participant' in description:
            return False
        logger.warning(f"Force join check failed for {target}: {e}")
        alert_owner_force_join_issue(channel, str(e))
        return False
    except Exception as e:
        logger.warning(f"Force join check error for {target}: {e}")
        alert_owner_force_join_issue(channel, str(e))
        return False

    status = getattr(member, 'status', '') or ''
    if status in JOINED_STATUSES:
        return True
    if status == 'restricted' and getattr(member, 'is_member', False):
        return True
    return False


def get_missing_force_channels(user_id, use_cache=True):
    """Return the channels the user still has to join."""
    if not is_force_join_enabled() or force_join_exempt(user_id):
        return []

    channels = get_force_channels()
    if not channels:
        return []

    if use_cache:
        with _force_join_cache_lock:
            expires = _force_join_cache.get(user_id, 0)
        if expires > time.time():
            return []

    missing = [ch for ch in channels if not is_user_in_channel(ch, user_id)]

    if missing:
        clear_force_join_cache(user_id)
    else:
        with _force_join_cache_lock:
            _force_join_cache[user_id] = time.time() + FORCE_JOIN_CACHE_SECONDS
    return missing


def clear_force_join_cache(user_id=None):
    """Drop cached membership results."""
    with _force_join_cache_lock:
        if user_id is None:
            _force_join_cache.clear()
        else:
            _force_join_cache.pop(user_id, None)


def build_force_join_markup(channels):
    """Join buttons plus the verify button."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        markup.add(
            types.InlineKeyboardButton(
                f"📢 {channel['button_name']}",
                url=channel["channel_url"],
                icon_custom_emoji_id=EMOJI_ALL_CHANNEL_BUTTON,
                style="primary"  # 🔵 নীল
            )
        )
    markup.add(
        types.InlineKeyboardButton(
            "✅ Verify / আমি জয়েন করেছি",
            callback_data='fj_verify',
            icon_custom_emoji_id=EMOJI_VERIFY_BUTTON,
            style="success"  # 🟢 সবুজ
        )
    )
    return markup


def build_force_join_text(channels, user_name=None):
    """The message shown to a user who has not joined yet."""
    greeting = (
        f"👋 হ্যালো {keep_user_name_emojis_normal(user_name)}!\n\n"
        if user_name else ""
    )
    total_required = len(get_force_channels()) or len(channels)
    lines = "\n".join(
        f"{i}. 📢 {ch['button_name']}" for i, ch in enumerate(channels, 1)
    )
    return (
        f"{bot_emoji_tag()} বট অ্যাক্সেস লকড {lock_emoji_tag()}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"{greeting}"
        f"📌 বট ব্যবহার করতে মোট {total_required}টি channel-এই join করা বাধ্যতামূলক।\n"
        f"⚠️ যেকোনো একটি channel-এ join না থাকলেও access বন্ধ থাকবে।\n\n"
        f"📋 এখনো যেগুলোতে join করা বাকি:\n"
        f"{lines}\n\n"
        f"✅ সব channel-এ join করার পর Verify চাপুন।\n"
        f"🔄 Verify সফল না হওয়া পর্যন্ত bot-এর কোনো feature ব্যবহার করা যাবে না।"
    )


def send_force_join_prompt(chat_id, channels, user_name=None):
    """Show the join requirement to the user."""
    if not channels:
        return
    try:
        bot.send_message(
            chat_id,
            render_body_text(build_force_join_text(channels, user_name)),
            reply_markup=build_force_join_markup(channels),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Failed to send force join prompt to {chat_id}: {e}")


def force_join_blocked(user_id):
    """True when the user must join channels before using the bot."""
    try:
        if force_join_exempt(user_id):
            return False
        # This is the security boundary.  Do not use the positive-result
        # cache here: a user may leave a channel after a previous successful
        # check, and must be blocked on the next bot interaction.
        return bool(get_missing_force_channels(user_id, use_cache=False))
    except Exception as e:
        logger.error(f"Force join gate error for {user_id}: {e}")
        # Fail closed: a bug here must not open a bypass.
        return bool(get_force_channels()) and is_force_join_enabled()


def get_file_forward_group():
    """Get file forward group ID from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT group_id FROM file_forward_group WHERE id = 1")
        res = c.fetchone()
        conn.close()
        return res[0] if res else ""
    except Exception as e:
        logger.error(f"Error getting file forward group: {e}")
        return ""

def set_file_forward_group(group_id):
    """Set file forward group ID in database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO file_forward_group (id, group_id) VALUES (1, ?)", (group_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error setting file forward group: {e}")
        return False

def get_user_balance_db(user_id):
    """Get user balance from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT balance FROM user_balances WHERE user_id = ?", (user_id,))
        res = c.fetchone()
        conn.close()
        return res[0] if res else 0.0
    except Exception as e:
        logger.error(f"Error getting balance for {user_id}: {e}")
        return 0.0

def update_user_balance_db(user_id, amount):
    """Update user balance"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO user_balances (user_id, balance) VALUES (?, COALESCE((SELECT balance FROM user_balances WHERE user_id = ?), 0) + ?)",
                  (user_id, user_id, amount))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating balance for {user_id}: {e}")
        return False

def credit_binance_deposit(user_id, amount_usdt, trx_id, rate):
    """Disabled legacy path; Binance is credited only by admin approval.

    Kept as a compatibility shim for old deployments that may still import
    the function.  It must never auto-credit a Binance transaction.
    """
    logger.warning("Blocked legacy automatic Binance credit path")
    return False, 0.0

def get_payment_methods():
    """Get all payment methods - DUPLICATE REMOVED"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT name, number_or_address, min_deposit, icon_key FROM payment_methods")
        methods = c.fetchall()
        conn.close()
        
        # Remove duplicates
        unique_methods = {}
        for m in methods:
            name_lower = m[0].lower()
            if name_lower not in unique_methods:
                unique_methods[name_lower] = {"name": m[0], "number": m[1], "min_deposit": m[2], "icon": m[3]}
        
        return list(unique_methods.values())
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        return []

def get_payment_method(name):
    """Get payment method by name"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """SELECT name, number_or_address, min_deposit
               FROM payment_methods
               WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
                  OR LOWER(name) LIKE '%' || LOWER(TRIM(?)) || '%'
               ORDER BY CASE
                   WHEN LOWER(TRIM(name)) = LOWER(TRIM(?)) THEN 0
                   ELSE 1
               END
               LIMIT 1""",
            (name, name, name)
        )
        res = c.fetchone()
        conn.close()
        if res:
            return {"name": res[0], "number": res[1], "min_deposit": res[2]}
        return None
    except Exception as e:
        logger.error(f"Error getting payment method {name}: {e}")
        return None

def create_deposit_request(user_id, amount, method, trx_id):
    """Create a new deposit request"""
    trx_id = normalize_txid(trx_id)
    if not trx_id:
        return None, "Transaction ID খালি রাখা যাবে না"

    # Serialize the check and insert.  Otherwise two users can submit the
    # same ID at the same moment and both can pass the pre-check.
    with DB_LOCK:
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("BEGIN IMMEDIATE")

            c.execute(
                "SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'",
                (user_id,)
            )
            if c.fetchone():
                conn.rollback()
                return None, "আপনার ইতিমধ্যে একটি pending ডিপোজিট রিকোয়েস্ট আছে! দয়া করে অ্যাডমিনের অ্যাপ্রুভের জন্য অপেক্ষা করুন।"

            # Rejected requests are intentionally excluded.  A typo rejected
            # by an admin must not become a permanent ban trigger.
            c.execute(
                """SELECT status FROM deposits_new
                   WHERE LOWER(TRIM(trx_id)) = ?
                     AND status IN ('pending', 'approved')
                   LIMIT 1""",
                (trx_id,)
            )
            if c.fetchone():
                conn.rollback()
                return None, "DUPLICATE_ACTIVE"

            c.execute(
                """INSERT INTO deposits_new
                   (user_id, amount, method, trx_id, status)
                   VALUES (?, ?, ?, ?, 'pending')""",
                (user_id, amount, method, trx_id)
            )
            deposit_id = c.lastrowid
            conn.commit()
            return deposit_id, None
        except sqlite3.IntegrityError:
            # Keep compatibility with the legacy UNIQUE(trx_id) constraint.
            # A collision is a ban-worthy duplicate only when the old record
            # is still active or was already approved.
            if conn:
                conn.rollback()
                try:
                    c.execute(
                        """SELECT status FROM deposits_new
                           WHERE LOWER(TRIM(trx_id)) = ?
                           LIMIT 1""",
                        (trx_id,)
                    )
                    row = c.fetchone()
                    if row and row[0] in ("pending", "approved"):
                        return None, "DUPLICATE_ACTIVE"
                except Exception:
                    pass
            return None, "Duplicate transaction ID"
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error creating deposit: {e}")
            return None, str(e)
        finally:
            if conn:
                conn.close()


def save_deposit_screenshot(deposit_id, screenshot_file_id):
    """Attach the Telegram photo only after the user submits a real photo."""
    if not deposit_id or not screenshot_file_id:
        return False
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE deposits_new SET screenshot_file_id = ? "
            "WHERE id = ? AND status = 'pending'",
            (str(screenshot_file_id), deposit_id)
        )
        updated = cursor.rowcount == 1
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        logger.error(f"Error saving deposit screenshot {deposit_id}: {e}")
        return False


def get_pending_deposits():
    """Get all pending deposits"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, user_id, amount, method, trx_id, created_at FROM deposits_new WHERE status = 'pending' ORDER BY created_at DESC")
        deposits = c.fetchall()
        conn.close()
        return deposits
    except Exception as e:
        logger.error(f"Error getting pending deposits: {e}")
        return []

def approve_deposit(deposit_id, admin_id):
    """Approve a deposit"""
    conn = None
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("BEGIN IMMEDIATE")

            c.execute(
                """SELECT user_id, amount, trx_id, method FROM deposits_new
                   WHERE id = ? AND status = 'pending'""",
                (deposit_id,)
            )
            dep = c.fetchone()
            if not dep:
                return False, "Deposit not found or already processed"

            user_id, amount, trx_id, method = dep
            # Binance deposits are submitted in USDT and credited in BDT.
            credit_amount = (
                usdt_to_bdt(amount) if (method or '').lower() == 'binance'
                else float(amount)
            )
            normalized = normalize_txid(trx_id)
            c.execute(
                "SELECT 1 FROM used_txids WHERE LOWER(TRIM(tx_id)) = ?",
                (normalized,)
            )
            if c.fetchone():
                return False, "Transaction ID already used"

            c.execute(
                """UPDATE deposits_new
                   SET status = 'approved', approved_by = ?, approved_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (admin_id, datetime.now(), deposit_id)
            )
            if c.rowcount != 1:
                return False, "Deposit was already processed"

            c.execute("INSERT INTO used_txids (tx_id) VALUES (?)", (normalized,))
            c.execute(
                """INSERT OR REPLACE INTO user_balances
                   (user_id, balance)
                   VALUES (?, COALESCE(
                       (SELECT balance FROM user_balances WHERE user_id = ?), 0
                   ) + ?)""",
                (user_id, user_id, credit_amount)
            )
            conn.commit()
            return True, credit_amount
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error approving deposit {deposit_id}: {e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()

def reject_deposit(deposit_id, admin_id):
    """Reject a deposit"""
    conn = None
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute(
                """UPDATE deposits_new
                   SET status = 'rejected', approved_by = ?, approved_at = ?
                   WHERE id = ? AND status = 'pending'""",
                (admin_id, datetime.now(), deposit_id)
            )
            if c.rowcount != 1:
                conn.rollback()
                return False
            conn.commit()
            return True
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error rejecting deposit {deposit_id}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def get_user_deposits(user_id):
    """Get all deposits for a user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id, amount, method, trx_id, status, created_at FROM deposits_new WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        deposits = c.fetchall()
        conn.close()
        return deposits
    except Exception as e:
        logger.error(f"Error getting user deposits: {e}")
        return []

def save_payment_method(name, number, min_deposit):
    """Save or update payment method"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        
        name_lower = name.lower()
        icon_key = 'card'
        if 'bkash' in name_lower:
            icon_key = 'bkash'
        elif 'nagad' in name_lower:
            icon_key = 'nagad'
        elif 'rocket' in name_lower:
            icon_key = 'rocket'
        elif 'upay' in name_lower:
            icon_key = 'upay'
        elif 'binance' in name_lower:
            icon_key = 'binance'
        
        c.execute("INSERT OR REPLACE INTO payment_methods (name, number_or_address, min_deposit, icon_key) VALUES (?, ?, ?, ?)",
                  (name, number, min_deposit, icon_key))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving payment method: {e}")
        return False

def delete_payment_method(name):
    """Delete payment method"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """DELETE FROM payment_methods
               WHERE LOWER(TRIM(name)) = LOWER(TRIM(?))
                  OR LOWER(name) LIKE '%' || LOWER(TRIM(?)) || '%'""",
            (name, name)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error deleting payment method: {e}")
        return False

# ==================== BINANCE PAY FUNCTIONS ====================

def parse_price_to_usdt(price_str):
    """Convert price to USDT"""
    price_clean = str(price_str).upper().strip()
    numbers = re.findall(r"[-+]?\d*\.\d+|\d+", price_clean)
    if not numbers:
        return 0.0, price_str

    val = float(numbers[0])
    if "BDT" in price_clean or "TAKA" in price_clean or "TK" in price_clean:
        usdt_val = round(val / get_usdt_rate(), 2)
        return usdt_val, f"{price_str} (~{usdt_val} USDT)"
    elif "USDT" in price_clean or "$" in price_clean or "USD" in price_clean:
        return round(val, 2), f"{val} USDT"
    else:
        return round(val, 2), f"{val} USDT"

def add_plan_db(name, file_limit, price, duration, buy_link):
    """Add a new Binance plan to database"""
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "INSERT INTO plans (name, file_limit, price, duration, buy_link) VALUES (?, ?, ?, ?, ?)",
            (name, file_limit, price, duration, buy_link),
        )
        conn.commit()
        conn.close()

def get_all_plans():
    """Get all Binance plans from database"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        "SELECT plan_id, name, file_limit, price, duration, buy_link FROM plans"
    )
    plans = c.fetchall()
    conn.close()
    return plans

def get_plan_by_id(plan_id):
    """Get a specific Binance plan by ID"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        "SELECT plan_id, name, file_limit, price, duration, buy_link FROM plans WHERE plan_id = ?",
        (plan_id,),
    )
    plan = c.fetchone()
    conn.close()
    return plan

def delete_plan_db(plan_id):
    """Delete a Binance plan from database"""
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("DELETE FROM plans WHERE plan_id = ?", (plan_id,))
        conn.commit()
        conn.close()

def get_pending_payment(user_id, plan_id):
    """Get pending payment amount for a user and plan"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        "SELECT paid_amount FROM pending_payments WHERE user_id=? AND plan_id=?",
        (user_id, plan_id),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0.0

def update_pending_payment(user_id, plan_id, amount):
    """Update pending payment amount"""
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO pending_payments (user_id, plan_id, paid_amount) VALUES (?, ?, ?)",
            (user_id, plan_id, amount),
        )
        conn.commit()
        conn.close()

def clear_pending_payment(user_id, plan_id):
    """Clear pending payment for a user and plan"""
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "DELETE FROM pending_payments WHERE user_id=? AND plan_id=?",
            (user_id, plan_id),
        )
        conn.commit()
        conn.close()

def is_txid_used(tx_id):
    """Check if a transaction ID has been used before"""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute(
        "SELECT tx_id FROM used_txids WHERE LOWER(TRIM(tx_id)) = ?",
        (normalize_txid(tx_id),)
    )
    row = c.fetchone()
    conn.close()
    return row is not None
def add_used_txid(tx_id):
    """Mark a transaction ID as used"""
    normalized = normalize_txid(tx_id)
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT 1 FROM used_txids WHERE LOWER(TRIM(tx_id)) = ?",
            (normalized,)
        )
        if c.fetchone():
            conn.close()
            return False
        c.execute("INSERT INTO used_txids (tx_id) VALUES (?)", (normalized,))
        conn.commit()
        conn.close()
        return True

def is_successful_txid_used(tx_id):
    """Check used_txids and already-approved deposits."""
    normalized = normalize_txid(tx_id)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """SELECT 1 FROM used_txids WHERE LOWER(TRIM(tx_id)) = ?
               UNION ALL
               SELECT 1 FROM deposits_new
               WHERE LOWER(TRIM(trx_id)) = ? AND status = 'approved'
               LIMIT 1""",
            (normalized, normalized)
        )
        used = c.fetchone() is not None
        conn.close()
        return used
    except Exception as e:
        logger.error(f"Error checking successful transaction {tx_id}: {e}")
        return False

def check_binance_payment(pay_order_id):
    """Disabled compatibility shim; Binance IDs are admin-reviewed manually."""
    return False, 0.0, "Binance automatic verification is disabled."

# ==================== END BINANCE PAY FUNCTIONS ====================

# --- Premium Plan Database Functions ---
def save_premium_plan(file_limit, days, price, plan_name="Basic"):
    """Save premium plan to database"""
    global plan_id_counter
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        
        c.execute('INSERT INTO premium_plans (plan_name, file_limit, days, price) VALUES (?, ?, ?, ?)',
                  (plan_name, file_limit, days, price))
        conn.commit()
        
        plan_id = c.lastrowid
        
        plan = {
            "id": plan_id,
            "plan_name": plan_name,
            "file_limit": file_limit,
            "days": days,
            "price": price
        }
        premium_plans.append(plan)
        
        if plan_id >= plan_id_counter:
            plan_id_counter = plan_id + 1
            
        conn.close()
        logger.info(f"✅ Premium plan added: {plan_name} - {file_limit} files, {days} days, {price} price (ID: {plan_id})")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving premium plan: {e}")
        return False

def remove_premium_plan(plan_id):
    """Remove premium plan from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM premium_plans WHERE id = ?', (plan_id,))
        conn.commit()
        conn.close()
        global premium_plans
        premium_plans = [p for p in premium_plans if p["id"] != plan_id]
        logger.info(f"✅ Premium plan removed: {plan_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Error removing premium plan: {e}")
        return False

def reset_all_plans():
    """Reset all premium plans"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM premium_plans')
        c.execute("DELETE FROM sqlite_sequence WHERE name='premium_plans'")
        conn.commit()
        conn.close()
        
        global premium_plans, plan_id_counter
        premium_plans = []
        plan_id_counter = 1
        
        logger.info(f"✅ All plans reset")
        return True
    except Exception as e:
        logger.error(f"❌ Error resetting plans: {e}")
        return False

def save_user_premium_plan(user_id, plan_id, expiry, file_limit):
    """Save user premium plan to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO user_premium (user_id, plan_id, expiry, file_limit) VALUES (?, ?, ?, ?)',
                  (user_id, plan_id, expiry.isoformat(), file_limit))
        conn.commit()
        conn.close()
        user_premium_plans[user_id] = {
            "plan_id": plan_id,
            "expiry": expiry,
            "file_limit": file_limit
        }
        logger.info(f"✅ User {user_id} premium plan activated")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving user premium plan: {e}")
        return False

def get_user_premium_plan(user_id):
    """Get the persisted Premium plan, falling back to the local cache."""
    cached = user_premium_plans.get(user_id)
    if cached:
        return cached
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT plan_id, expiry, file_limit FROM user_premium WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        plan = {
            "plan_id": row[0],
            "expiry": datetime.fromisoformat(row[1]),
            "file_limit": row[2],
        }
        user_premium_plans[user_id] = plan
        return plan
    except Exception as e:
        logger.error(f"Could not load Premium plan for user {user_id}: {e}")
        return cached


def get_active_premium_plan(user_id):
    """Return an unexpired persisted Premium plan, if one exists."""
    plan = get_user_premium_plan(user_id)
    if plan and plan.get("expiry") and plan["expiry"] > datetime.now():
        return plan
    return None

REFERRAL_BOT_USERNAME = None

def get_or_create_referral_code(user_id):
    """Return one permanent, unique deep-link code for each Telegram user."""
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT code FROM referral_codes WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row:
                conn.close()
                return row[0]
            for _ in range(5):
                code = "ref_" + secrets.token_urlsafe(9).replace("-", "").replace("_", "")
                try:
                    c.execute(
                        "INSERT INTO referral_codes (user_id, code) VALUES (?, ?)",
                        (user_id, code)
                    )
                    conn.commit()
                    conn.close()
                    return code
                except sqlite3.IntegrityError:
                    continue
            conn.close()
    except Exception as e:
        logger.error(f"Could not create referral code for {user_id}: {e}", exc_info=True)
    return ""

def get_referral_link(user_id):
    global REFERRAL_BOT_USERNAME
    try:
        if not REFERRAL_BOT_USERNAME:
            REFERRAL_BOT_USERNAME = bot.get_me().username
    except Exception as e:
        logger.warning(f"Could not resolve bot username for referral link: {e}")
    code = get_or_create_referral_code(user_id)
    if not code or not REFERRAL_BOT_USERNAME:
        return ""
    return f"https://t.me/{REFERRAL_BOT_USERNAME}?start={code}"

def get_referral_count(user_id):
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'verified'",
            (user_id,)
        )
        count = int(c.fetchone()[0] or 0)
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Could not read referral count for {user_id}: {e}")
        return 0

def get_claimed_free_host_plan_ids(user_id):
    """Return plans already redeemed by this user."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT plan_id FROM free_host_plan_claims WHERE user_id = ?",
            (user_id,)
        )
        claimed = {int(row[0]) for row in c.fetchall()}
        conn.close()
        return claimed
    except Exception as e:
        logger.error(f"Could not read claimed free host plans for {user_id}: {e}")
        return set()

def format_free_host_duration(host_hours):
    """Show a friendly day-based duration when the plan uses full days."""
    hours = int(host_hours)
    if hours % 24 == 0:
        days = hours // 24
        return f"{days} day" if days == 1 else f"{days} days"
    return f"{hours} hours"

def get_referral_bonus():
    try:
        return float(get_setting("referral_bonus") or 0)
    except (TypeError, ValueError):
        return 0.0

def get_free_host_plans():
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT id, plan_name, referral_target, host_hours, file_limit "
            "FROM free_host_plans ORDER BY id"
        )
        rows = c.fetchall()
        conn.close()
        return [
            {
                "id": row[0], "name": row[1], "target": int(row[2]),
                "host_hours": int(row[3]), "file_limit": int(row[4])
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Could not read free host plan: {e}")
        return []

def get_free_host_plan():
    plans = get_free_host_plans()
    return plans[0] if plans else None

def get_free_host_plan_by_id(plan_id):
    """Return one configured free-host plan by its admin-assigned ID."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT id, plan_name, referral_target, host_hours, file_limit "
            "FROM free_host_plans WHERE id = ?", (plan_id,)
        )
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row[0], "name": row[1], "target": int(row[2]),
            "host_hours": int(row[3]), "file_limit": int(row[4])
        }
    except Exception as e:
        logger.error(f"Could not read free host plan {plan_id}: {e}")
        return None

def activate_selected_free_host_plan(user_id, plan_id):
    """Claim one eligible free-host plan after the user selects its button."""
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute(
                "SELECT id, plan_name, referral_target, host_hours, file_limit "
                "FROM free_host_plans WHERE id = ?", (plan_id,)
            )
            row = c.fetchone()
            if not row:
                conn.close()
                return {"status": "not_found"}

            plan = {
                "id": row[0], "name": row[1], "target": int(row[2]),
                "host_hours": int(row[3]), "file_limit": int(row[4])
            }
            c.execute(
                "SELECT COUNT(*) FROM referrals "
                "WHERE referrer_id = ? AND status = 'verified'", (user_id,)
            )
            referral_count = int(c.fetchone()[0] or 0)

            if referral_count < plan["target"]:
                conn.close()
                return {
                    "status": "insufficient",
                    "plan": plan,
                    "count": referral_count
                }

            c.execute(
                "SELECT plan_id, plan_name, host_hours, file_limit, expiry "
                "FROM free_host_grants WHERE user_id = ?", (user_id,)
            )
            current = c.fetchone()
            if current:
                try:
                    current_expiry = datetime.fromisoformat(str(current[4]))
                    if current_expiry > datetime.now():
                        conn.close()
                        return {
                            "status": "active",
                            "plan_name": current[1],
                            "expiry": current_expiry
                        }
                except (TypeError, ValueError):
                    pass
                c.execute("DELETE FROM free_host_grants WHERE user_id = ?", (user_id,))

            c.execute(
                "SELECT 1 FROM free_host_plan_claims "
                "WHERE user_id = ? AND plan_id = ?", (user_id, plan_id)
            )
            if c.fetchone():
                conn.close()
                return {"status": "claimed", "plan": plan}

            expiry = datetime.now() + timedelta(hours=plan["host_hours"])
            c.execute(
                """INSERT INTO free_host_plan_claims (user_id, plan_id)
                   VALUES (?, ?)""",
                (user_id, plan_id)
            )
            c.execute(
                """INSERT OR REPLACE INTO free_host_grants
                   (user_id, plan_id, plan_name, host_hours, file_limit, expiry)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id, plan["id"], plan["name"], plan["host_hours"],
                    plan["file_limit"], expiry.isoformat()
                )
            )
            conn.commit()
            conn.close()
            return {
                "status": "activated",
                "plan": plan,
                "expiry": expiry
            }
    except sqlite3.IntegrityError:
        return {"status": "claimed", "plan": get_free_host_plan_by_id(plan_id)}
    except Exception as e:
        logger.error(
            f"Could not activate selected free host plan for {user_id}: {e}",
            exc_info=True
        )
        return {"status": "error"}

def get_active_free_host_grant(user_id):
    """Return an active grant and clean up an expired one."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "SELECT plan_id, plan_name, host_hours, file_limit, activated_at, expiry "
            "FROM free_host_grants WHERE user_id = ?", (user_id,)
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        expiry = datetime.fromisoformat(str(row[5]))
        if expiry <= datetime.now():
            c.execute("DELETE FROM free_host_grants WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return None
        conn.close()
        return {
            "plan_id": row[0], "plan_name": row[1], "host_hours": int(row[2]),
            "file_limit": int(row[3]), "activated_at": row[4], "expiry": expiry
        }
    except Exception as e:
        logger.error(f"Could not read free host grant for {user_id}: {e}")
        return None

def activate_free_host_if_eligible(user_id):
    """Activate a current grant when the configured referral target is met."""
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute(
                "SELECT id, plan_name, referral_target, host_hours, file_limit "
                "FROM free_host_plans ORDER BY id"
            )
            plans = c.fetchall()
            if not plans:
                conn.close()
                return None
            c.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? "
                "AND status = 'verified'", (user_id,)
            )
            count = int(c.fetchone()[0] or 0)
            plan = next((p for p in plans if count >= int(p[2])), None)
            if plan is None:
                conn.close()
                return None
            c.execute("SELECT expiry FROM free_host_grants WHERE user_id = ?", (user_id,))
            current = c.fetchone()
            if current:
                try:
                    current_expiry = datetime.fromisoformat(str(current[0]))
                    if current_expiry > datetime.now():
                        conn.close()
                        return {
                            "plan_name": plan[1], "host_hours": int(plan[3]),
                            "file_limit": int(plan[4]), "expiry": current_expiry,
                            "already_active": True
                        }
                except ValueError:
                    pass
                c.execute("DELETE FROM free_host_grants WHERE user_id = ?", (user_id,))
            expiry = datetime.now() + timedelta(hours=int(plan[3]))
            c.execute(
                """INSERT OR REPLACE INTO free_host_grants
                   (user_id, plan_id, plan_name, host_hours, file_limit, expiry)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, plan[0], plan[1], int(plan[3]), int(plan[4]), expiry.isoformat())
            )
            conn.commit()
            conn.close()
            return {
                "plan_name": plan[1], "host_hours": int(plan[3]),
                "file_limit": int(plan[4]), "expiry": expiry,
                "already_active": False
            }
    except Exception as e:
        logger.error(f"Could not activate free host for {user_id}: {e}", exc_info=True)
        return None

def add_referral_strike(user_id, reason):
    """Track hard Telegram-visible abuse signals."""
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT strike_count FROM referral_strikes WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            count = int(row[0] if row else 0) + 1
            c.execute(
                """INSERT OR REPLACE INTO referral_strikes
                   (user_id, strike_count, last_reason, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
                (user_id, count, reason)
            )
            conn.commit()
            conn.close()
            return count
    except Exception as e:
        logger.error(f"Could not add referral strike for {user_id}: {e}")
        return 0

def _notify_referral_admins(text):
    for admin_id in get_unique_admin_ids():
        try:
            bot.send_message(admin_id, render_body_text(text), parse_mode='HTML')
        except Exception as e:
            logger.warning(f"Referral admin notification failed for {admin_id}: {e}")

def register_referral_from_start(referred_id, referred_user, allow_new_user=True):
    """Register a unique /start deep-link referral and credit it atomically."""
    text = str(getattr(referred_user, "text", "") or "").strip()
    match = re.match(r"^/start(?:@\w+)?\s+([A-Za-z0-9_-]+)", text, re.IGNORECASE)
    if not match:
        return None
    code = match.group(1)
    referrer_id = None
    bonus = 0.0
    referral_count = 0
    activated = None
    suspicious_reason = None
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT user_id FROM referral_codes WHERE code = ?", (code,))
            owner = c.fetchone()
            if not owner:
                conn.close()
                return {"status": "invalid"}
            referrer_id = int(owner[0])
            if referrer_id == referred_id:
                suspicious_reason = "Self-referral attempt"
                conn.close()
            else:
                if not allow_new_user:
                    conn.close()
                    return {"status": "already_registered"}
                c.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (referrer_id,))
                if c.fetchone():
                    conn.close()
                    return {"status": "blocked"}
                c.execute("SELECT 1 FROM referrals WHERE referred_id = ?", (referred_id,))
                if c.fetchone():
                    conn.close()
                    return {"status": "already_registered"}
                try:
                    bonus = float(get_setting("referral_bonus") or 0)
                except (TypeError, ValueError):
                    bonus = 0.0
                c.execute(
                    """INSERT INTO referrals
                       (referrer_id, referred_id, referral_code, referred_username,
                        referred_name, status, verified_at)
                       VALUES (?, ?, ?, ?, ?, 'verified', CURRENT_TIMESTAMP)""",
                    (referrer_id, referred_id, code,
                     getattr(referred_user, "username", "") or "",
                     getattr(referred_user, "first_name", "") or "")
                )
                if bonus > 0:
                    c.execute(
                        """INSERT OR REPLACE INTO user_balances (user_id, balance)
                           VALUES (?, COALESCE((SELECT balance FROM user_balances
                           WHERE user_id = ?), 0) + ?)""",
                        (referrer_id, referrer_id, bonus)
                    )
                c.execute(
                    "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'verified'",
                    (referrer_id,)
                )
                referral_count = int(c.fetchone()[0] or 0)
                conn.commit()
                conn.close()
                # A referral only increases the user's progress.  The user
                # must explicitly select an eligible plan to claim it.
                activated = None
    except sqlite3.IntegrityError:
        return {"status": "already_registered"}
    except Exception as e:
        logger.error(f"Could not register referral for {referred_id}: {e}", exc_info=True)
        return {"status": "error"}

    if suspicious_reason:
        strike = add_referral_strike(referrer_id, suspicious_reason)
        warning = (
            f"⚠️ *Referral abuse warning*\n\n📌 Reason: {suspicious_reason}\n"
            f"🧾 Strike: {strike}/2\n"
        )
        if strike >= 2:
            ban_user(referrer_id, "Second referral abuse strike", OWNER_ID, notify=True)
            warning += "⛔ Account auto-banned."
        else:
            warning += "দ্বিতীয়বার হলে account auto-ban হবে।"
        try:
            bot.send_message(referrer_id, render_body_text(warning), parse_mode='HTML')
        except Exception:
            pass
        _notify_referral_admins(
            f"🔔 *Referral abuse detected*\n👤 User ID: `{referrer_id}`\n"
            f"📌 Reason: {suspicious_reason}\n🧾 Strike: {strike}/2"
        )
        return {"status": "suspicious", "referrer_id": referrer_id, "strike": strike}

    success = (
        f"🎉 *Successful referral!*\n👤 New user: `{referred_id}`\n"
        f"✅ Total referrals: {referral_count}\n💰 Bonus added: ৳{bonus:.2f}"
    )
    try:
        bot.send_message(referrer_id, render_body_text(success), parse_mode='HTML')
    except Exception as e:
        logger.warning(f"Could not notify referrer {referrer_id}: {e}")
    _notify_referral_admins(
        f"🔔 *New successful referral*\n👤 Referrer: `{referrer_id}`\n"
        f"👤 Referred user: `{referred_id}`\n✅ Count: {referral_count}\n"
        f"💰 Bonus: ৳{bonus:.2f}"
    )
    if activated and not activated.get("already_active"):
        grant_text = (
            f"🎁 *Free hosting activated!*\n📦 Plan: {activated['plan_name']}\n"
            f"📁 File limit: {activated['file_limit']}\n"
            f"⏰ Hosting time: {activated['host_hours']} hours\n"
            f"⌛ Expires: {activated['expiry'].strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            bot.send_message(referrer_id, render_body_text(grant_text), parse_mode='HTML')
        except Exception:
            pass
        _notify_referral_admins(
            f"🔔 *Free host activated*\n👤 User ID: `{referrer_id}`\n"
            f"📦 Plan: {activated['plan_name']}"
        )
    return {
        "status": "verified", "referrer_id": referrer_id,
        "count": referral_count, "bonus": bonus, "activated": activated
    }

def _referral_message(user_id):
    link = get_referral_link(user_id)
    count = get_referral_count(user_id)
    bonus = get_referral_bonus()
    link_text = link or "লিংক তৈরি করা যায়নি—বট username সেট আছে কি না দেখুন।"
    markup = types.InlineKeyboardMarkup(row_width=1)
    if link:
        from urllib.parse import quote
        share_url = "https://t.me/share/url?url=" + quote(link) + "&text=" + quote(
            "এই বট দিয়ে নিজের bot host করুন!"
        )
        markup.add(types.InlineKeyboardButton("🔗 SHARE REFERRAL LINK", url=share_url))
    return (
        render_body_text(
            f"🎁 *REFER & BONUS*\n━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Successful referrals: *{count}*\n💰 Bonus per referral: ৳{bonus:.2f}\n\n"
            f"🔗 *Your unique referral link:*\n`{link_text}`\n\n"
            f"বন্ধুকে এই লিংক দিয়ে বটে `/start` করান। একই Telegram account "
            f"শুধু একবার গণনা হবে।"
        ),
        markup
    )

def _logic_referral(message, user_id=None):
    user_id = user_id or message.from_user.id
    if is_user_banned(user_id):
        send_banned_user_notice(message.chat.id, user_id)
        return
    text, markup = _referral_message(user_id)
    bot.reply_to(message, text, reply_markup=markup, parse_mode='HTML')

FREE_HOST_BUY_BUTTON_PREFIX = "𝘽𝙐𝙔 𝙁𝙍𝙀𝙀 𝙋𝙇𝘼𝙉 "
FREE_HOST_SHARE_BUTTON_TEXT = "𝙎𝙃𝘼𝙍𝙀 𝙍𝙀𝙁𝙁𝙀𝙍𝘼𝙇 𝙇𝙄𝙉𝙆"
FREE_HOST_BACK_BUTTON_TEXT = "𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝘽𝘼𝘾𝙆"

def _logic_free_host(message, user_id=None):
    user_id = user_id or message.from_user.id
    # Admins manage the same feature from the same button.
    if is_otp_admin(user_id):
        _logic_referral_admin_panel(message)
        return
    if is_user_banned(user_id):
        send_banned_user_notice(message.chat.id, user_id)
        return
    plans = get_free_host_plans()
    if not plans:
        bot.reply_to(
            message,
            render_body_text(
                "🤖 *FREE BOT HOST*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "⏳ Admin এখনো কোনো free hosting plan সেট করেনি।\n"
                "পরে আবার চেষ্টা করুন।"
            ),
            parse_mode='HTML'
        )
        return
    count = get_referral_count(user_id)
    grant = get_active_free_host_grant(user_id)
    referral_link = get_referral_link(user_id)
    claimed_plan_ids = get_claimed_free_host_plan_ids(user_id)
    plan_lines = []
    for plan in plans:
        if grant and grant["plan_id"] == plan["id"]:
            plan_status = (
                f"✅ ACTIVE until {grant['expiry'].strftime('%Y-%m-%d %H:%M')}"
            )
        elif plan["id"] in claimed_plan_ids:
            plan_status = "☑️ Already claimed"
        elif count >= plan["target"]:
            plan_status = "🎉 Eligible — select the button below"
        else:
            plan_status = f"🔒 Need {plan['target'] - count} more referral(s)"
        plan_lines.append(
            f"<blockquote>"
            f"🎁 *Plan {plan['id']}: {plan['name']}*\n"
            f"   👥 Required: {plan['target']} successful referrals\n"
            f"   📁 File limit: {plan['file_limit']}\n"
            f"   ⏰ Hosting time: {format_free_host_duration(plan['host_hours'])}\n"
            f"   {plan_status}"
            f"</blockquote>"
        )
    plan_text = "\n\n".join(plan_lines)
    link_text = referral_link or "লিংক তৈরি করা যায়নি—বট username সেট আছে কি না দেখুন।"
    keyboard_layout = []
    for plan in plans:
        keyboard_layout.append([{
            "text": f"{FREE_HOST_BUY_BUTTON_PREFIX}{plan['id']}",
            "icon_custom_emoji_id": EMOJI_GIFT,
            "style": "success",
        }])
    keyboard_layout.append([{
        "text": FREE_HOST_SHARE_BUTTON_TEXT,
        "icon_custom_emoji_id": EMOJI_USERS,
        "style": "primary",
    }])
    keyboard_layout.append([{
        "text": FREE_HOST_BACK_BUTTON_TEXT,
        "icon_custom_emoji_id": EMOJI_BACK,
        "style": "primary",
    }])
    bot.reply_to(
        message,
        render_body_text(
            f"🤖 *FREE BOT HOST PLANS*\n━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Your successful referrals: *{count}*\n"
            f"🔗 Your referral link:\n`{link_text}`\n\n"
            f"{plan_text}\n\n"
            f"👇 আপনার পছন্দের plan-এর *BUY FREE PLAN* button চাপুন।\n"
            f"Referral target পূরণ না হলে plan active হবে না।"
        ),
        reply_markup=build_reply_keyboard(keyboard_layout), parse_mode='HTML'
    )

def _logic_free_host_share(message):
    """Send the share action from inside the free-host plan menu."""
    user_id = message.from_user.id
    if is_user_banned(user_id):
        send_banned_user_notice(message.chat.id, user_id)
        return
    link = get_referral_link(user_id)
    if not link:
        bot.reply_to(
            message,
            render_body_text("❌ Referral link তৈরি করা যায়নি। পরে আবার চেষ্টা করুন।"),
            parse_mode='HTML'
        )
        return
    from urllib.parse import quote
    share_url = (
        "https://t.me/share/url?url=" + quote(link) +
        "&text=" + quote("এই বট দিয়ে নিজের bot host করুন!")
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔗 SHARE NOW", url=share_url))
    bot.reply_to(
        message,
        render_body_text(
            f"🔗 *আপনার referral link প্রস্তুত!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n`{link}`\n\n"
            f"👇 SHARE NOW চাপুন অথবা link copy করে বন্ধুদের পাঠান।"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def _logic_free_host_plan_selection(message):
    """Activate exactly the free-host plan selected by the user."""
    user_id = message.from_user.id
    if is_otp_admin(user_id):
        _logic_referral_admin_panel(message)
        return
    if is_user_banned(user_id):
        send_banned_user_notice(message.chat.id, user_id)
        return
    text = str(message.text or "").strip()
    if not text.startswith(FREE_HOST_BUY_BUTTON_PREFIX):
        return
    try:
        plan_id = int(text[len(FREE_HOST_BUY_BUTTON_PREFIX):].strip())
    except ValueError:
        bot.reply_to(
            message,
            render_body_text("❌ Free plan button সঠিক নয়। আবার FREE BOT HOST খুলুন।"),
            parse_mode='HTML'
        )
        return

    result = activate_selected_free_host_plan(user_id, plan_id)
    status = result.get("status")
    if status == "activated":
        plan = result["plan"]
        bot.reply_to(
            message,
            render_body_text(
                f"🎉 *FREE PLAN ACTIVATED SUCCESSFULLY!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 Plan: {plan['name']}\n"
                f"📁 File limit: {plan['file_limit']}\n"
                f"⏰ Hosting time: {format_free_host_duration(plan['host_hours'])}\n"
                f"⌛ Expires: {result['expiry'].strftime('%Y-%m-%d %H:%M')}\n\n"
                f"✅ এখন UPLOAD FILE থেকে আপনার bot host করুন।"
            ),
            parse_mode='HTML'
        )
    elif status == "insufficient":
        plan = result["plan"]
        remaining = plan["target"] - result["count"]
        bot.reply_to(
            message,
            render_body_text(
                f"🔒 *FREE PLAN NOT ACTIVE*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🎁 Plan: {plan['name']}\n"
                f"👥 Required: {plan['target']} successful referrals\n"
                f"✅ Completed: {result['count']}\n"
                f"📌 বাকি: {remaining} referral(s)\n\n"
                f"Referral complete করে আবার BUY FREE PLAN button চাপুন।"
            ),
            parse_mode='HTML'
        )
    elif status == "active":
        bot.reply_to(
            message,
            render_body_text(
                f"⏳ *একটি free plan ইতিমধ্যে active আছে।*\n"
                f"🎁 Plan: {result['plan_name']}\n"
                f"⌛ Expires: {result['expiry'].strftime('%Y-%m-%d %H:%M')}"
            ),
            parse_mode='HTML'
        )
    elif status == "claimed":
        bot.reply_to(
            message,
            render_body_text(
                "☑️ এই free plan আগে একবার claim করা হয়েছে।\n"
                "অন্য eligible plan থাকলে সেটি select করুন।"
            ),
            parse_mode='HTML'
        )
    elif status == "not_found":
        bot.reply_to(
            message,
            render_body_text("❌ এই free plan আর available নেই। FREE BOT HOST আবার খুলুন।"),
            parse_mode='HTML'
        )
    else:
        bot.reply_to(
            message,
            render_body_text("❌ Plan active করা যায়নি। পরে আবার চেষ্টা করুন।"),
            parse_mode='HTML'
        )
    if status == "activated":
        _logic_free_host(message)

@bot.message_handler(func=lambda message: (
    str(getattr(message, "text", "") or "").strip() ==
    FREE_HOST_SHARE_BUTTON_TEXT
))
def handle_free_host_share_button(message):
    _logic_free_host_share(message)

@bot.message_handler(func=lambda message: (
    str(getattr(message, "text", "") or "").strip() ==
    FREE_HOST_BACK_BUTTON_TEXT
))
def handle_free_host_back_button(message):
    go_back_to_main(message)

@bot.message_handler(func=lambda message: (
    str(getattr(message, "text", "") or "").strip().startswith(
        FREE_HOST_BUY_BUTTON_PREFIX
    )
))
def handle_free_host_plan_button(message):
    _logic_free_host_plan_selection(message)

def _logic_referral_admin_panel(message):
    user_id = message.from_user.id
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ Unauthorized!"), parse_mode='HTML')
        return
    plans = get_free_host_plans()
    plan_text = (
        "📦 Configured free plans:\n" + "\n".join(
            f"• ID {p['id']}: {p['name']} — {p['target']} referrals, "
            f"{format_free_host_duration(p['host_hours'])}, {p['file_limit']} files"
            for p in plans
        )
        if plans else "📦 Configured free plans: None"
    )
    bot.reply_to(
        message,
        render_body_text(
            f"🎁 *FREE BOT HOST SETTINGS*\n━━━━━━━━━━━━━━━━━\n\n"
            f"💰 Current referral bonus: ৳{get_referral_bonus():.2f}\n"
            f"{plan_text}\n\nSelect an admin action:"
        ),
        reply_markup=build_reply_keyboard(REFERRAL_ADMIN_BUTTONS),
        parse_mode='HTML'
    )

def handle_set_referral_bonus(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, render_body_text("⛔ Unauthorized!"), parse_mode='HTML')
        return
    bot.reply_to(
        message,
        render_body_text("💰 Send the bonus amount per successful referral (example: `5`):"),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, save_referral_bonus)

def save_referral_bonus(message):
    if not is_otp_admin(message.from_user.id):
        return
    try:
        amount = float(str(message.text).strip())
        if amount < 0 or not math.isfinite(amount):
            raise ValueError
    except (TypeError, ValueError):
        bot.reply_to(message, render_body_text("❌ Invalid amount. Send a non-negative number."), parse_mode='HTML')
        return
    if set_setting("referral_bonus", f"{amount:.2f}"):
        bot.reply_to(message, render_body_text(f"✅ Referral bonus updated to ৳{amount:.2f}."), parse_mode='HTML')
    else:
        bot.reply_to(message, render_body_text("❌ Could not save referral bonus."), parse_mode='HTML')

def handle_free_host_plan_admin(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, render_body_text("⛔ Unauthorized!"), parse_mode='HTML')
        return
    plans = get_free_host_plans()
    current = (
        "📦 Configured plans:\n" + "\n".join(
            f"• ID {p['id']}: {p['name']} | target {p['target']} | "
            f"{format_free_host_duration(p['host_hours'])} | {p['file_limit']} files"
            for p in plans
        )
        if plans else "📦 Current: no plan"
    )
    bot.reply_to(
        message,
        render_body_text(f"🎁 *FREE HOST PLAN SETTINGS*\n━━━━━━━━━━━━━━━━━\n\n{current}"),
        reply_markup=build_reply_keyboard(FREE_HOST_PLAN_ADMIN_BUTTONS),
        parse_mode='HTML'
    )

def handle_add_free_host_plan(message):
    if not is_otp_admin(message.from_user.id):
        return
    bot.reply_to(
        message,
        render_body_text(
            "➕ Send plan details in this exact format:\n"
            "`Plan Name | Referral Target | Host Hours | File Limit`\n\n"
            "Example: `Starter | 100 | 24 | 1`"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, save_free_host_plan)

def save_free_host_plan(message):
    if not is_otp_admin(message.from_user.id):
        return
    try:
        parts = [p.strip() for p in str(message.text).split("|")]
        if len(parts) != 4:
            raise ValueError
        name = parts[0][:80]
        target, hours, file_limit = map(int, parts[1:])
        if not name or target < 1 or hours < 1 or file_limit < 1:
            raise ValueError
    except (TypeError, ValueError):
        bot.reply_to(message, render_body_text("❌ Invalid format. Use: `Starter | 100 | 24 | 1`"), parse_mode='HTML')
        return
    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM free_host_plans")
            plan_id = int(c.fetchone()[0])
            c.execute(
                """INSERT INTO free_host_plans
                   (id, plan_name, referral_target, host_hours, file_limit, updated_at)
                   VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (plan_id, name, target, hours, file_limit)
            )
            conn.commit()
            conn.close()
        bot.reply_to(
            message,
            render_body_text(
                f"✅ Free hosting plan saved! (ID: {plan_id})\n📦 {name}\n👥 Target: {target}\n"
                f"⏰ Hours: {hours}\n📁 Files: {file_limit}"
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Could not save free host plan: {e}", exc_info=True)
        bot.reply_to(message, render_body_text("❌ Could not save the plan."), parse_mode='HTML')

def handle_remove_free_host_plan(message):
    if not is_otp_admin(message.from_user.id):
        return
    bot.reply_to(
        message,
        render_body_text("🗑️ Send the plan ID to remove (use the ID shown in FREE HOST PLAN settings):"),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(message, remove_free_host_plan)

def remove_free_host_plan(message):
    if not is_otp_admin(message.from_user.id):
        return
    try:
        plan_id = int(str(message.text).strip())
        if plan_id < 1:
            raise ValueError
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("DELETE FROM free_host_plans WHERE id = ?", (plan_id,))
            removed = c.rowcount > 0
            conn.commit()
            conn.close()
        bot.reply_to(
            message,
            render_body_text(
                f"✅ Free host plan {plan_id} removed."
                if removed else f"ℹ️ Free host plan {plan_id} was not found."
            ),
            parse_mode='HTML'
        )
    except ValueError:
        bot.reply_to(message, render_body_text("❌ Plan ID must be a positive number."), parse_mode='HTML')
    except Exception as e:
        logger.error(f"Could not remove free host plan: {e}", exc_info=True)
        bot.reply_to(message, render_body_text("❌ Could not remove the plan."), parse_mode='HTML')

def get_user_file_limit(user_id):
    """Get the file upload limit for a user"""
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    
    premium = get_user_premium_plan(user_id)
    if premium and premium["expiry"] > datetime.now():
        return premium["file_limit"]

    free_grant = get_active_free_host_grant(user_id)
    if free_grant:
        return free_grant["file_limit"]
    
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    
    return FREE_USER_LIMIT_SETTINGS["limit"]

def get_user_host_time(user_id):
    """Get the host time for a user's files"""
    if user_id == OWNER_ID: return float('inf')
    if user_id in admin_ids: return float('inf')
    
    premium = get_user_premium_plan(user_id)
    if premium and premium["expiry"] > datetime.now():
        return float('inf')

    free_grant = get_active_free_host_grant(user_id)
    if free_grant:
        return free_grant["host_hours"]
    
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return 168
    
    return FREE_USER_LIMIT_SETTINGS["host_time"]

def get_user_upload_count_in_time(user_id):
    """Get number of uploads in current time window"""
    upload_times = user_upload_times.get(user_id, [])
    time_limit_hours = FREE_USER_LIMIT_SETTINGS["time"]
    
    premium = get_user_premium_plan(user_id)
    if premium and premium["expiry"] > datetime.now():
        return 0

    if get_active_free_host_grant(user_id):
        return 0
    
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(hours=time_limit_hours)
    return len([t for t in upload_times if t > cutoff_time])

def _persist_file_state_to_sheets(action):
    """Flush important file-state changes before a host restart can lose them."""
    configured = globals().get("_google_sheets_configured")
    if not callable(configured) or not configured():
        return None
    if not globals().get("google_sheet_data_loaded", False):
        logger.error(
            "Cannot persist file action '%s': Google Sheets data is not loaded.",
            action,
        )
        return False
    sync = globals().get("sync_to_google_sheets")
    if not callable(sync):
        logger.error("Google Sheets sync is not ready for file action '%s'.", action)
        return False
    try:
        if sync(force=True):
            return True
        logger.error("Google Sheets checkpoint failed after file action '%s'.", action)
    except Exception:
        logger.exception("Google Sheets checkpoint raised after file action '%s'.", action)
    retry = globals().get("trigger_google_sheets_sync")
    if callable(retry):
        retry()
    return False


def stop_user_file(user_id, file_name):
    """Stop a user's file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            'UPDATE user_files SET is_stopped = 1 '
            'WHERE user_id = ? AND file_name = ? AND COALESCE(is_stopped, 0) = 0',
            (user_id, file_name)
        )
        newly_stopped = c.rowcount > 0
        conn.commit()
        conn.close()
        
        if user_id not in file_stop_status:
            file_stop_status[user_id] = []
        if file_name not in file_stop_status[user_id]:
            file_stop_status[user_id].append(file_name)
        
        script_key = f"{user_id}_{file_name}"
        if script_key in bot_scripts:
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]
        
        if not newly_stopped:
            logger.info(
                "Duplicate stop suppressed for file %s (user %s).",
                file_name,
                user_id,
            )
            return False

        logger.info(f"🛑 File stopped: {file_name} for user {user_id}")
        _persist_file_state_to_sheets(f"stop {user_id}/{file_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Error stopping file: {e}")
        return False

def start_user_file(user_id, file_name):
    """Start a user's file (remove from stop status)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('UPDATE user_files SET is_stopped = 0 WHERE user_id = ? AND file_name = ?', (user_id, file_name))
        conn.commit()
        conn.close()
        
        if user_id in file_stop_status and file_name in file_stop_status[user_id]:
            file_stop_status[user_id].remove(file_name)
            if not file_stop_status[user_id]:
                del file_stop_status[user_id]
        
        logger.info(f"🟢 File started: {file_name} for user {user_id}")
        _persist_file_state_to_sheets(f"start {user_id}/{file_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Error starting file: {e}")
        return False

# --- Auto Checker Functions ---
def check_and_stop_expired_files():
    """Check and stop files that have expired"""
    logger.info("🔍 Checking for expired files...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, file_name, upload_time FROM user_files WHERE is_stopped = 0')
        files = c.fetchall()
        conn.close()
        
        current_time = datetime.now()
        stopped_count = 0
        
        for user_id, file_name, upload_time_str in files:
            try:
                upload_time = datetime.fromisoformat(upload_time_str)
                host_time_hours = get_user_host_time(user_id)
                
                if host_time_hours != float('inf'):
                    expiry_time = upload_time + timedelta(hours=host_time_hours)
                    if current_time > expiry_time:
                        if stop_user_file(user_id, file_name):
                            stopped_count += 1
                            try:
                                bot.send_message(
                                    user_id,
                                    render_body_text(
                                        f"⏰ *আপনার ফাইল হোস্ট করার সময় শেষ হয়েছে!*\n"
                                        f"━━━━━━━━━━━━━━━━━\n\n"
                                        f"📄 ফাইল: `{file_name}`\n"
                                        f"⏰ সময় শেষ: {host_time_hours} ঘন্টা\n\n"
                                        f"💡 *আবার ফাইল আপলোড করতে পারেন*"
                                    ),
                                    parse_mode='HTML'
                                )
                            except:
                                pass
                            
                            for admin_id in get_unique_admin_ids():
                                try:
                                    bot.send_message(
                                        admin_id,
                                        render_body_text(
                                            f"🔔 *একটি ফাইল অটো স্টপ হয়েছে!*\n"
                                            f"━━━━━━━━━━━━━━━━━\n\n"
                                            f"👤 ইউজার: `{user_id}`\n"
                                            f"📄 ফাইল: `{file_name}`\n"
                                            f"⏰ হোস্ট সময় শেষ: {host_time_hours} ঘন্টা"
                                        ),
                                        parse_mode='HTML'
                                    )
                                except:
                                    pass
            except Exception as e:
                logger.error(f"Error processing file {file_name} for user {user_id}: {e}")
        
        if stopped_count > 0:
            logger.info(f"✅ Stopped {stopped_count} expired files")
            
    except Exception as e:
        logger.error(f"❌ Error checking expired files: {e}")

def check_and_stop_subscription_expired():
    """Check and stop files for users with expired subscriptions"""
    logger.info("🔍 Checking for expired subscriptions...")
    
    try:
        current_time = datetime.now()
        stopped_count = 0
        
        for user_id, premium_data in list(user_premium_plans.items()):
            if premium_data["expiry"] <= current_time:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute('SELECT file_name FROM user_files WHERE user_id = ? AND is_stopped = 0', (user_id,))
                files = c.fetchall()
                conn.close()
                
                for file_name in files:
                    if stop_user_file(user_id, file_name[0]):
                        stopped_count += 1
                        try:
                            bot.send_message(
                                user_id,
                                render_body_text(
                                    f"⏰ *আপনার প্রিমিয়াম প্লান শেষ হয়েছে!*\n"
                                    f"━━━━━━━━━━━━━━━━━\n\n"
                                    f"📄 ফাইল: `{file_name[0]}`\n"
                                    f"💡 *আবার প্রিমিয়াম কিনতে পারেন*"
                                ),
                                parse_mode='HTML'
                            )
                        except:
                            pass
                
                del user_premium_plans[user_id]
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('DELETE FROM user_premium WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                except:
                    pass
                
                for admin_id in get_unique_admin_ids():
                    try:
                        bot.send_message(
                            admin_id,
                            render_body_text(
                                f"🔔 *একটি প্রিমিয়াম প্লান শেষ হয়েছে!*\n"
                                f"━━━━━━━━━━━━━━━━━\n\n"
                                f"👤 ইউজার: `{user_id}`\n"
                                f"📄 ফাইল স্টপ: {len(files)} টি\n"
                                f"⏰ সাবস্ক্রিপশনের সময় শেষ হয়েছে"
                            ),
                            parse_mode='HTML'
                        )
                    except:
                        pass
        
        for user_id, sub_data in list(user_subscriptions.items()):
            if sub_data["expiry"] <= current_time:
                conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                c = conn.cursor()
                c.execute('SELECT file_name FROM user_files WHERE user_id = ? AND is_stopped = 0', (user_id,))
                files = c.fetchall()
                conn.close()
                
                for file_name in files:
                    if stop_user_file(user_id, file_name[0]):
                        stopped_count += 1
                
                del user_subscriptions[user_id]
                try:
                    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                    c = conn.cursor()
                    c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
                    conn.commit()
                    conn.close()
                except:
                    pass
        
        if stopped_count > 0:
            logger.info(f"✅ Stopped {stopped_count} files due to expired subscriptions")
            
    except Exception as e:
        logger.error(f"❌ Error checking expired subscriptions: {e}")

def auto_checker():
    """Auto checker thread - runs every minute"""
    while True:
        try:
            check_and_stop_expired_files()
            check_and_stop_subscription_expired()
            time.sleep(60)
        except Exception as e:
            logger.error(f"❌ Auto checker error: {e}")
            time.sleep(60)

auto_checker_thread = None
_auto_checker_start_lock = threading.Lock()


def start_auto_checker():
    """Start expiry checks once, only after durable data has loaded."""
    global auto_checker_thread
    with _auto_checker_start_lock:
        if auto_checker_thread and auto_checker_thread.is_alive():
            return
        auto_checker_thread = Thread(
            target=auto_checker,
            daemon=True,
            name="file-expiry-checker",
        )
        auto_checker_thread.start()
        logger.info("🔄 Auto checker started after durable data load.")

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder for storing files"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

# Telegram callback_data is limited to 64 bytes.  A raw user id plus the
# complete filename can exceed that limit (especially with Unicode names),
# which makes Telegram reject the keyboard or leaves the button unusable.
# Keep callbacks short and resolve the filename from the in-memory file list.
def make_file_callback(prefix, user_id, file_name):
    token_source = f"{user_id}\0{file_name}".encode("utf-8")
    token = hashlib.sha256(token_source).hexdigest()[:16]
    return f"{prefix}_{token}"

def resolve_file_callback(data, prefix):
    """Return (owner_id, filename) for new short callbacks or old callbacks."""
    marker = f"{prefix}_"
    if not data.startswith(marker):
        return None

    value = data[len(marker):]

    # New callbacks use a deterministic short SHA-256 token.  Searching the
    # already-loaded list also keeps old Telegram messages working after a
    # bot restart.
    if len(value) == 16 and re.fullmatch(r"[0-9a-f]{16}", value):
        for owner_id, files in user_files.items():
            for file_name, _file_type in files:
                expected = hashlib.sha256(
                    f"{owner_id}\0{file_name}".encode("utf-8")
                ).hexdigest()[:16]
                if expected == value:
                    return int(owner_id), file_name

        # The in-memory cache can be stale after a restart or when a file was
        # uploaded by another worker.  Resolve the same short token directly
        # from SQLite so a valid Check Files button never becomes a dead
        # callback just because the cache was not populated.
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, file_name FROM user_files")
            rows = cursor.fetchall()
            conn.close()
            for owner_id, file_name in rows:
                expected = hashlib.sha256(
                    f"{owner_id}\0{file_name}".encode("utf-8")
                ).hexdigest()[:16]
                if expected == value:
                    return int(owner_id), file_name
        except Exception as e:
            logger.error(f"Database file callback resolution failed: {e}")
        return None

    # Backward compatibility for buttons created by older versions:
    # prefix_<user_id>_<filename>
    try:
        owner_id, file_name = value.split("_", 1)
        return int(owner_id), file_name
    except (ValueError, IndexError):
        return None


def get_user_files_for_owner(user_id):
    """Return the authoritative file list and refresh the local cache."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_name, file_type FROM user_files "
            "WHERE user_id = ? ORDER BY file_name",
            (int(user_id),)
        )
        rows = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        if rows:
            user_files[int(user_id)] = rows
        elif int(user_id) in user_files:
            # A database delete is authoritative; do not keep showing a
            # removed file from the old in-memory list.
            user_files.pop(int(user_id), None)
        return rows
    except Exception as e:
        logger.error(f"Could not load files for user {user_id}: {e}")
        return list(user_files.get(int(user_id), []))

def get_user_file_count(user_id):
    """Get the number of files uploaded by a user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name):
    """Check if a bot script is currently running"""
    script_key = f"{script_owner_id}_{file_name}"
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                logger.warning(f"Process {script_info['process'].pid} for {script_key} found in memory but not running/zombie. Cleaning up.")
                if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                    try:
                        script_info['log_file'].close()
                    except Exception as log_e:
                        logger.error(f"Error closing log file during zombie cleanup {script_key}: {log_e}")
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            logger.warning(f"Process for {script_key} not found (NoSuchProcess). Cleaning up.")
            if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                try:
                    script_info['log_file'].close()
                except Exception as log_e:
                    logger.error(f"Error closing log file during cleanup of non-existent process {script_key}: {log_e}")
            if script_key in bot_scripts:
                del bot_scripts[script_key]
            return False
        except Exception as e:
            logger.error(f"Error checking process status for {script_key}: {e}", exc_info=True)
            return False
    return False

def kill_process_tree(process_info):
    """Kill a process and all its children"""
    pid = None
    log_file_closed = False
    script_key = process_info.get('script_key', 'N/A')

    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close') and not process_info['log_file'].closed:
            try:
                process_info['log_file'].close()
                log_file_closed = True
                logger.info(f"Closed log file for {script_key} (PID: {process_info.get('process', {}).get('pid', 'N/A')})")
            except Exception as log_e:
                logger.error(f"Error closing log file during kill for {script_key}: {log_e}")

        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
            pid = process.pid
            if pid:
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    logger.info(f"Attempting to kill process tree for {script_key} (PID: {pid}, Children: {[c.pid for c in children]})")

                    for child in children:
                        try:
                            child.terminate()
                            logger.info(f"Terminated child process {child.pid} for {script_key}")
                        except psutil.NoSuchProcess:
                            logger.warning(f"Child process {child.pid} for {script_key} already gone.")
                        except Exception as e:
                            logger.error(f"Error terminating child {child.pid} for {script_key}: {e}. Trying kill...")
                            try:
                                child.kill()
                                logger.info(f"Killed child process {child.pid} for {script_key}")
                            except Exception as e2:
                                logger.error(f"Failed to kill child {child.pid} for {script_key}: {e2}")

                    gone, alive = psutil.wait_procs(children, timeout=1)
                    for p in alive:
                        logger.warning(f"Child process {p.pid} for {script_key} still alive. Killing.")
                        try:
                            p.kill()
                        except Exception as e:
                            logger.error(f"Failed to kill child {p.pid} for {script_key} after wait: {e}")

                    try:
                        parent.terminate()
                        logger.info(f"Terminated parent process {pid} for {script_key}")
                        try:
                            parent.wait(timeout=1)
                        except psutil.TimeoutExpired:
                            logger.warning(f"Parent process {pid} for {script_key} did not terminate. Killing.")
                            parent.kill()
                            logger.info(f"Killed parent process {pid} for {script_key}")
                    except psutil.NoSuchProcess:
                        logger.warning(f"Parent process {pid} for {script_key} already gone.")
                    except Exception as e:
                        logger.error(f"Error terminating parent {pid} for {script_key}: {e}. Trying kill...")
                        try:
                            parent.kill()
                            logger.info(f"Killed parent process {pid} for {script_key}")
                        except Exception as e2:
                            logger.error(f"Failed to kill parent {pid} for {script_key}: {e2}")

                except psutil.NoSuchProcess:
                    logger.warning(f"Process {pid or 'N/A'} for {script_key} not found during kill. Already terminated?")
            else:
                logger.error(f"Process PID is None for {script_key}.")
        elif log_file_closed:
            logger.warning(f"Process object missing for {script_key}, but log file closed.")
        else:
            logger.error(f"Process object missing for {script_key}, and no log file. Cannot kill.")
    except Exception as e:
        logger.error(f"❌ Unexpected error killing process tree for PID {pid or 'N/A'} ({script_key}): {e}", exc_info=True)

# --- Telegram Modules Mapping ---
TELEGRAM_MODULES = {
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pillow': 'Pillow',
    'cv2': 'opencv-python',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'flask': 'Flask',
    'django': 'Django',
    'sqlalchemy': 'SQLAlchemy',
    'psutil': 'psutil',
    'asyncio': None,
    'json': None,
    'datetime': None,
    'os': None,
    'sys': None,
    're': None,
    'time': None,
    'math': None,
    'random': None,
    'logging': None,
    'threading': None,
    'subprocess': None,
    'zipfile': None,
    'tempfile': None,
    'shutil': None,
    'sqlite3': None,
    'atexit': None
}

# Keep dependency setup fast without sacrificing compatibility:
# - pip installs all discovered packages in one command
# - --prefer-binary avoids slow source builds when a wheel exists
# - --no-input prevents a package prompt from blocking the bot
# - npm skips network-heavy audit/funding checks
PIP_FAST_INSTALL_FLAGS = [
    '--disable-pip-version-check',
    '--no-input',
    '--prefer-binary',
    '--upgrade-strategy', 'only-if-needed',
]
NPM_FAST_INSTALL_FLAGS = ['--no-audit', '--no-fund', '--prefer-offline']

# --- Script Running Functions ---
def _python_import_names(script_path):
    """Return top-level imports without importing or executing user code."""
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as source:
            tree = ast.parse(source.read(), filename=script_path)
    except (OSError, SyntaxError) as e:
        logger.warning(f"Could not inspect Python imports in {script_path}: {e}")
        return []

    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(
                alias.name.split('.')[0].strip()
                for alias in node.names
                if alias.name
            )
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split('.')[0].strip())
    return sorted(module for module in modules if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', module))


def _missing_python_packages(script_path):
    """Find all unavailable third-party packages used by one Python file."""
    missing = []
    for module_name in _python_import_names(script_path):
        package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name)
        if package_name is None:
            continue
        try:
            available = importlib.util.find_spec(module_name) is not None
        except (ImportError, AttributeError, ValueError):
            available = False
        if not available and package_name not in missing:
            missing.append(package_name)
    return missing


def install_python_requirements_file(req_path, message):
    """Install exactly the packages listed in a requirements file."""
    req_name = os.path.basename(req_path)
    bot.reply_to(
        message,
        render_body_text(f"🔄 Manual mode: installing modules from `{req_name}`..."),
        parse_mode='HTML'
    )
    try:
        command = (
            [sys.executable, '-m', 'pip', 'install']
            + PIP_FAST_INSTALL_FLAGS
            + ['-r', req_path]
        )
        result = subprocess.run(
            command, capture_output=True, text=True, check=False,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            bot.reply_to(
                message,
                render_body_text(f"✅ Modules from `{req_name}` installed successfully."),
                parse_mode='HTML'
            )
            return True
        error_text = result.stderr or result.stdout or "Unknown pip error"
        logger.error(f"Requirements install failed for {req_path}: {error_text}")
        error_msg = f"❌ Failed to install modules from `{req_name}`.\nLog:\n```\n{error_text}\n```"
        bot.reply_to(message, error_msg[:4000], parse_mode='HTML')
        return False
    except Exception as e:
        logger.error(f"Unexpected requirements install error: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Error installing `{req_name}`: {e}")
        return False


def install_missing_python_modules(script_path, message):
    """Install all missing Python packages together for Auto mode."""
    packages = _missing_python_packages(script_path)
    if not packages:
        return True

    bot.reply_to(
        message,
        render_body_text(
            "🔄 *Auto mode: installing all missing Python modules together...*\n"
            f"📦 Packages: `{', '.join(packages)}`"
        ),
        parse_mode='HTML'
    )
    try:
        command = (
            [sys.executable, '-m', 'pip', 'install']
            + PIP_FAST_INSTALL_FLAGS
            + packages
        )
        result = subprocess.run(
            command, capture_output=True, text=True, check=False,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            bot.reply_to(
                message,
                render_body_text(
                    f"✅ All missing Python modules installed ({len(packages)} package(s))."
                ),
                parse_mode='HTML'
            )
            return True
        error_text = result.stderr or result.stdout or "Unknown pip error"
        logger.error(f"Auto Python install failed: {error_text}")
        error_msg = (
            "❌ Auto module installation failed.\n"
            f"Packages: `{', '.join(packages)}`\n"
            f"Log:\n```\n{error_text}\n```"
        )
        bot.reply_to(message, error_msg[:4000], parse_mode='HTML')
        return False
    except Exception as e:
        logger.error(f"Unexpected auto Python install error: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Auto module installation error: {e}")
        return False


def _node_import_names(script_path):
    """Return external CommonJS/ES module names used by a JavaScript file."""
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as source:
            code = source.read()
    except OSError as e:
        logger.warning(f"Could not inspect JS imports in {script_path}: {e}")
        return []

    matches = re.findall(
        r"""(?:require\s*\(\s*|from\s*['"]|import\s*['"])([^'"\s)]+)""",
        code
    )
    packages = set()
    for package_name in matches:
        if package_name.startswith(('.', '/', 'node:')):
            continue
        packages.add(package_name)
    return sorted(packages)


def install_missing_node_modules(script_path, user_folder, message):
    """Install all external Node packages found in a JS file together."""
    packages = []
    for package_name in _node_import_names(script_path):
        package_path = os.path.join(
            user_folder, 'node_modules', *package_name.split('/')
        )
        if not os.path.exists(package_path):
            packages.append(package_name)
    if not packages:
        return True

    bot.reply_to(
        message,
        render_body_text(
            "🔄 *Auto mode: installing all missing Node modules together...*\n"
            f"📦 Packages: `{', '.join(packages)}`"
        ),
        parse_mode='HTML'
    )
    try:
        result = subprocess.run(
            ['npm', 'install'] + NPM_FAST_INSTALL_FLAGS + packages,
            capture_output=True, text=True, check=False, cwd=user_folder,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            bot.reply_to(
                message,
                render_body_text(
                    f"✅ All missing Node modules installed ({len(packages)} package(s))."
                ),
                parse_mode='HTML'
            )
            return True
        error_text = result.stderr or result.stdout or "Unknown npm error"
        logger.error(f"Auto Node install failed: {error_text}")
        bot.reply_to(
            message,
            f"❌ Auto Node module installation failed.\nLog:\n```\n{error_text}\n```"[:4000],
            parse_mode='HTML'
        )
        return False
    except FileNotFoundError:
        bot.reply_to(message, "❌ `npm` পাওয়া যায়নি। Node.js/npm install করুন।")
        return False
    except Exception as e:
        logger.error(f"Unexpected auto Node install error: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Auto Node module installation error: {e}")
        return False


def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name) 
    if package_name is None: 
        logger.info(f"Module '{module_name}' is core. Skipping pip install.")
        return False 
    try:
        bot.reply_to(message, f"🐍 Module `{module_name}` not found. Installing `{package_name}`...", parse_mode='HTML')
        command = (
            [sys.executable, '-m', 'pip', 'install']
            + PIP_FAST_INSTALL_FLAGS
            + [package_name]
        )
        logger.info(f"Running install: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"Installed {package_name}. Output:\n{result.stdout}")
            bot.reply_to(message, f"✅ Package `{package_name}` (for `{module_name}`) installed.", parse_mode='HTML')
            return True
        else:
            error_msg = f"❌ Failed to install `{package_name}` for `{module_name}`.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='HTML')
            return False
    except Exception as e:
        error_msg = f"❌ Error installing `{package_name}`: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        bot.reply_to(message, f"🟠 Node package `{module_name}` not found. Installing locally...", parse_mode='HTML')
        command = ['npm', 'install'] + NPM_FAST_INSTALL_FLAGS + [module_name]
        logger.info(f"Running npm install: {' '.join(command)} in {user_folder}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"Installed {module_name}. Output:\n{result.stdout}")
            bot.reply_to(message, f"✅ Node package `{module_name}` installed locally.", parse_mode='HTML')
            return True
        else:
            error_msg = f"❌ Failed to install Node package `{module_name}`.\nLog:\n```\n{result.stderr or result.stdout}\n```"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='HTML')
            return False
    except FileNotFoundError:
         error_msg = "❌ Error: 'npm' not found. Ensure Node.js/npm are installed and in PATH."
         logger.error(error_msg)
         bot.reply_to(message, error_msg)
         return False
    except Exception as e:
        error_msg = f"❌ Error installing Node package `{module_name}`: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def _return_user_to_main_menu_after_deploy(message_obj, script_owner_id):
    """Return a user to the same main menu shown by /start after deployment.

    Admin start/restart actions use a small fake message that has no
    ``from_user``.  Only an actual upload message from the file owner should
    trigger the automatic return, otherwise an admin could receive a menu
    intended for another user.
    """
    source_user = getattr(message_obj, "from_user", None)
    if getattr(source_user, "id", None) != script_owner_id:
        return
    try:
        go_back_to_main(message_obj, menu_user_id=script_owner_id)
    except Exception as exc:
        logger.warning(
            "Could not return user %s to the main menu after deployment: %s",
            script_owner_id,
            exc,
            exc_info=True,
        )


def run_script(
    script_path, script_owner_id, user_folder, file_name,
    message_obj_for_reply, attempt=1, dependency_mode='auto'
):
    """Run Python script"""
    max_attempts = 2 
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} attempts. Check logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Attempt {attempt} to run Python script: {script_path} (Key: {script_key}) for user {script_owner_id}")

    try:
        if not os.path.exists(script_path):
            bot.reply_to(message_obj_for_reply, f"❌ Error: Script '{file_name}' not found at '{script_path}'!")
            logger.error(f"Script not found: {script_path} for user {script_owner_id}")
            # Keep the database record so a temporary filesystem problem
            # cannot silently destroy the user's file metadata.
            stop_user_file(script_owner_id, file_name)
            return

        if script_owner_id in file_stop_status and file_name in file_stop_status[script_owner_id]:
            bot.reply_to(message_obj_for_reply, render_body_text(f"⏰ *এই ফাইলটি স্টপ করা হয়েছে!*\n\n📄 ফাইল: `{file_name}`\n💡 *আবার আপলোড করতে পারেন*"), parse_mode='HTML')
            return

        if attempt == 1:
            check_command = [sys.executable, script_path]
            logger.info(f"Running Python pre-check: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"Python Pre-check early. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_py = re.search(r"ModuleNotFoundError: No module named '(.+?)'", stderr)
                    if match_py:
                        module_name = match_py.group(1).strip().strip("'\"")
                        logger.info(f"Detected missing Python module: {module_name}")
                        if dependency_mode != 'auto':
                            bot.reply_to(
                                message_obj_for_reply,
                                f"❌ Manual mode: `{module_name}` is not in the uploaded requirements.txt."
                            )
                            return
                        if attempt_install_pip(module_name, message_obj_for_reply):
                            logger.info(f"Install OK for {module_name}. Retrying run_script...")
                            bot.reply_to(message_obj_for_reply, f"🔄 Install successful. Retrying '{file_name}'...")
                            time.sleep(2)
                            threading.Thread(
                                target=run_script,
                                args=(
                                    script_path, script_owner_id, user_folder,
                                    file_name, message_obj_for_reply,
                                    attempt + 1, dependency_mode
                                )
                            ).start()
                            return
                        else:
                            bot.reply_to(message_obj_for_reply, f"❌ Install failed. Cannot run '{file_name}'.")
                            return
                    else:
                        error_summary = stderr[:500]
                        bot.reply_to(message_obj_for_reply, f"❌ Error in script pre-check for '{file_name}':\n```\n{error_summary}\n```\nFix the script.", parse_mode='HTML')
                        return
            except subprocess.TimeoutExpired:
                logger.info("Python Pre-check timed out (>5s), imports likely OK. Killing check process.")
                if check_proc and check_proc.poll() is None:
                    check_proc.kill()
                    check_proc.communicate()
                logger.info("Python Check process killed. Proceeding to long run.")
            except FileNotFoundError:
                logger.error(f"Python interpreter not found: {sys.executable}")
                bot.reply_to(message_obj_for_reply, f"❌ Error: Python interpreter '{sys.executable}' not found.")
                return
            except Exception as e:
                logger.error(f"Error in Python pre-check for {script_key}: {e}", exc_info=True)
                bot.reply_to(message_obj_for_reply, f"❌ Unexpected error in script pre-check for '{file_name}': {e}")
                return
            finally:
                if check_proc and check_proc.poll() is None:
                    logger.warning(f"Python Check process {check_proc.pid} still running. Killing.")
                    check_proc.kill()
                    check_proc.communicate()

        logger.info(f"Starting long-running Python process for {script_key}")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None
        process = None
        try:
            log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to open log file '{log_file_path}' for {script_key}: {e}", exc_info=True)
            bot.reply_to(message_obj_for_reply, f"❌ Failed to open log file '{log_file_path}': {e}")
            return
        try:
            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                [sys.executable, script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"Started Python process {process.pid} for {script_key}")
            bot_scripts[script_key] = {
                'process': process,
                'log_file': log_file,
                'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(),
                'user_folder': user_folder,
                'type': 'py',
                'script_key': script_key
            }
            
            bot.reply_to(
                message_obj_for_reply,
                f"<tg-emoji emoji-id=\"{EMOJI_SUCCESS}\">✅</tg-emoji> Python script '{file_name}' started! (PID: {process.pid}) (For User: {script_owner_id})",
                parse_mode='HTML'
            )
            _return_user_to_main_menu_after_deploy(
                message_obj_for_reply, script_owner_id
            )
            
        except FileNotFoundError:
            logger.error(f"Python interpreter {sys.executable} not found for long run {script_key}")
            bot.reply_to(message_obj_for_reply, f"❌ Error: Python interpreter '{sys.executable}' not found.")
            if log_file and not log_file.closed:
                log_file.close()
            if script_key in bot_scripts:
                del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed:
                log_file.close()
            error_msg = f"❌ Error starting Python script '{file_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                logger.warning(f"Killing potentially started Python process {process.pid} for {script_key}")
                kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts:
                del bot_scripts[script_key]
                
    except Exception as e:
        error_msg = f"❌ Unexpected error running Python script '{file_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
            logger.warning(f"Cleaning up {script_key} due to error in run_script.")
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]

def run_js_script(
    script_path, script_owner_id, user_folder, file_name,
    message_obj_for_reply, attempt=1, dependency_mode='auto'
):
    """Run JS script"""
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"❌ Failed to run '{file_name}' after {max_attempts} attempts. Check logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Attempt {attempt} to run JS script: {script_path} (Key: {script_key}) for user {script_owner_id}")

    try:
        if not os.path.exists(script_path):
            bot.reply_to(message_obj_for_reply, f"❌ Error: Script '{file_name}' not found at '{script_path}'!")
            logger.error(f"JS Script not found: {script_path} for user {script_owner_id}")
            # Keep the database record so a temporary filesystem problem
            # cannot silently destroy the user's file metadata.
            stop_user_file(script_owner_id, file_name)
            return

        if script_owner_id in file_stop_status and file_name in file_stop_status[script_owner_id]:
            bot.reply_to(message_obj_for_reply, render_body_text(f"⏰ *এই ফাইলটি স্টপ করা হয়েছে!*\n\n📄 ফাইল: `{file_name}`\n💡 *আবার আপলোড করতে পারেন*"), parse_mode='HTML')
            return

        if attempt == 1:
            check_command = ['node', script_path]
            logger.info(f"Running JS pre-check: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"JS Pre-check early. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_js = re.search(r"Cannot find module '(.+?)'", stderr)
                    if match_js:
                        module_name = match_js.group(1).strip().strip("'\"")
                        if not module_name.startswith('.') and not module_name.startswith('/'):
                            logger.info(f"Detected missing Node module: {module_name}")
                            if dependency_mode != 'auto':
                                bot.reply_to(
                                    message_obj_for_reply,
                                    f"❌ Manual mode: `{module_name}` is not in the uploaded requirements.txt."
                                )
                                return
                            if attempt_install_npm(module_name, user_folder, message_obj_for_reply):
                                logger.info(f"NPM Install OK for {module_name}. Retrying run_js_script...")
                                bot.reply_to(message_obj_for_reply, f"🔄 NPM Install successful. Retrying '{file_name}'...")
                                time.sleep(2)
                                threading.Thread(
                                    target=run_js_script,
                                    args=(
                                        script_path, script_owner_id, user_folder,
                                        file_name, message_obj_for_reply,
                                        attempt + 1, dependency_mode
                                    )
                                ).start()
                                return
                            else:
                                bot.reply_to(message_obj_for_reply, f"❌ NPM Install failed. Cannot run '{file_name}'.")
                                return
                        else:
                            logger.info(f"Skipping npm install for relative/core: {module_name}")
                    error_summary = stderr[:500]
                    bot.reply_to(message_obj_for_reply, f"❌ Error in JS script pre-check for '{file_name}':\n```\n{error_summary}\n```\nFix script or install manually.", parse_mode='HTML')
                    return
            except subprocess.TimeoutExpired:
                logger.info("JS Pre-check timed out (>5s), imports likely OK. Killing check process.")
                if check_proc and check_proc.poll() is None:
                    check_proc.kill()
                    check_proc.communicate()
                logger.info("JS Check process killed. Proceeding to long run.")
            except FileNotFoundError:
                error_msg = "❌ Error: 'node' not found. Ensure Node.js is installed for JS files."
                logger.error(error_msg)
                bot.reply_to(message_obj_for_reply, error_msg)
                return
            except Exception as e:
                logger.error(f"Error in JS pre-check for {script_key}: {e}", exc_info=True)
                bot.reply_to(message_obj_for_reply, f"❌ Unexpected error in JS script pre-check for '{file_name}': {e}")
                return
            finally:
                if check_proc and check_proc.poll() is None:
                    logger.warning(f"JS Check process {check_proc.pid} still running. Killing.")
                    check_proc.kill()
                    check_proc.communicate()

        logger.info(f"Starting long-running JS process for {script_key}")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None
        process = None
        try:
            log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to open log file '{log_file_path}' for JS script {script_key}: {e}", exc_info=True)
            bot.reply_to(message_obj_for_reply, f"❌ Failed to open log file '{log_file_path}': {e}")
            return
        try:
            startupinfo = None
            creationflags = 0
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                ['node', script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"Started JS process {process.pid} for {script_key}")
            bot_scripts[script_key] = {
                'process': process,
                'log_file': log_file,
                'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(),
                'user_folder': user_folder,
                'type': 'js',
                'script_key': script_key
            }
            
            # 🔥 এখানে প্রিমিয়াম ইমোজি যোগ করা হয়েছে
            bot.reply_to(
                message_obj_for_reply,
                f"<tg-emoji emoji-id=\"{EMOJI_SUCCESS}\">✅</tg-emoji> JS script '{file_name}' started! (PID: {process.pid}) (For User: {script_owner_id})",
                parse_mode='HTML'
            )
            _return_user_to_main_menu_after_deploy(
                message_obj_for_reply, script_owner_id
            )
            
        except FileNotFoundError:
            error_msg = "❌ Error: 'node' not found for long run. Ensure Node.js is installed."
            logger.error(error_msg)
            if log_file and not log_file.closed:
                log_file.close()
            bot.reply_to(message_obj_for_reply, error_msg)
            if script_key in bot_scripts:
                del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed:
                log_file.close()
            error_msg = f"❌ Error starting JS script '{file_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                logger.warning(f"Killing potentially started JS process {process.pid} for {script_key}")
                kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts:
                del bot_scripts[script_key]
    except Exception as e:
        error_msg = f"❌ Unexpected error running JS script '{file_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
            logger.warning(f"Cleaning up {script_key} due to error in run_js_script.")
            kill_process_tree(bot_scripts[script_key])
            del bot_scripts[script_key]

# --- Database Operations ---
# The local SQLite database is durable when BOT_DATA_DIR points at persistent
# storage. Google Sheets remains the off-host backup and recovery source.

# ==================== GOOGLE SHEETS BACKUP/SYNC ====================
_google_sheets_stop_event = threading.Event()
_google_sheets_sync_thread = None
_google_sheets_last_hashes = {}


def _google_sheets_configured():
    """Return whether Google Sheets credentials are available.

    The Sheet ID and service-account JSON are hardcoded in this file, so
    this function simply validates that the required pieces exist before
    starting the background worker.
    """
    try:
        if not GOOGLE_SHEETS_SYNC_ENABLED:
            logger.info("Google Sheets sync is disabled by config.")
            return False
        if not GOOGLE_SHEET_ID or GOOGLE_SHEET_ID == "PASTE_GOOGLE_SHEET_ID_HERE":
            logger.info("Google Sheets sync: GOOGLE_SHEET_ID not configured.")
            return False
        if gspread is None or Credentials is None:
            logger.warning(
                "Google Sheets sync: install gspread and google-auth first "
                "(pip install gspread google-auth)."
            )
            return False
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            return True
        if GOOGLE_SERVICE_ACCOUNT_FILE and os.path.isfile(GOOGLE_SERVICE_ACCOUNT_FILE):
            return True
        logger.info(
            "Google Sheets sync: no service-account credentials available."
        )
        return False
    except Exception as exc:
        logger.error(
            f"Google Sheets config check failed: {exc}", exc_info=True
        )
        return False


def _google_sheets_authorize():
    """Create an authorized gspread client from JSON or a JSON file."""
    if gspread is None or Credentials is None:
        raise RuntimeError(
            "Install Google Sheets dependencies first: "
            "pip install gspread google-auth"
        )

    if GOOGLE_SERVICE_ACCOUNT_JSON:
        try:
            service_account_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON"
            ) from exc
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=GOOGLE_SHEETS_SCOPES,
        )
    elif GOOGLE_SERVICE_ACCOUNT_FILE:
        if not os.path.isfile(GOOGLE_SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"Service-account file not found: {GOOGLE_SERVICE_ACCOUNT_FILE}"
            )
        credentials = Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=GOOGLE_SHEETS_SCOPES,
        )
    else:
        raise RuntimeError(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_FILE"
        )

    client = gspread.authorize(credentials)
    return client.open_by_key(GOOGLE_SHEET_ID)


def _google_sheets_read_table(table_name):
    """Read one SQLite table as a JSON-safe two-dimensional snapshot."""
    if table_name not in GOOGLE_SHEETS_SYNC_TABLES:
        raise ValueError(f"Table is not allowlisted for Sheets sync: {table_name}")

    # Table names come only from the constant allowlist above; quoting them
    # keeps SQLite safe while still supporting names such as user_premium.
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            cursor = conn.execute(f'SELECT * FROM "{table_name}"')
            headers = [column[0] for column in cursor.description or ()]
            rows = cursor.fetchall()
        finally:
            conn.close()

    values = [headers]
    for row in rows:
        normalized_row = []
        for value in row:
            if value is None:
                normalized_row.append("")
            elif isinstance(value, (bytes, bytearray)):
                normalized_row.append(value.decode("utf-8", errors="replace"))
            else:
                # Google Sheets cells have a size limit.  Keep the backup
                # usable instead of allowing one oversized value to fail the
                # entire table update.
                normalized_row.append(str(value)[:49000])
        values.append(normalized_row)
    return values


def _google_sheets_snapshot_hash(values):
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _google_sheets_get_or_create_worksheet(spreadsheet, title):
    """Get a worksheet tab, creating it the first time it is needed."""
    try:
        return spreadsheet.worksheet(title)
    except Exception:
        return spreadsheet.add_worksheet(title=title, rows=100, cols=20)


def _google_sheets_write_table(spreadsheet, table_name, values):
    """Replace one worksheet tab with the latest SQLite snapshot."""
    worksheet = _google_sheets_get_or_create_worksheet(
        spreadsheet, table_name[:100]
    )
    worksheet.clear()
    if not values:
        return
    try:
        # gspread 6.x signature.
        worksheet.update(
            values,
            "A1",
            value_input_option="RAW",
        )
    except TypeError:
        # Compatibility with older gspread versions.
        worksheet.update("A1", values)


def google_sheets_sync_worker():
    """Auto-sync all important tables to Google Sheets.

    SQLite remains the primary database.  The first successful cycle
    always writes every table, so a fresh deployment pushes the entire
    database immediately.  After that, only changed tables are written
    every GOOGLE_SHEETS_SYNC_INTERVAL_SECONDS seconds.
    """
    if not _google_sheets_configured():
        logger.info(
            "Google Sheets sync is disabled until GOOGLE_SHEET_ID and "
            "service-account credentials are configured."
        )
        return

    spreadsheet = None
    last_auth_error = None
    first_sync_done = False

    while not _google_sheets_stop_event.is_set():
        try:
            if spreadsheet is None:
                spreadsheet = _google_sheets_authorize()
                last_auth_error = None
                logger.info("✅ Google Sheets sync connected successfully.")

            changed_tables = 0
            for table_name in GOOGLE_SHEETS_SYNC_TABLES:
                try:
                    values = _google_sheets_read_table(table_name)
                    snapshot_hash = _google_sheets_snapshot_hash(values)

                    # Force the first cycle to write every table.
                    if (
                        first_sync_done
                        and _google_sheets_last_hashes.get(table_name) == snapshot_hash
                    ):
                        continue

                    _google_sheets_write_table(spreadsheet, table_name, values)
                    _google_sheets_last_hashes[table_name] = snapshot_hash
                    changed_tables += 1
                except sqlite3.Error as exc:
                    logger.error(
                        "Could not read table %s for Google Sheets sync: %s",
                        table_name,
                        exc,
                    )
                except Exception as exc:
                    logger.error(
                        "Could not sync table %s to Google Sheets: %s",
                        table_name,
                        exc,
                        exc_info=True,
                    )
                    # Re-authorize on the next cycle for expired/revoked
                    # credentials or a deleted spreadsheet.
                    spreadsheet = None
                    break

            if changed_tables:
                logger.info(
                    "Google Sheets sync updated %s changed table(s).",
                    changed_tables,
                )

            if spreadsheet is not None and not first_sync_done:
                first_sync_done = True
                logger.info(
                    "✅ Google Sheets initial full sync completed "
                    f"({len(GOOGLE_SHEETS_SYNC_TABLES)} tables)."
                )
        except Exception as exc:
            if str(exc) != last_auth_error:
                logger.error("Google Sheets sync unavailable: %s", exc)
                last_auth_error = str(exc)
            spreadsheet = None
            first_sync_done = False
            # Auth/config errors should not hammer the API every 2 seconds.
            _google_sheets_stop_event.wait(30)
            continue

        _google_sheets_stop_event.wait(GOOGLE_SHEETS_SYNC_INTERVAL_SECONDS)


def start_google_sheets_sync():
    """Start the Google Sheets auto-sync worker.

    The Sheet ID and service-account JSON are hardcoded earlier in this
    file, so the worker starts automatically as soon as the bot boots.
    """
    global _google_sheets_sync_thread
    if _google_sheets_sync_thread and _google_sheets_sync_thread.is_alive():
        logger.info("Google Sheets sync already running.")
        return
    if not _google_sheets_configured():
        logger.warning(
            "Google Sheets sync NOT started: configure GOOGLE_SHEET_ID and "
            "service-account credentials."
        )
        return
    _google_sheets_stop_event.clear()
    _google_sheets_sync_thread = threading.Thread(
        target=google_sheets_sync_worker,
        daemon=True,
        name="google-sheets-sync",
    )
    _google_sheets_sync_thread.start()
    logger.info(
        f"✅ Google Sheets auto-sync started "
        f"(interval: {GOOGLE_SHEETS_SYNC_INTERVAL_SECONDS}s, "
        f"tables: {len(GOOGLE_SHEETS_SYNC_TABLES)})."
    )


def stop_google_sheets_sync():
    """Stop the background worker during graceful shutdown."""
    _google_sheets_stop_event.set()


# ==================== APP.PY-STYLE PRIMARY STORAGE ====================
# The older gspread/SQLite-backup implementation above is intentionally
# shadowed by this REST-based implementation. Runtime SQL is only a transient
# compatibility cache; Google Sheets is loaded first and written back as the
# durable source of truth.
google_sheet_data_loaded = False
google_sheet_last_error = ""
google_sheet_last_signature = None
google_sheet_last_success_at = ""
google_sheet_tabs = set()
google_sheet_tab_ids = {}
google_auth_warning_printed = False
_google_credentials = None
_google_credentials_fingerprint = None
_google_credentials_lock = threading.RLock()
_google_sheet_sync_lock = threading.RLock()
GOOGLE_SHEET_USER_TAB = "Users"


def _google_sheets_configured():
    return bool(
        GOOGLE_SHEETS_SYNC_ENABLED
        and GOOGLE_SHEET_ID
        and GOOGLE_SERVICE_ACCOUNT_JSON
    )


def _read_service_account_info():
    raw = GOOGLE_SERVICE_ACCOUNT_JSON
    if not raw:
        return None
    try:
        candidate = raw.strip()
        if len(candidate) < 4096 and "\n" not in candidate and os.path.isfile(candidate):
            with open(candidate, "r", encoding="utf-8") as handle:
                candidate = handle.read().strip()

        if candidate.startswith('"'):
            unwrapped = json.loads(candidate)
            if isinstance(unwrapped, str):
                candidate = unwrapped.strip()

        try:
            info = json.loads(candidate)
        except json.JSONDecodeError:
            padding = "=" * ((4 - len(candidate) % 4) % 4)
            decoded = base64.b64decode(candidate + padding).decode("utf-8")
            info = json.loads(decoded)

        if isinstance(info, str):
            info = json.loads(info)
        if not isinstance(info, dict):
            raise ValueError("credential payload is not a JSON object")
        if info.get("type") != "service_account":
            raise ValueError("credential type is not service_account")
        if not info.get("client_email") or not info.get("private_key"):
            raise ValueError("credential is missing client_email or private_key")

        # Some secret managers preserve the two characters \"\\n\" instead of
        # expanding them into line breaks. google-auth expects real newlines.
        private_key = str(info["private_key"])
        if "\\n" in private_key:
            info["private_key"] = private_key.replace("\\n", "\n")
        return info
    except Exception:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON must be service-account JSON, "
            "a JSON file path, or base64-encoded service-account JSON."
        ) from None


def _google_access_token(force_refresh=False):
    global google_auth_warning_printed
    global _google_credentials, _google_credentials_fingerprint
    try:
        from google.oauth2.service_account import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        if not google_auth_warning_printed:
            logger.error("Google Sheets needs google-auth.")
            google_auth_warning_printed = True
        return None

    fingerprint = hashlib.sha256(
        GOOGLE_SERVICE_ACCOUNT_JSON.encode("utf-8")
    ).hexdigest()
    with _google_credentials_lock:
        if (
            _google_credentials is None
            or _google_credentials_fingerprint != fingerprint
        ):
            _google_credentials = Credentials.from_service_account_info(
                _read_service_account_info(), scopes=GOOGLE_SHEET_SCOPES
            )
            _google_credentials_fingerprint = fingerprint
        if force_refresh or not _google_credentials.valid:
            _google_credentials.refresh(Request())
        return _google_credentials.token


def _rewind_google_request_streams(kwargs):
    def rewind(value):
        if hasattr(value, "seek"):
            value.seek(0)
        elif isinstance(value, (tuple, list)):
            for item in value:
                rewind(item)

    rewind(kwargs.get("data"))
    files = kwargs.get("files")
    if isinstance(files, dict):
        for value in files.values():
            rewind(value)


def _google_request(method, url, token, **kwargs):
    request_headers = dict(kwargs.pop("headers", {}) or {})
    timeout = kwargs.pop("timeout", 30)

    def send(access_token):
        headers = dict(request_headers)
        headers["Authorization"] = f"Bearer {access_token}"
        return requests.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )

    response = send(token)
    if response.status_code == 401:
        refreshed_token = _google_access_token(force_refresh=True)
        if refreshed_token:
            _rewind_google_request_streams(kwargs)
            response = send(refreshed_token)
    if not response.ok:
        raise RuntimeError(
            f"Google API {response.status_code}: {response.text[:300]}"
        )
    return response


def _google_api(method, url, token, payload=None, params=None):
    response = _google_request(
        method,
        url,
        token,
        headers={"Content-Type": "application/json"},
        json=payload,
        params=params,
    )
    return response.json() if response.content else {}


def _google_drive_upload(local_path, existing_file_id="", display_name=None):
    """Back up one hosted source file to the configured Drive folder."""
    if not _google_sheets_configured():
        logger.error(
            "Google Drive backup skipped: Sheets/Drive credentials are not configured."
        )
        return ""
    if not os.path.isfile(local_path):
        logger.error(
            "Google Drive backup skipped: local source file is missing: %s",
            local_path,
        )
        return ""
    token = _google_access_token()
    if not token:
        logger.error(
            "Google Drive backup skipped: could not obtain a service-account token."
        )
        return ""
    try:
        file_name = display_name or os.path.basename(local_path)
        if existing_file_id:
            try:
                with open(local_path, "rb") as handle:
                    response = _google_request(
                        "PATCH",
                        "https://www.googleapis.com/upload/drive/v3/files/"
                        f"{existing_file_id}",
                        token,
                        params={"uploadType": "media"},
                        headers={"Content-Type": "application/octet-stream"},
                        data=handle,
                        timeout=60,
                    )
            except RuntimeError as exc:
                # A removed/inaccessible old ID should not permanently block a
                # new backup; create a replacement and save its new ID.
                if "Google API 404:" not in str(exc):
                    raise
                existing_file_id = ""
        if not existing_file_id:
            metadata = {"name": file_name}
            if GOOGLE_DRIVE_FOLDER_ID:
                metadata["parents"] = [GOOGLE_DRIVE_FOLDER_ID]
            with open(local_path, "rb") as handle:
                response = _google_request(
                    "POST",
                    "https://www.googleapis.com/upload/drive/v3/files",
                    token,
                    params={"uploadType": "multipart", "fields": "id"},
                    files={
                        "metadata": (
                            "metadata",
                            json.dumps(metadata),
                            "application/json",
                        ),
                        "file": (
                            file_name,
                            handle,
                            "application/octet-stream",
                        ),
                    },
                    timeout=60,
                )
        file_id = str(response.json().get("id") or existing_file_id or "")
        if not file_id:
            raise RuntimeError("Google Drive upload succeeded without returning a file ID.")
        if existing_file_id and GOOGLE_DRIVE_FOLDER_ID:
            file_url = (
                "https://www.googleapis.com/drive/v3/files/"
                f"{existing_file_id}"
            )
            current = _google_api(
                "GET",
                file_url,
                token,
                params={"fields": "id,parents"},
            )
            parents = [
                str(parent) for parent in current.get("parents", []) if parent
            ]
            if GOOGLE_DRIVE_FOLDER_ID not in parents:
                move_params = {
                    "addParents": GOOGLE_DRIVE_FOLDER_ID,
                    "fields": "id,parents",
                }
                if parents:
                    move_params["removeParents"] = ",".join(parents)
                _google_api(
                    "PATCH",
                    file_url,
                    token,
                    payload={},
                    params=move_params,
                )
        return file_id
    except Exception as exc:
        logger.error("Google Drive backup failed for %s: %s", local_path, exc)
        return ""


def _google_drive_download(file_id, destination_path):
    if not file_id or not _google_sheets_configured():
        return False
    token = _google_access_token()
    if not token:
        return False
    try:
        response = _google_request(
            "GET",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            token,
            params={"alt": "media"},
            timeout=60,
        )
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        temporary_path = destination_path + ".restore.tmp"
        try:
            with open(temporary_path, "wb") as handle:
                handle.write(response.content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, destination_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        return True
    except Exception as exc:
        logger.error("Google Drive restore failed for %s: %s", file_id, exc)
        return False


def _google_drive_delete(file_id):
    if not file_id or not _google_sheets_configured():
        return True
    token = _google_access_token()
    if not token:
        return False
    try:
        response = _google_request(
            "DELETE",
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            token,
            timeout=30,
        )
        return response.status_code in (200, 204, 404)
    except Exception as exc:
        if "Google API 404:" in str(exc):
            return True
        logger.error("Google Drive backup delete failed: %s", exc)
        return False


def _backup_hosted_file(user_id, file_name, file_type):
    existing_file_id = ""
    with DB_LOCK:
        connection = get_db_connection()
        try:
            row = connection.execute(
                "SELECT drive_file_id FROM hosted_bot_backups "
                "WHERE user_id = ? AND file_name = ?",
                (user_id, file_name),
            ).fetchone()
            existing_file_id = str(row[0]) if row and row[0] else ""
        finally:
            connection.close()
    local_path = os.path.join(get_user_folder(user_id), file_name)
    drive_file_id = _google_drive_upload(
        local_path,
        existing_file_id=existing_file_id,
        display_name=f"{user_id}_{os.path.basename(file_name)}",
    )
    saved_file_id = drive_file_id or existing_file_id
    backup_pending = 0 if drive_file_id else 1
    with DB_LOCK:
        connection = get_db_connection()
        try:
            connection.execute(
                """INSERT OR REPLACE INTO hosted_bot_backups
                   (user_id, file_name, file_type, drive_file_id,
                    desired_status, backup_pending)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    file_name,
                    file_type,
                    saved_file_id,
                    "active",
                    backup_pending,
                ),
            )
            connection.commit()
        finally:
            connection.close()
    if not drive_file_id:
        logger.warning(
            "Hosted file %s/%s is queued for Drive backup retry.",
            user_id,
            file_name,
        )
    else:
        logger.info(
            "Hosted file backup saved to Google Drive for %s/%s%s.",
            user_id,
            file_name,
            " in the configured shared folder"
            if GOOGLE_DRIVE_FOLDER_ID else " in the service-account Drive",
        )


def _ensure_pending_hosted_file_backups(limit=5):
    """Retry files whose Drive upload did not return a durable file ID."""
    if not _google_sheets_configured() or not google_sheet_data_loaded:
        return 0
    with DB_LOCK:
        connection = get_db_connection()
        try:
            pending = connection.execute(
                """SELECT files.user_id, files.file_name, files.file_type,
                          COALESCE(backups.drive_file_id, ''),
                          CAST(COALESCE(backups.backup_pending, 0) AS INTEGER)
                   FROM user_files AS files
                   LEFT JOIN hosted_bot_backups AS backups
                     ON backups.user_id = files.user_id
                    AND backups.file_name = files.file_name
                   WHERE COALESCE(backups.drive_file_id, '') = ''
                      OR CAST(COALESCE(backups.backup_pending, 0) AS INTEGER) = 1
                   ORDER BY files.upload_time ASC
                   LIMIT ?""",
                (max(1, int(limit)),),
            ).fetchall()
        finally:
            connection.close()

    completed = 0
    for user_id, file_name, file_type, existing_file_id, _pending_flag in pending:
        safe_name = os.path.basename(str(file_name).replace("\\", "/"))
        if not safe_name or safe_name != str(file_name):
            logger.error(
                "Drive backup retry skipped unsafe filename for user %s: %r",
                user_id,
                file_name,
            )
            continue
        local_path = os.path.join(get_user_folder(int(user_id)), safe_name)
        if not os.path.isfile(local_path):
            continue
        file_id = _google_drive_upload(
            local_path,
            existing_file_id=str(existing_file_id or ""),
            display_name=f"{user_id}_{safe_name}",
        )
        if not file_id:
            with DB_LOCK:
                connection = get_db_connection()
                try:
                    connection.execute(
                        """INSERT OR REPLACE INTO hosted_bot_backups
                           (user_id, file_name, file_type, drive_file_id,
                            desired_status, backup_pending)
                           VALUES (?, ?, ?, ?, COALESCE(
                               (SELECT desired_status FROM hosted_bot_backups
                                WHERE user_id = ? AND file_name = ?), 'active'), 1)""",
                        (
                            user_id,
                            safe_name,
                            file_type,
                            existing_file_id or "",
                            user_id,
                            safe_name,
                        ),
                    )
                    connection.commit()
                finally:
                    connection.close()
            continue
        with DB_LOCK:
            connection = get_db_connection()
            try:
                connection.execute(
                    """INSERT OR REPLACE INTO hosted_bot_backups
                       (user_id, file_name, file_type, drive_file_id,
                        desired_status, backup_pending)
                       VALUES (?, ?, ?, ?, COALESCE(
                           (SELECT desired_status FROM hosted_bot_backups
                            WHERE user_id = ? AND file_name = ?), 'active'), 0)""",
                    (
                        user_id,
                        safe_name,
                        file_type,
                        file_id,
                        user_id,
                        safe_name,
                    ),
                )
                connection.commit()
            finally:
                connection.close()
        completed += 1
        logger.info("Drive backup retry succeeded for %s/%s.", user_id, safe_name)
    return completed


def _remove_hosted_backup(user_id, file_name):
    with DB_LOCK:
        connection = get_db_connection()
        try:
            row = connection.execute(
                "SELECT drive_file_id FROM hosted_bot_backups "
                "WHERE user_id = ? AND file_name = ?",
                (user_id, file_name),
            ).fetchone()
            connection.execute(
                "DELETE FROM hosted_bot_backups "
                "WHERE user_id = ? AND file_name = ?",
                (user_id, file_name),
            )
            connection.commit()
        finally:
            connection.close()
    # Keep the Drive copy until the updated Sheets snapshot has been saved.
    # If Sheets is temporarily unavailable, the old row can still restore the
    # source file rather than leaving a visible but unrecoverable file record.
    return str(row[0]) if row and row[0] else ""


def restore_hosted_files_from_drive():
    """Restore source files that are missing after a fresh deployment."""
    if not _google_sheets_configured():
        logger.warning("Drive restore skipped: Google Sheets/Drive is not configured.")
        return {"restored": 0, "failed": 0, "skipped": 0}
    with DB_LOCK:
        connection = get_db_connection()
        try:
            backups = connection.execute(
                "SELECT user_id, file_name, drive_file_id FROM hosted_bot_backups"
            ).fetchall()
        finally:
            connection.close()
    restored = failed = skipped = 0
    for user_id, file_name, drive_file_id in backups:
        try:
            normalized_user_id = int(user_id)
            original_name = str(file_name or "")
            safe_name = os.path.basename(original_name.replace("\\", "/"))
            if not safe_name or safe_name != original_name:
                skipped += 1
                logger.error(
                    "Drive restore skipped unsafe filename for user %s: %r",
                    user_id,
                    file_name,
                )
                continue
            destination = os.path.join(
                get_user_folder(normalized_user_id), safe_name
            )
            if os.path.isfile(destination):
                continue
            if not drive_file_id:
                if _restore_one_hosted_file_from_drive(
                    normalized_user_id, safe_name
                ):
                    restored += 1
                else:
                    failed += 1
                    logger.error(
                        "Drive restore unavailable for user %s, file %s: "
                        "no stored backup ID or matching Drive file; "
                        "the file record was kept.",
                        user_id,
                        safe_name,
                    )
            elif _google_drive_download(str(drive_file_id), destination):
                restored += 1
                logger.info(
                    "Restored user file from Drive: %s/%s",
                    normalized_user_id,
                    safe_name,
                )
            else:
                failed += 1
        except Exception:
            failed += 1
            logger.exception(
                "Drive restore failed for user %s, file %r; continuing "
                "with the remaining backup records.",
                user_id,
                file_name,
            )
    logger.info(
        "Drive restore finished: %s restored, %s failed, %s skipped.",
        restored, failed, skipped,
    )
    return {"restored": restored, "failed": failed, "skipped": skipped}


def _restore_one_hosted_file_from_drive(user_id, file_name):
    """Restore one missing source file without changing its database record."""
    original_name = str(file_name or "")
    safe_name = os.path.basename(original_name.replace("\\", "/"))
    if not safe_name or safe_name != original_name:
        logger.error(
            "On-demand Drive restore skipped unsafe filename for user %s: %r",
            user_id,
            file_name,
        )
        return False

    destination = os.path.join(get_user_folder(int(user_id)), safe_name)
    if os.path.isfile(destination):
        return True

    with DB_LOCK:
        connection = get_db_connection()
        try:
            row = connection.execute(
                "SELECT drive_file_id FROM hosted_bot_backups "
                "WHERE user_id = ? AND file_name = ?",
                (user_id, safe_name),
            ).fetchone()
        finally:
            connection.close()

    drive_file_id = str(row[0]) if row and row[0] else ""
    if not drive_file_id:
        # A previous Drive upload may have completed even if the process
        # stopped before its file ID was written to the durable database.
        # Search only for the exact app-generated backup name in that case.
        try:
            token = _google_access_token()
            if token:
                backup_name = f"{int(user_id)}_{safe_name}"
                escaped_name = backup_name.replace("\\", "\\\\").replace(
                    "'", "\\'"
                )
                result = _google_api(
                    "GET",
                    "https://www.googleapis.com/drive/v3/files",
                    token,
                    params={
                        "q": f"name = '{escaped_name}' and trashed = false",
                        "pageSize": 10,
                        "orderBy": "modifiedTime desc",
                        "fields": "files(id,name,modifiedTime)",
                    },
                )
                matches = [
                    item for item in result.get("files", [])
                    if item.get("name") == backup_name and item.get("id")
                ]
                if matches:
                    drive_file_id = str(matches[0]["id"])
                    if len(matches) > 1:
                        logger.warning(
                            "Found %s Drive backups named %s; using the "
                            "most recently modified one.",
                            len(matches),
                            backup_name,
                        )
        except Exception as exc:
            logger.warning(
                "Could not search Drive for an unindexed backup of %s/%s: %s",
                user_id,
                safe_name,
                exc,
            )

        if not drive_file_id:
            logger.warning(
                "On-demand restore unavailable for %s/%s: no Drive backup "
                "was found; the user_files record is being kept.",
                user_id,
                safe_name,
            )
            return False

        with DB_LOCK:
            connection = get_db_connection()
            try:
                file_row = connection.execute(
                    "SELECT file_type, is_stopped FROM user_files "
                    "WHERE user_id = ? AND file_name = ?",
                    (user_id, safe_name),
                ).fetchone()
                file_type = (
                    str(file_row[0] or "")
                    if file_row else os.path.splitext(safe_name)[1].lstrip(".")
                )
                desired_status = (
                    "stopped" if file_row and file_row[1] else "active"
                )
                connection.execute(
                    """INSERT INTO hosted_bot_backups
                       (user_id, file_name, file_type, drive_file_id,
                        desired_status, backup_pending)
                       VALUES (?, ?, ?, ?, ?, 0)
                       ON CONFLICT(user_id, file_name) DO UPDATE SET
                           drive_file_id = excluded.drive_file_id,
                           backup_pending = 0""",
                    (
                        user_id,
                        safe_name,
                        file_type,
                        drive_file_id,
                        desired_status,
                    ),
                )
                connection.commit()
            finally:
                connection.close()

    if _google_drive_download(drive_file_id, destination):
        logger.info(
            "Restored missing hosted file from Drive: %s/%s",
            user_id,
            safe_name,
        )
        return True

    logger.error(
        "On-demand Drive restore failed for %s/%s; "
        "the user_files record is being kept.",
        user_id,
        safe_name,
    )
    return False


def _retry_missing_hosted_file_restores(limit=5):
    """Retry individual Drive downloads that failed during startup."""
    if not _google_sheets_configured() or not google_sheet_data_loaded:
        return 0
    with DB_LOCK:
        connection = get_db_connection()
        try:
            backups = connection.execute(
                """SELECT user_id, file_name, drive_file_id
                   FROM hosted_bot_backups
                   WHERE COALESCE(drive_file_id, '') != ''
                   ORDER BY user_id, file_name"""
            ).fetchall()
        finally:
            connection.close()

    restored = 0
    attempted = 0
    for user_id, file_name, drive_file_id in backups:
        safe_name = os.path.basename(str(file_name).replace("\\", "/"))
        if not safe_name or safe_name != str(file_name):
            continue
        destination = os.path.join(get_user_folder(int(user_id)), safe_name)
        if os.path.isfile(destination):
            continue
        if attempted >= max(1, int(limit)):
            break
        attempted += 1
        if _google_drive_download(str(drive_file_id), destination):
            restored += 1
            logger.info("Drive retry restored file %s/%s.", user_id, safe_name)
    return restored


def _ensure_google_sheet_tabs(token):
    global google_sheet_tabs, google_sheet_tab_ids
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
    data = _google_api(
        "GET", base_url, token, params={"fields": "sheets.properties"}
    )
    def refresh_tabs(response):
        if not isinstance(response, dict):
            raise TypeError(
                "Google Sheets spreadsheet metadata must be a dict, "
                f"got {type(response).__name__}"
            )
        sheet_items = response.get("sheets", [])
        if not isinstance(sheet_items, list):
            raise TypeError(
                "Google Sheets metadata field 'sheets' must be a list, "
                f"got {type(sheet_items).__name__}"
            )
        google_sheet_tab_ids = {}
        for item in sheet_items:
            if not isinstance(item, dict):
                raise TypeError(
                    "Google Sheets metadata contains a non-object sheet entry "
                    f"({type(item).__name__})"
                )
            properties = item.get("properties", {})
            if not isinstance(properties, dict):
                raise TypeError(
                    "Google Sheets sheet properties must be a dict, "
                    f"got {type(properties).__name__}"
                )
            title = properties.get("title")
            if title:
                google_sheet_tab_ids[title] = properties.get("sheetId")
        google_sheet_tabs = set(google_sheet_tab_ids)
        return google_sheet_tabs, google_sheet_tab_ids

    google_sheet_tabs, google_sheet_tab_ids = refresh_tabs(data)
    missing = [
        name for name in GOOGLE_SHEETS_SYNC_TABLES
        if name not in google_sheet_tabs
    ]
    if GOOGLE_SHEET_USER_TAB not in google_sheet_tabs:
        missing.append(GOOGLE_SHEET_USER_TAB)
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
        refreshed = _google_api(
            "GET", base_url, token, params={"fields": "sheets.properties"}
        )
        google_sheet_tabs, google_sheet_tab_ids = refresh_tabs(refreshed)


def _sheet_rows(token, sheet_name):
    if sheet_name not in GOOGLE_SHEETS_SYNC_TABLES:
        raise ValueError(f"Unknown Google Sheets data tab: {sheet_name!r}")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{GOOGLE_SHEET_ID}/values/{sheet_name}"
    )
    data = _google_api("GET", url, token)
    if not isinstance(data, dict):
        raise TypeError(
            f"Google Sheets response for tab {sheet_name!r} "
            f"must be a dict, got {type(data).__name__}"
        )
    values = data.get("values")
    if values is None or values == []:
        return None
    if not isinstance(values, list):
        raise TypeError(
            f"Google Sheets values for tab {sheet_name!r} must be a list, "
            f"got {type(values).__name__}"
        )
    if not isinstance(values[0], list):
        raise TypeError(
            f"Google Sheets header row for tab {sheet_name!r} must be a list, "
            f"got {type(values[0]).__name__}"
        )

    headers = []
    for column_number, value in enumerate(values[0], start=1):
        if value is None:
            header = ""
        elif isinstance(value, (str, int, float, bool)):
            header = str(value).strip()
        else:
            raise TypeError(
                f"Invalid header value in tab {sheet_name!r}, "
                f"column {column_number}: {type(value).__name__}"
            )
        if not header:
            raise ValueError(
                f"Blank header in tab {sheet_name!r}, column {column_number}"
            )
        if header in headers:
            raise ValueError(
                f"Duplicate header {header!r} in tab {sheet_name!r}"
            )
        headers.append(header)

    expected_headers = set(_runtime_table_headers(sheet_name))
    missing_headers = expected_headers.difference(headers)
    if not expected_headers:
        raise ValueError(
            f"No local SQLite schema found for Google Sheets tab {sheet_name!r}"
        )
    if missing_headers:
        raise ValueError(
            f"Google Sheets tab {sheet_name!r} is missing required column(s): "
            f"{', '.join(sorted(missing_headers))}"
        )

    rows = []
    skipped_rows = 0
    for row_number, raw_row in enumerate(values[1:], start=2):
        if not isinstance(raw_row, list):
            skipped_rows += 1
            logger.warning(
                "Skipping malformed Google Sheets row %s in tab %s: "
                "expected a list, got %s.",
                row_number,
                sheet_name,
                type(raw_row).__name__,
            )
            continue
        if len(raw_row) > len(headers):
            skipped_rows += 1
            logger.warning(
                "Skipping malformed Google Sheets row %s in tab %s: "
                "expected at most %s columns, got %s.",
                row_number,
                sheet_name,
                len(headers),
                len(raw_row),
            )
            continue
        if len(raw_row) < len(headers):
            # The Sheets Values API omits trailing blank cells by default.
            # Pad those cells instead of dropping an otherwise valid record.
            logger.info(
                "Google Sheets row %s in tab %s has %s trailing blank "
                "column(s); padding them during restore.",
                row_number,
                sheet_name,
                len(headers) - len(raw_row),
            )
            raw_row = raw_row + [""] * (len(headers) - len(raw_row))

        normalized_row = []
        invalid_cell = False
        for column_number, value in enumerate(raw_row, start=1):
            if value is None:
                normalized_row.append("")
            elif isinstance(value, (str, int, float, bool)):
                normalized_row.append(str(value))
            else:
                logger.warning(
                    "Skipping malformed Google Sheets row %s in tab %s: "
                    "column %s contains %s, not a scalar cell value.",
                    row_number,
                    sheet_name,
                    column_number,
                    type(value).__name__,
                )
                invalid_cell = True
                break
        if invalid_cell:
            skipped_rows += 1
            continue
        if not any(value.strip() for value in normalized_row):
            continue
        rows.append(dict(zip(headers, normalized_row)))

    if skipped_rows:
        logger.warning(
            "Google Sheets tab %s load skipped %s malformed row(s).",
            sheet_name,
            skipped_rows,
        )
    # Never interpret a header-only or wholly malformed tab as an instruction
    # to erase an existing local table.
    return rows or None


def _runtime_table_headers(table_name):
    with DB_LOCK:
        connection = get_db_connection()
        try:
            return [
                row[1]
                for row in connection.execute(
                    f'PRAGMA table_info("{table_name}")'
                ).fetchall()
            ]
        finally:
            connection.close()


def _runtime_table_matrix(table_name):
    headers = _runtime_table_headers(table_name)
    with DB_LOCK:
        connection = get_db_connection()
        try:
            rows = connection.execute(
                f'SELECT * FROM "{table_name}"'
            ).fetchall()
        finally:
            connection.close()

    matrix = [headers]
    for row in rows:
        matrix.append([
            "" if value is None
            else value.decode("utf-8", errors="replace")
            if isinstance(value, (bytes, bytearray))
            else str(value)[:49000]
            for value in row
        ])
    return matrix


def _restore_runtime_table(table_name, rows, connection=None):
    if rows is None:
        return
    if not isinstance(rows, list):
        raise TypeError(
            f"Rows for table {table_name!r} must be a list, "
            f"got {type(rows).__name__}"
        )
    owns_connection = connection is None
    with DB_LOCK:
        if owns_connection:
            connection = get_db_connection()
        try:
            metadata = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            headers = [row[1] for row in metadata]
            column_types = {row[1]: str(row[2]).upper() for row in metadata}
            not_null_columns = {
                row[1]: bool(row[3]) for row in metadata
            }
            if not headers:
                return
            connection.execute(f'DELETE FROM "{table_name}"')
            quoted_columns = ", ".join(f'"{name}"' for name in headers)
            placeholders = ", ".join("?" for _ in headers)
            statement = (
                f'INSERT INTO "{table_name}" ({quoted_columns}) '
                f"VALUES ({placeholders})"
            )
            for row_number, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    logger.warning(
                        "Skipping malformed row %s for table %s during "
                        "Sheets restore: expected a mapping, got %s.",
                        row_number,
                        table_name,
                        type(row).__name__,
                    )
                    continue
                values = []
                for name in headers:
                    value = row.get(name, "")
                    if value is None or value == "":
                        # SQLite's PRAGMA notnull flag is an integer, not an
                        # iterable. Use it as a boolean directly; blank cells
                        # in required columns become "", nullable ones None.
                        values.append(
                            "" if not_null_columns.get(name, False) else None
                        )
                        continue
                    data_type = column_types.get(name, "")
                    try:
                        if "INT" in data_type:
                            value = int(float(value))
                        elif any(kind in data_type for kind in ("REAL", "FLOA", "DOUB")):
                            value = float(value)
                    except (TypeError, ValueError):
                        pass
                    values.append(value)
                try:
                    connection.execute(statement, values)
                except sqlite3.Error as exc:
                    logger.warning(
                        "Skipping malformed %s row during Sheets restore: %s",
                        table_name,
                        exc,
                    )
            if owns_connection:
                connection.commit()
        finally:
            if owns_connection:
                connection.close()


def _google_sheets_read_table(table_name):
    if table_name not in GOOGLE_SHEETS_SYNC_TABLES:
        raise ValueError(f"Table is not allowlisted for Sheets sync: {table_name}")
    return _runtime_table_matrix(table_name)


def _google_users_matrix():
    """Build one human-friendly worksheet containing each user's full view."""
    headers = [
        "User ID", "Name", "Username", "Joined At", "Status", "Admin",
        "Banned", "Balance (BDT)", "Subscription Expiry", "Premium Plan ID",
        "Files", "Running Files", "File Limit", "Host Time (hours)",
        "Referral Count", "Action Count",
    ]
    with DB_LOCK:
        connection = get_db_connection()
        try:
            profiles = {
                int(row[0]): {
                    "name": row[1] or "Unknown",
                    "username": row[2] or "@unknown",
                    "joined": row[3] or "",
                }
                for row in connection.execute(
                    "SELECT user_id, name, username, joined_at FROM user_profiles"
                ).fetchall()
            }
            user_ids = set(profiles)
            for table_name, column_name in (
                ("active_users", "user_id"),
                ("admins", "user_id"),
                ("subscriptions", "user_id"),
                ("user_premium", "user_id"),
                ("user_files", "user_id"),
                ("user_balances", "user_id"),
                ("banned_users", "user_id"),
                ("referrals", "referrer_id"),
                ("user_file_action_quota", "user_id"),
            ):
                user_ids.update(
                    int(row[0])
                    for row in connection.execute(
                        f'SELECT DISTINCT "{column_name}" FROM "{table_name}"'
                    ).fetchall()
                    if row[0] is not None
                )

            balances = dict(connection.execute(
                "SELECT user_id, balance FROM user_balances"
            ).fetchall())
            subscriptions = dict(connection.execute(
                "SELECT user_id, expiry FROM subscriptions"
            ).fetchall())
            premium = {
                int(row[0]): (row[1], row[2])
                for row in connection.execute(
                    "SELECT user_id, plan_id, expiry FROM user_premium"
                ).fetchall()
            }
            files = {}
            for row in connection.execute(
                "SELECT user_id, is_stopped FROM user_files"
            ).fetchall():
                owner_id = int(row[0])
                total, stopped = files.get(owner_id, (0, 0))
                files[owner_id] = (total + 1, stopped + (1 if row[1] else 0))
            referral_counts = dict(connection.execute(
                """SELECT referrer_id, COUNT(*) FROM referrals
                   WHERE status = 'verified' GROUP BY referrer_id"""
            ).fetchall())
            action_counts = dict(connection.execute(
                "SELECT user_id, action_count FROM user_file_action_quota"
            ).fetchall())
            admin_user_ids = {
                int(row[0]) for row in connection.execute(
                    "SELECT user_id FROM admins"
                ).fetchall()
            }
            banned_user_ids = {
                int(row[0]) for row in connection.execute(
                    "SELECT user_id FROM banned_users"
                ).fetchall()
            }
        finally:
            connection.close()

    for user in all_users:
        try:
            user_id = int(user["id"])
        except (KeyError, TypeError, ValueError):
            continue
        user_ids.add(user_id)
        profiles.setdefault(user_id, {
            "name": user.get("name") or "Unknown",
            "username": user.get("username") or "@unknown",
            "joined": user.get("joined") or "",
        })

    rows = [headers]
    for user_id in sorted(user_ids):
        profile = profiles.get(user_id, {})
        plan_id, premium_expiry = premium.get(user_id, ("", ""))
        subscription_expiry = subscriptions.get(user_id, "")
        total_files, stopped_files = files.get(user_id, (0, 0))
        running_files = max(0, total_files - stopped_files)
        if user_id in banned_user_ids:
            status = "Banned"
        elif user_id == OWNER_ID:
            status = "Owner"
        elif user_id in admin_user_ids or user_id in admin_list:
            status = "Admin"
        elif premium_expiry:
            status = "Premium"
        else:
            status = "Free"
        try:
            file_limit = get_user_file_limit(user_id)
            file_limit = (
                "Unlimited" if file_limit == float("inf") else str(file_limit)
            )
        except Exception:
            file_limit = ""
        try:
            host_time = get_user_host_time(user_id)
            host_time = "Unlimited" if host_time == float("inf") else str(host_time)
        except Exception:
            host_time = ""
        rows.append([
            user_id,
            profile.get("name", "Unknown"),
            profile.get("username", "@unknown"),
            profile.get("joined", ""),
            status,
            "Yes" if user_id in admin_user_ids or user_id in admin_list
            or user_id == OWNER_ID else "No",
            "Yes" if user_id in banned_user_ids else "No",
            f"{float(balances.get(user_id, 0) or 0):.2f}",
            premium_expiry or subscription_expiry or "",
            plan_id or "",
            total_files,
            running_files,
            file_limit,
            host_time,
            referral_counts.get(user_id, 0),
            action_counts.get(user_id, 0),
        ])
    return rows


def _format_google_sheets(token, tab_matrices):
    """Apply a readable header, frozen row, and automatic column sizing."""
    requests_payload = []
    for title, matrix in tab_matrices.items():
        sheet_id = google_sheet_tab_ids.get(title)
        if sheet_id is None:
            continue
        column_count = max(
            1, max((len(row) for row in matrix), default=1)
        )
        requests_payload.extend([
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": column_count,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {
                                "red": 0.10, "green": 0.25, "blue": 0.45
                            },
                            "textFormat": {
                                "foregroundColor": {
                                    "red": 1, "green": 1, "blue": 1
                                },
                                "bold": True,
                            },
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": (
                        "userEnteredFormat(backgroundColor,textFormat,"
                        "horizontalAlignment)"
                    ),
                }
            },
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": column_count,
                    }
                }
            },
        ])
    if requests_payload:
        base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
        _google_api(
            "POST",
            f"{base_url}:batchUpdate",
            token,
            {"requests": requests_payload},
        )


def _google_sheets_snapshot_hash(values):
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sync_to_google_sheets_unlocked(force=False):
    global google_sheet_last_signature, google_sheet_last_error
    global google_sheet_last_success_at
    if not _google_sheets_configured() or not google_sheet_data_loaded:
        if not _google_sheets_configured():
            google_sheet_last_error = (
                "Google Sheets is not configured. Set GOOGLE_SHEET_ID and "
                "GOOGLE_SERVICE_ACCOUNT_JSON."
            )
        elif not google_sheet_data_loaded:
            google_sheet_last_error = "Google Sheets data is not loaded yet."
        return False
    try:
        rows_by_tab = {
            name: _google_sheets_read_table(name)
            for name in GOOGLE_SHEETS_SYNC_TABLES
        }
        rows_by_tab[GOOGLE_SHEET_USER_TAB] = _google_users_matrix()
        signature = hashlib.sha256(
            json.dumps(
                rows_by_tab, ensure_ascii=False, sort_keys=True
            ).encode("utf-8")
        ).hexdigest()
        if not force and signature == google_sheet_last_signature:
            return True
        token = _google_access_token()
        if not token:
            return False
        _ensure_google_sheet_tabs(token)
        base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{GOOGLE_SHEET_ID}"
        # Write the new complete snapshot before clearing obsolete trailing
        # rows. Clearing first meant a timeout between these requests could
        # leave the spreadsheet empty and destroy the only remote copy.
        _google_api(
            "POST",
            f"{base_url}/values:batchUpdate",
            token,
            {
                "valueInputOption": "RAW",
                "data": [
                    {
                        "range": f"{name}!A1",
                        "values": rows_by_tab[name],
                    }
                    for name in rows_by_tab
                ],
            },
        )
        _google_api(
            "POST",
            f"{base_url}/values:batchClear",
            token,
            {
                "ranges": [
                    f"{name}!A{len(values) + 1}:ZZ"
                    for name, values in rows_by_tab.items()
                ]
            },
        )
        _format_google_sheets(token, rows_by_tab)
        google_sheet_last_signature = signature
        google_sheet_last_error = ""
        google_sheet_last_success_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return True
    except Exception as exc:
        google_sheet_last_error = str(exc)
        logger.error("Google Sheets sync failed: %s", exc)
        return False


def sync_to_google_sheets(force=False):
    """Serialize snapshots so an older concurrent sync cannot undo a change."""
    with _google_sheet_sync_lock:
        return _sync_to_google_sheets_unlocked(force=force)


def trigger_google_sheets_sync():
    """Schedule a debounced sync after a meaningful runtime DB change."""
    if not _google_sheets_configured() or not google_sheet_data_loaded:
        return
    threading.Thread(
        target=lambda: (time.sleep(0.5), sync_to_google_sheets()),
        daemon=True,
        name="google-sheets-sync-trigger",
    ).start()


def google_sheets_status_text():
    """Return a short, actionable sync status for the GX admin panel."""
    if not _google_sheets_configured():
        state = "❌ NOT CONFIGURED"
    elif google_sheet_last_error:
        state = "❌ ERROR"
    elif google_sheet_last_success_at:
        state = "✅ SUCCESS"
    elif google_sheet_data_loaded:
        state = "⏳ READY / WAITING FOR FIRST SYNC"
    else:
        state = "⏳ STARTING"
    lines = [
        "📊 *GOOGLE SHEETS SYNC STATUS*",
        "━━━━━━━━━━━━━━━━━",
        "",
        f"🔰 *Status:* {state}",
        f"📄 *Sheet ID:* {'Configured' if GOOGLE_SHEET_ID else 'Missing'}",
        f"🔐 *Credentials:* {'Configured' if GOOGLE_SERVICE_ACCOUNT_JSON else 'Missing'}",
        f"💾 *Data loaded:* {'Yes' if google_sheet_data_loaded else 'No'}",
    ]
    if google_sheet_last_success_at:
        lines.append(f"✅ *Last success:* {google_sheet_last_success_at}")
    if google_sheet_last_error:
        lines.extend([
            "",
            "⚠️ *Last error:*",
            f"<code>{html_escape(str(google_sheet_last_error)[:1200])}</code>",
        ])
    return "\n".join(lines)


def delete_all_bot_data():
    """Delete all runtime/user data, then recreate only safe defaults.

    Owner and environment-configured admin access are intentionally restored
    after the purge so a destructive click cannot permanently lock the owner
    out of the bot.
    """
    global google_sheet_last_signature, google_sheet_last_error
    global google_sheet_last_success_at, bot_locked

    deleted_drive_backups = []
    with DB_LOCK:
        connection = get_db_connection()
        try:
            deleted_drive_backups = [
                row[0] for row in connection.execute(
                    "SELECT drive_file_id FROM hosted_bot_backups "
                    "WHERE drive_file_id IS NOT NULL AND drive_file_id != ''"
                ).fetchall()
            ]
        finally:
            connection.close()

    for drive_file_id in deleted_drive_backups:
        _google_drive_delete(drive_file_id)

    stopped_processes = 0
    for script_key, script_info in list(bot_scripts.items()):
        try:
            kill_process_tree(script_info)
            stopped_processes += 1
        except Exception as exc:
            logger.warning("Could not stop %s during full purge: %s", script_key, exc)
    bot_scripts.clear()

    with DB_LOCK:
        connection = get_db_connection()
        try:
            connection.execute("PRAGMA foreign_keys = OFF")
            tables = [
                row[0] for row in connection.execute(
                    """SELECT name FROM sqlite_master
                       WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"""
                ).fetchall()
            ]
            for table_name in tables:
                connection.execute(f'DELETE FROM "{table_name}"')
            connection.commit()
        finally:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.close()

    for entry in os.listdir(UPLOAD_BOTS_DIR):
        path = os.path.join(UPLOAD_BOTS_DIR, entry)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as exc:
            logger.warning("Could not remove uploaded data %s: %s", path, exc)

    active_users.clear()
    user_subscriptions.clear()
    user_files.clear()
    all_users.clear()
    all_files.clear()
    banned_users.clear()
    premium_plans.clear()
    user_premium_plans.clear()
    binance_plans.clear()
    user_limits.clear()
    user_upload_times.clear()
    file_stop_status.clear()
    pending_upload_modes.clear()
    payment_delete_state.clear()
    admin_list[:] = list(dict.fromkeys([ADMIN_ID, OWNER_ID]))
    admin_ids.clear()
    admin_ids.update([ADMIN_ID, OWNER_ID])
    bot_locked = False
    FREE_USER_LIMIT_SETTINGS.update({"limit": 1, "time": 1, "host_time": 1})

    # Recreate tables/default settings after clearing every row.
    init_db()
    google_sheet_last_signature = None
    google_sheet_last_error = ""
    google_sheet_last_success_at = ""
    sync_ok = (
        sync_to_google_sheets(force=True)
        if google_sheet_data_loaded else False
    )
    return {
        "tables": len(tables),
        "files": len(deleted_drive_backups),
        "processes": stopped_processes,
        "sync_ok": sync_ok,
    }


def load_google_sheet_data():
    global google_sheet_data_loaded, google_sheet_last_error
    global google_sheet_last_signature
    if not _google_sheets_configured():
        google_sheet_last_error = (
            "Set GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON."
        )
        logger.warning(
            "Google Sheets is not configured; runtime starts without "
            "persistent data."
        )
        return False
    try:
        token = _google_access_token()
        if not token:
            return False
        _ensure_google_sheet_tabs(token)
        # Fetch every tab before changing local data. A temporary API error
        # must not leave half the SQLite tables restored and half untouched.
        table_rows = {}
        for table_name in GOOGLE_SHEETS_SYNC_TABLES:
            try:
                table_rows[table_name] = _sheet_rows(token, table_name)
            except Exception:
                logger.exception(
                    "Google Sheets load failed while reading tab %s.",
                    table_name,
                )
                raise
        with DB_LOCK:
            connection = get_db_connection()
            try:
                connection.execute("BEGIN IMMEDIATE")
                for table_name, rows in table_rows.items():
                    _restore_runtime_table(
                        table_name, rows, connection=connection
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()
        google_sheet_data_loaded = True
        google_sheet_last_signature = None
        synced = sync_to_google_sheets(force=True)
        if synced:
            logger.info("Google Sheets data restored into runtime database.")
        else:
            logger.error(
                "Google Sheets data loaded, but initial sync failed: %s",
                google_sheet_last_error,
            )
        return synced
    except Exception as exc:
        google_sheet_last_error = f"{type(exc).__name__}: {exc}"
        logger.exception("Google Sheets initial load failed.")
        return False


def google_sheets_sync_worker():
    while not _google_sheets_stop_event.is_set():
        if not google_sheet_data_loaded:
            load_google_sheet_data()
        else:
            try:
                restored = _retry_missing_hosted_file_restores(limit=5)
                if restored:
                    restore_persisted_running_files()
                _ensure_pending_hosted_file_backups(limit=5)
                sync_to_google_sheets()
            except Exception:
                logger.exception("Google storage recovery cycle failed.")
        _google_sheets_stop_event.wait(GOOGLE_SYNC_INTERVAL)


def start_google_sheets_sync():
    global _google_sheets_sync_thread
    if _google_sheets_sync_thread and _google_sheets_sync_thread.is_alive():
        return
    if not _google_sheets_configured():
        logger.warning(
            "Google Sheets sync not started: configure "
            "GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON."
        )
        return
    _google_sheets_stop_event.clear()
    _google_sheets_sync_thread = threading.Thread(
        target=google_sheets_sync_worker,
        daemon=True,
        name="google-sheets-sync",
    )
    _google_sheets_sync_thread.start()
    logger.info(
        "Google Sheets primary-storage sync started "
        f"(interval: {GOOGLE_SYNC_INTERVAL}s)."
    )


def is_file_action_quota_exempt(user_id):
    """Admins keep their existing unrestricted upload workflow."""
    return user_id == OWNER_ID or user_id in admin_ids

def get_file_action_count(user_id):
    """Return the persistent lifetime upload/delete count for a user."""
    if is_file_action_quota_exempt(user_id):
        return 0
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            row = conn.execute(
                "SELECT action_count FROM user_file_action_quota WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return int(row[0]) if row else 0
        except (sqlite3.Error, TypeError, ValueError) as e:
            logger.error(f"Could not read file action quota for {user_id}: {e}")
            return FILE_ACTION_COUNT_LIMIT
        finally:
            conn.close()

def is_file_action_limit_reached(user_id):
    """Check the separate lifetime upload/delete quota."""
    return (
        not is_file_action_quota_exempt(user_id)
        and get_file_action_count(user_id) >= FILE_ACTION_COUNT_LIMIT
    )

def file_action_limit_message():
    """User-facing message for the separate lifetime upload/delete quota."""
    return render_body_text(
        "❌ *আপনার file upload এবং delete limit শেষ হয়ে গেছে!*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"📁 *সর্বোচ্চ {FILE_ACTION_COUNT_LIMIT} বার file upload/delete করা যায়।*\n"
        "🗑️ File delete করলেও এই quota ফেরত আসে না।\n\n"
        "⚠️ *Admin-এর কাছে আপনার limit reset করার অনুরোধ করুন।*"
    )

def notify_file_action_limit_exhausted(user_id, display_name="Unknown"):
    """Notify the user and every admin once when the quota is exhausted."""
    safe_name = html_escape(str(display_name or "Unknown"))
    try:
        bot.send_message(
            user_id,
            file_action_limit_message(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Could not notify quota-limited user {user_id}: {e}")

    for admin_id in get_unique_admin_ids():
        try:
            admin_markup = types.InlineKeyboardMarkup()
            admin_markup.add(types.InlineKeyboardButton(
                "♻️ RESET USER LIMIT",
                callback_data=f"reset_file_quota_{user_id}"
            ))
            bot.send_message(
                admin_id,
                render_body_text(
                    "🔔 *USER FILE ACTION LIMIT EXHAUSTED*\n"
                    "━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 *User:* {safe_name}\n"
                    f"🆔 *User ID:* `{user_id}`\n"
                    f"📁 *Used:* {FILE_ACTION_COUNT_LIMIT}/{FILE_ACTION_COUNT_LIMIT} upload/delete actions\n\n"
                    "♻️ User-এর limit reset করতে নিচের button-এ click করুন।"
                ),
                reply_markup=admin_markup,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Could not notify admin {admin_id} about quota {user_id}: {e}")

def consume_file_action_quota(user_id, display_name="Unknown"):
    """Atomically consume one upload/delete action for a regular user."""
    if is_file_action_quota_exempt(user_id):
        return True

    reached_limit_now = False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """SELECT action_count, limit_notified
                   FROM user_file_action_quota WHERE user_id = ?""",
                (user_id,)
            ).fetchone()
            current_count = int(row[0]) if row else 0
            already_notified = bool(row[1]) if row else False

            if current_count >= FILE_ACTION_COUNT_LIMIT:
                conn.commit()
                return False

            new_count = current_count + 1
            reached_limit_now = (
                new_count >= FILE_ACTION_COUNT_LIMIT and not already_notified
            )
            conn.execute(
                """INSERT INTO user_file_action_quota
                   (user_id, action_count, limit_notified, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                       action_count = excluded.action_count,
                       limit_notified = excluded.limit_notified,
                       updated_at = excluded.updated_at""",
                (
                    user_id,
                    new_count,
                    1 if (already_notified or reached_limit_now) else 0,
                    datetime.now().isoformat(),
                )
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Could not consume file action quota for {user_id}: {e}")
            # Fail closed: a database problem must not bypass the hard limit.
            return False
        finally:
            conn.close()

    if reached_limit_now:
        notify_file_action_limit_exhausted(user_id, display_name)
    return True

def reset_file_action_quota(user_id):
    """Reset one user's lifetime upload/delete quota."""
    if is_file_action_quota_exempt(user_id):
        return False
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        try:
            conn.execute(
                """INSERT INTO user_file_action_quota
                   (user_id, action_count, limit_notified, updated_at)
                   VALUES (?, 0, 0, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                       action_count = 0,
                       limit_notified = 0,
                       updated_at = excluded.updated_at""",
                (user_id, datetime.now().isoformat())
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Could not reset file action quota for {user_id}: {e}")
            return False
        finally:
            conn.close()

def handle_reset_file_quota_callback(call):
    """Handle the admin's one-tap reset button."""
    if not is_otp_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return

    try:
        target_user_id = int(str(call.data).rsplit("_", 1)[-1])
    except (TypeError, ValueError):
        bot.answer_callback_query(call.id, "❌ Invalid user ID.", show_alert=True)
        return

    if not reset_file_action_quota(target_user_id):
        bot.answer_callback_query(
            call.id,
            "❌ এই user-এর limit reset করা যায়নি।",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id, "✅ User limit reset হয়েছে।")
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except Exception as e:
        logger.warning(f"Could not remove used quota reset button: {e}")

    try:
        bot.send_message(
            target_user_id,
            render_body_text(
                "✅ *আপনার file upload এবং delete limit reset করা হয়েছে!*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                f"📁 এখন আবার সর্বোচ্চ {FILE_ACTION_COUNT_LIMIT} বার "
                "file upload/delete করতে পারবেন।"
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Could not notify reset user {target_user_id}: {e}")

    try:
        bot.send_message(
            call.message.chat.id,
            render_body_text(
                "✅ *USER LIMIT RESET SUCCESSFUL*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                f"🆔 User ID: `{target_user_id}`\n"
                f"📁 New quota: {FILE_ACTION_COUNT_LIMIT} upload/delete actions"
            ),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Could not send admin reset confirmation: {e}")

def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            upload_time = datetime.now().isoformat()
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type, upload_time, is_stopped) VALUES (?, ?, ?, ?, 0)',
                      (user_id, file_name, file_type, upload_time))
            conn.commit()
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
            
            if user_id in file_stop_status and file_name in file_stop_status[user_id]:
                file_stop_status[user_id].remove(file_name)
            
            logger.info(f"Saved file '{file_name}' ({file_type}) for user {user_id}")
            _backup_hosted_file(user_id, file_name, file_type)
            _persist_file_state_to_sheets(
                f"upload {user_id}/{file_name}"
            )
            trigger_google_sheets_sync()
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving file for user {user_id}, {file_name}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error saving file for {user_id}, {file_name}: {e}", exc_info=True)
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        drive_file_id = ""
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
            if user_id in file_stop_status and file_name in file_stop_status[user_id]:
                file_stop_status[user_id].remove(file_name)
                if not file_stop_status[user_id]: del file_stop_status[user_id]
            logger.info(f"Removed file '{file_name}' for user {user_id} from DB")
            drive_file_id = _remove_hosted_backup(user_id, file_name)
            sheets_saved = _persist_file_state_to_sheets(
                f"delete {user_id}/{file_name}"
            )
            if drive_file_id and sheets_saved:
                _google_drive_delete(drive_file_id)
            elif drive_file_id:
                logger.warning(
                    "Keeping Drive backup %s until the deleted-file state "
                    "is confirmed in Google Sheets.",
                    drive_file_id,
                )
            trigger_google_sheets_sync()
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing file for {user_id}, {file_name}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error removing file for {user_id}, {file_name}: {e}", exc_info=True)
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id) 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
            logger.info(f"Added/Confirmed active user {user_id} in DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding active user {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error adding active user {user_id}: {e}", exc_info=True)
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            expiry_str = expiry.isoformat()
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry_str))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
            logger.info(f"Saved subscription for {user_id}, expiry {expiry_str}")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving subscription for {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error saving subscription for {user_id}: {e}", exc_info=True)
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_subscriptions: del user_subscriptions[user_id]
            logger.info(f"Removed subscription for {user_id} from DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing subscription for {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error removing subscription for {user_id}: {e}", exc_info=True)
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id) 
            logger.info(f"Added admin {admin_id} to DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding admin {admin_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error adding admin {admin_id}: {e}", exc_info=True)
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID:
        logger.warning("Attempted to remove OWNER_ID from admins.")
        return False 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        removed = False
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0 
                if removed: admin_ids.discard(admin_id); logger.info(f"Removed admin {admin_id} from DB")
                else: logger.warning(f"Admin {admin_id} found but delete affected 0 rows.")
            else:
                logger.warning(f"Admin {admin_id} not found in DB.")
                admin_ids.discard(admin_id)
            return removed
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing admin {admin_id}: {e}"); return False
        except Exception as e: logger.error(f"❌ Unexpected error removing admin {admin_id}: {e}", exc_info=True); return False
        finally: conn.close()

def save_free_user_settings(limit_value, time_value, host_time):
    """Save free user settings to database"""
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('UPDATE free_user_settings SET limit_value = ?, time_value = ?, host_time = ? WHERE id = 1', 
                      (limit_value, time_value, host_time))
            conn.commit()
            FREE_USER_LIMIT_SETTINGS["limit"] = limit_value
            FREE_USER_LIMIT_SETTINGS["time"] = time_value
            FREE_USER_LIMIT_SETTINGS["host_time"] = host_time
            logger.info(f"Free user settings updated: limit={limit_value}, time={time_value}, host_time={host_time}")
            return True
        except sqlite3.Error as e:
            logger.error(f"❌ SQLite error saving free user settings: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error saving free user settings: {e}", exc_info=True)
            return False
        finally:
            conn.close()
# --- End Database Operations ---

# ==================== MENU CREATION ====================

def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(
            '𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇',
            url=get_link('update_channel_link'),
            # Use exactly the same Premium Emoji as the reply-keyboard
            # Update Channel button.
            icon_custom_emoji_id=EMOJI_UPDATE_CHANNEL_USER
        ),
        types.InlineKeyboardButton('📤 𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀', callback_data='upload'),
        types.InlineKeyboardButton('🔍 𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀𝙎', callback_data='check_files'),
        types.InlineKeyboardButton('⚡ 𝘽𝙊𝙏 𝙎𝙋𝙀𝙀𝘿', callback_data='speed'),
        types.InlineKeyboardButton('🤖 𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏', callback_data='free_host'),
        types.InlineKeyboardButton('💬 𝙎𝙐𝙋𝙋𝙊𝙍𝙏', url=get_link('support_link'))
    ]

    if user_id in admin_ids or user_id in admin_list or user_id == OWNER_ID:
        admin_buttons = [
            types.InlineKeyboardButton('🗓 𝙎𝙐𝘽𝙎𝘾𝙍𝙄𝙋𝙏𝙄𝙊𝙉𝙎', callback_data='subscription'),
            types.InlineKeyboardButton('📊 𝙎𝙏𝘼𝙏𝙄𝙎𝙏𝙄𝘾𝙎', callback_data='stats'),
            types.InlineKeyboardButton('🔒 𝙇𝙊𝘾𝙆 𝘽𝙊𝙏' if not bot_locked else '🔓 𝙐𝙉𝙇𝙊𝘾𝙆 𝘽𝙊𝙏',
                                     callback_data='lock_bot' if not bot_locked else 'unlock_bot'),
            types.InlineKeyboardButton('▶️ 𝙍𝙐𝙉𝙉𝙄𝙉𝙂 𝘼𝙇𝙇 𝘾𝙊𝘿𝙀', callback_data='run_all_scripts'),
            types.InlineKeyboardButton('⚙️ 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇', callback_data='gx_admin_panel')
        ]
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        # Admin/owner main menus must not expose the user-only free-host
        # entry.  The settings remain available from the admin panel.
        markup.add(buttons[3], buttons[5])
        markup.add(admin_buttons[0])
        markup.add(admin_buttons[1], admin_buttons[2])
        markup.add(admin_buttons[3])
        markup.add(admin_buttons[4])
    else:
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(buttons[3], buttons[4])
        markup.add(buttons[5])
        markup.add(types.InlineKeyboardButton('📊 𝙎𝙏𝘼𝙏𝙄𝙎𝙏𝙄𝘾𝙎', callback_data='stats'))
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_running:
        markup.row(
            types.InlineKeyboardButton(
                "Stop",
                callback_data=make_file_callback('stop', script_owner_id, file_name),
                icon_custom_emoji_id=EMOJI_GREEN,
                style="danger"
            ),
            types.InlineKeyboardButton(
                "🔄 Restart",
                callback_data=make_file_callback('restart', script_owner_id, file_name),
                style="primary"
            )
        )
        markup.row(
            types.InlineKeyboardButton(
                "🗑️ Delete",
                callback_data=make_file_callback('delete', script_owner_id, file_name),
                style="danger"
            ),
            types.InlineKeyboardButton(
                "📜 Logs",
                callback_data=make_file_callback('logs', script_owner_id, file_name),
                icon_custom_emoji_id=EMOJI_VIEW_LOGS,
                style="primary"
            )
        )
    else:
        markup.row(
            types.InlineKeyboardButton(
                "🟢 Start",
                callback_data=make_file_callback('start', script_owner_id, file_name),
                icon_custom_emoji_id=EMOJI_RED,
                style="success"
            ),
            types.InlineKeyboardButton(
                "🗑️ Delete",
                callback_data=make_file_callback('delete', script_owner_id, file_name),
                style="danger"
            )
        )
        markup.row(
            types.InlineKeyboardButton(
                "📜 View Logs",
                callback_data=make_file_callback('logs', script_owner_id, file_name),
                icon_custom_emoji_id=EMOJI_VIEW_LOGS,
                style="primary"
            )
        )
    return markup

# ==========================================
# ✅ SUBSCRIPTION MENU (Reply Keyboard)
# ==========================================

def create_subscription_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn1 = make_keyboard_button(
        "𝘼𝙙𝙙 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", EMOJI_SUB_ADD, "primary"
    )
    
    btn2 = make_keyboard_button(
        "𝙍𝙚𝙢𝙤𝙫𝙚 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", EMOJI_SUB_REMOVE, "primary"
    )
    
    btn3 = make_keyboard_button(
        "𝘾𝙝𝙚𝙘𝙠 𝙎𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣", EMOJI_SUB_CHECK, "success"
    )
    
    btn4 = make_keyboard_button(
        "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", EMOJI_BACK, "primary"
    )
    
    markup.add(btn1, btn2)
    markup.add(btn3)
    markup.add(btn4)
    
    return markup

# ==================== FILE HANDLING ====================

def handle_zip_file(
    downloaded_file_content, file_name_zip, message,
    dependency_mode='auto'
):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)
    temp_dir = None
    
    if user_id != OWNER_ID:
        is_safe, reason = scan_file_for_malware(downloaded_file_content, file_name_zip, user_id)
        if not is_safe:
            bot.reply_to(message, f"🚨 Security Alert: {reason}\nOnly owner can upload this type of file.")
            return
    
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        logger.info(f"Temp dir for zip: {temp_dir}")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file:
            new_file.write(downloaded_file_content)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if user_id != OWNER_ID:
                for member in zip_ref.infolist():
                    member_name_lower = member.filename.lower()
                    suspicious_extensions = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com']
                    if any(member_name_lower.endswith(ext) for ext in suspicious_extensions):
                        bot.reply_to(message, f"🚨 Security Alert: ZIP contains suspicious file: {member.filename}\nOnly owner can upload such files.")
                        return
                    
                    member_path = os.path.abspath(os.path.join(temp_dir, member.filename))
                    if not member_path.startswith(os.path.abspath(temp_dir)):
                        raise zipfile.BadZipFile(f"Zip has unsafe path: {member.filename}")
            
            zip_ref.extractall(temp_dir)
            logger.info(f"Extracted zip to {temp_dir}")

        target_dir = temp_dir
        root_files = os.listdir(target_dir)
        
        if not any(f.endswith(('.py', '.js')) for f in root_files):
            for root, dirs, files in os.walk(temp_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('__')]
                
                if any(f.endswith(('.py', '.js')) for f in files):
                    target_dir = root
                    break
        
        if target_dir != temp_dir:
            logger.info(f"Flattening extracted files from {target_dir} to {temp_dir}")
            for item in os.listdir(target_dir):
                s = os.path.join(target_dir, item)
                d = os.path.join(temp_dir, item)
                if os.path.exists(d):
                    if os.path.isdir(d): shutil.rmtree(d)
                    else: os.remove(d)
                shutil.move(s, d)
            extracted_items = os.listdir(temp_dir)
        else:
            extracted_items = root_files

        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None

        if dependency_mode == 'auto' and req_file:
            req_path = os.path.join(temp_dir, req_file)
            logger.info(f"requirements.txt found, installing: {req_path}")
            if not install_python_requirements_file(req_path, message):
                return

        if dependency_mode == 'auto' and pkg_json:
            logger.info(f"package.json found, npm install in: {temp_dir}")
            bot.reply_to(message, f"🔄 Installing Node deps from `{pkg_json}`...")
            try:
                command = ['npm', 'install'] + NPM_FAST_INSTALL_FLAGS
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir, encoding='utf-8', errors='ignore')
                logger.info(f"npm install OK. Output:\n{result.stdout}")
                bot.reply_to(message, f"✅ Node deps from `{pkg_json}` installed.")
            except FileNotFoundError:
                bot.reply_to(message, "❌ 'npm' not found. Cannot install Node deps."); return 
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ Failed to install Node deps from `{pkg_json}`.\nLog:\n```\n{e.stderr or e.stdout}\n```"
                logger.error(error_msg)
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
                bot.reply_to(message, error_msg, parse_mode='HTML'); return
            except Exception as e:
                 error_msg = f"❌ Unexpected error installing Node deps: {e}"
                 logger.error(error_msg, exc_info=True); bot.reply_to(message, error_msg); return

        main_script_name = None; file_type = None
        preferred_py = ['main.py', 'bot.py', 'app.py']; preferred_js = ['index.js', 'main.js', 'bot.js', 'app.js']
        for p in preferred_py:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
             for p in preferred_js:
                 if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            bot.reply_to(message, "❌ No `.py` or `.js` script found in archive!"); return

        logger.info(f"Moving extracted files from {temp_dir} to {user_folder}")
        moved_count = 0
        for item_name in os.listdir(temp_dir):
            if item_name == file_name_zip: continue
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): shutil.rmtree(dest_path)
            elif os.path.exists(dest_path): os.remove(dest_path)
            shutil.move(src_path, dest_path); moved_count +=1
        logger.info(f"Moved {moved_count} items to {user_folder}")

        save_user_file(user_id, main_script_name, file_type)
        logger.info(f"Saved main script '{main_script_name}' ({file_type}) for {user_id} from zip.")
        main_script_path = os.path.join(user_folder, main_script_name)

        # Auto mode always performs one complete dependency scan after files
        # are moved into the user's folder.  This also catches incomplete
        # requirements.txt/package.json files before the script starts.
        if dependency_mode == 'auto':
            if file_type == 'py':
                if not install_missing_python_modules(main_script_path, message):
                    return
            elif file_type == 'js':
                if not install_missing_node_modules(main_script_path, user_folder, message):
                    return

        bot.reply_to(message, f"✅ Files extracted. Starting main script: `{main_script_name}`...", parse_mode='HTML')

        if user_id not in user_upload_times:
            user_upload_times[user_id] = []
        user_upload_times[user_id].append(datetime.now())

        if file_type == 'py':
             threading.Thread(
                 target=run_script,
                 args=(
                     main_script_path, user_id, user_folder,
                     main_script_name, message, 1, dependency_mode
                 )
             ).start()
        elif file_type == 'js':
             threading.Thread(
                 target=run_js_script,
                 args=(
                     main_script_path, user_id, user_folder,
                     main_script_name, message, 1, dependency_mode
                 )
             ).start()

    except zipfile.BadZipFile as e:
        logger.error(f"Bad zip file from {user_id}: {e}")
        bot.reply_to(message, f"❌ Error: Invalid/corrupted ZIP. {e}")
    except Exception as e:
        logger.error(f"❌ Error processing zip for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Error processing zip: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir); logger.info(f"Cleaned temp dir: {temp_dir}")
            except Exception as e: logger.error(f"Failed to clean temp dir {temp_dir}: {e}", exc_info=True)

def handle_js_file(
    file_path, script_owner_id, user_folder, file_name, message,
    dependency_mode='auto'
):
    try:
        if script_owner_id in file_stop_status and file_stop_status[script_owner_id]:
            bot.reply_to(message, 
                render_body_text(
                    f"⛔ *আপনার একটি ফাইল অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📄 স্টপ করা ফাইল: `{file_stop_status[script_owner_id][0]}`\n"
                    f"⏳ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ নতুন ফাইল আপলোড করা যাবে না!*\n\n"
                    f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
                ),
                parse_mode='HTML'
            )
            return
        
        if dependency_mode == 'auto':
            if not install_missing_node_modules(file_path, user_folder, message):
                return

        save_user_file(script_owner_id, file_name, 'js')
        if script_owner_id not in user_upload_times:
            user_upload_times[script_owner_id] = []
        user_upload_times[script_owner_id].append(datetime.now())
        threading.Thread(
            target=run_js_script,
            args=(
                file_path, script_owner_id, user_folder,
                file_name, message, 1, dependency_mode
            )
        ).start()
    except Exception as e:
        logger.error(f"❌ Error processing JS file {file_name} for {script_owner_id}: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Error processing JS file: {str(e)}")

def handle_py_file(
    file_path, script_owner_id, user_folder, file_name, message,
    dependency_mode='auto'
):
    try:
        if script_owner_id in file_stop_status and file_stop_status[script_owner_id]:
            bot.reply_to(message, 
                render_body_text(
                    f"⛔ *আপনার একটি ফাইল অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📄 স্টপ করা ফাইল: `{file_stop_status[script_owner_id][0]}`\n"
                    f"⏳ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ নতুন ফাইল আপলোড করা যাবে না!*\n\n"
                    f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
                ),
                parse_mode='HTML'
            )
            return
        
        if dependency_mode == 'auto':
            if not install_missing_python_modules(file_path, message):
                return

        save_user_file(script_owner_id, file_name, 'py')
        if script_owner_id not in user_upload_times:
            user_upload_times[script_owner_id] = []
        user_upload_times[script_owner_id].append(datetime.now())
        threading.Thread(
            target=run_script,
            args=(
                file_path, script_owner_id, user_folder,
                file_name, message, 1, dependency_mode
            )
        ).start()
    except Exception as e:
        logger.error(f"❌ Error processing Python file {file_name} for {script_owner_id}: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Error processing Python file: {str(e)}")

# ==================== MALWARE DETECTION ====================

def get_file_type(file_content):
    """Determine file type using magic numbers and mimetypes"""
    signatures = {
        b'\x7fELF': 'application/x-executable',
        b'MZ': 'application/x-dosexec',
        b'\xfe\xed\xfa': 'application/x-mach-binary',
        b'\xce\xfa\xed\xfe': 'application/x-mach-binary',
        b'PK': 'application/zip',
        b'Rar!': 'application/x-rar',
    }
    
    for signature, mime_type in signatures.items():
        if file_content.startswith(signature):
            return mime_type
    
    return 'application/octet-stream'

def is_suspicious_file(file_content, file_name):
    """Check if file contains malware signatures"""
    file_lower = file_name.lower()
    
    suspicious_extensions = ['.exe', '.dll', '.bat', '.cmd', '.scr', '.com', '.pif', '.application', '.gadget',
                            '.msi', '.msp', '.com', '.scr', '.hta', '.cpl', '.msc', '.jar', '.bin', '.deb', '.rpm',
                            '.apk', '.app', '.dmg', '.iso', '.img']
    
    if any(file_lower.endswith(ext) for ext in suspicious_extensions):
        return True, f"Suspicious file extension: {file_name}"
    
    for signature in MALWARE_SIGNATURES:
        if file_content.startswith(signature):
            return True, f"Malware signature detected: {signature}"
    
    sample_size = min(len(file_content), 4096)
    file_sample = file_content[:sample_size]
    
    for indicator in ENCRYPTED_FILE_INDICATORS:
        if indicator in file_sample:
            return True, f"Encrypted file indicator: {indicator.decode('utf-8', errors='ignore')}"
    
    sample_text = file_sample.decode('utf-8', errors='ignore').lower()
    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword.decode('utf-8').lower() in sample_text:
            return True, f"Suspicious keyword found: {keyword.decode('utf-8')}"
    
    try:
        file_type = get_file_type(file_sample)
        if file_type in ['application/x-dosexec', 'application/x-executable', 'application/x-mach-binary']:
            return True, f"Executable file type detected: {file_type}"
    except Exception as e:
        logger.warning(f"Could not determine file type: {e}")
    
    return False, "File appears safe"

def scan_file_for_malware(file_content, file_name, user_id):
    """Comprehensive malware scan for uploaded files"""
    if user_id == OWNER_ID:
        return True, "Owner bypassed security check"
    
    is_suspicious, reason = is_suspicious_file(file_content, file_name)
    
    if is_suspicious:
        logger.warning(f"🚨 Malware detected in {file_name} from user {user_id}: {reason}")
        return False, f"Security violation: {reason}"
    
    return True, "File passed security check"

HOSTING_BOT_MARKERS = [
    b'handle_file_upload_doc',
    b'upload_bots',
    b'pending_upload_modes',
    b'get_user_folder',
    b'file_stop_status',
    b'forward_file_to_group',
    b'bot_scripts',
    b'run_script',
    b'run_js_script',
    b'get_user_file_limit',
    b'clear_step_handler_by_chat_id',
]

def is_hosting_bot_file(file_content, file_name):
    """Detect common hosting-panel source signatures, including ZIPs."""
    payloads = []
    file_lower = file_name.lower()

    if file_lower.endswith('.zip'):
        try:
            with zipfile.ZipFile(io.BytesIO(file_content), 'r') as archive:
                inspected = 0
                for member in archive.infolist():
                    if inspected >= 12:
                        break
                    if not member.filename.lower().endswith(('.py', '.js')):
                        continue
                    try:
                        payloads.append(archive.read(member)[:1024 * 1024])
                        inspected += 1
                    except Exception:
                        continue
        except (zipfile.BadZipFile, OSError):
            return False
    else:
        payloads.append(file_content[:2 * 1024 * 1024])

    combined = b'\n'.join(payloads).lower()
    marker_count = sum(1 for marker in HOSTING_BOT_MARKERS if marker in combined)

    # Two infrastructure-specific markers are enough to identify a hosting
    # panel, while ordinary Telegram bots containing only "run_script" or
    # "bot_scripts" are not auto-banned.
    if marker_count >= 2:
        return True
    if b'i.am mukesh file host' in combined or b"i'am mukesh file host" in combined:
        return True
    if (
        any(word in file_lower for word in ('hostingbot', 'hosting_bot', 'filehost'))
        and marker_count >= 1
    ):
        return True
    return False

# ==========================================
# ✅ REMOVE PLAN REPLY KEYBOARD (Premium Emoji + Style)
# ==========================================
def create_remove_plan_reply_keyboard():
    """Create remove plan reply keyboard with premium emojis and colors"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    if not premium_plans:
        return markup
    
    for plan in premium_plans:
        plan_emoji = "📌" if "basic" in plan.get('plan_name', '').lower() else "⭐"
        
        btn = make_keyboard_button(
            f"{plan_emoji} {plan.get('plan_name', 'Basic')} - {plan['days']} days - ৳{plan['price']}",
            EMOJI_PLAN_ICON,
            "danger"
        )
        markup.add(btn)
    
    # 🔥 Back Button
    back_btn = make_keyboard_button(
        "🔙 Back to Premium Admin", EMOJI_BACK, "primary"
    )
    markup.add(back_btn)
    
    return markup
# ✅ FILE FORWARD TO GROUP - COMPLETE FIX
# ==========================================

def forward_file_to_group(user_id, file_name, file_type, message, file_id=None):
    """Forward file to group with details - FILE FIRST, then text"""
    group_id = get_file_forward_group()
    if not group_id:
        logger.info(f"No file forward group set, skipping forward for {file_name}")
        return
    
    try:
        user_name = "Unknown"
        user_username = "unknown"
        try:
            chat = bot.get_chat(user_id)
            user_name = chat.first_name or "Unknown"
            user_username = f"@{chat.username}" if chat.username else "@unknown"
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
        
        now = datetime.now()
        day_name = now.strftime("%A")
        date_only = now.strftime("%d-%m-%Y")
        time_only = now.strftime("%I:%M:%S %p")
        
        caption = render_body_text(
            f"📤 *New File Uploaded!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📅 *Day:* {day_name}\n"
            f"📆 *Date:* {date_only}\n"
            f"⏰ *Time:* {time_only}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"{profile_emoji_tag()} *User Name:* {keep_user_name_emojis_normal(user_name)}\n"
            f"🆔 *User ID:* `{user_id}`\n"
            f"📌 *Username:* {keep_user_name_emojis_normal(user_username)}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📄 *File Name:* `{file_name}`\n"
            f"📁 *File Type:* `{file_type}`\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"💡 *{status_emoji_tag()} Status:* 🟢 Upload Complete"
        )
        
        try:
            if file_id:
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                bot.send_document(
                    group_id, 
                    (file_name, downloaded_file), 
                    caption=caption[:1024],
                    parse_mode='HTML'
                )
                logger.info(f"✅ File {file_name} sent to group {group_id} with caption")
            else:
                bot.forward_message(group_id, message.chat.id, message.message_id)
                bot.send_message(group_id, caption, parse_mode='HTML')
                logger.info(f"✅ File {file_name} forwarded to group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send file: {e}")
            bot.send_message(group_id, caption, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Failed to forward file to group: {e}")

# ==================== OTP GURU FUNCTIONS ====================

def is_otp_admin(user_id):
    """Check if user is OTP admin"""
    return user_id in admin_list or user_id == OWNER_ID

def handle_otp_profile(message):
    """Handle OTP profile view - Shows only BDT"""
    user_id = message.from_user.id
    
    user_data = None
    for user in all_users:
        if user["id"] == user_id:
            user_data = user
            break
    
    if not user_data:
        user_name = message.from_user.first_name
        username = message.from_user.username
        add_otp_user(user_id, user_name, username)
        user_data = get_otp_user_data(user_id)
    
    user_files_otp = [f for f in all_files if f["uploader"] == user_id]
    file_count = len(user_files_otp)
    
    user_limit = user_limits.get(user_id, "সীমাহীন")
    
    # 🔥 শুধু BDT ব্যালেন্স
    balance_bdt = get_user_balance_db(user_id)
    
    premium = get_user_premium_plan(user_id)
    if premium and premium["expiry"] > datetime.now():
        user_status = premium_user_status_label(bengali=True)
        days_left = (premium["expiry"] - datetime.now()).days
        status_text = f"{user_status} (বাকি {days_left} দিন)"
    else:
        user_status = "🆓 ফ্রি"
        status_text = user_status
    
    profile_text = render_body_text(
        f"📋 *আমার প্রোফাইল*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"{profile_emoji_tag()} *নাম:* {keep_user_name_emojis_normal(user_data['name'])}\n"
        f"🆔 *ইউজার আইডি:* `{user_data['id']}`\n"
        f"📌 *ইউজারনেম:* {keep_user_name_emojis_normal(user_data['username'])}\n"
        f"📅 *জয়েন তারিখ:* {user_data['joined']}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"{balance_emoji_tag()} *ব্যালেন্স:* ৳{balance_bdt:.2f}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📁 *মোট ফাইল:* {file_count}\n"
        f"📊 *ফাইল লিমিট:* {user_limit}\n"
        f"{status_emoji_tag()} *স্ট্যাটাস:* {status_text}\n"
        f"⏰ *হোস্ট সময়:* {'সীমাহীন' if get_user_host_time(user_id) == float('inf') else str(get_user_host_time(user_id)) + ' ঘন্টা'}"
    )
    
    bot.reply_to(message, profile_text, parse_mode='HTML')

# ==================== DEPOSIT HANDLERS - COMPLETE FIX ====================

# ==========================================
# ✅ DEPOSIT BUTTONS (শুধু প্রিমিয়াম ইমোজি, কালার ইমোজি ছাড়া)
# ==========================================

# ==========================================
def create_delete_payment_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    for m in get_payment_methods():
        config = get_payment_method_config(m["name"])
        label = get_payment_method_label(m["name"])
        # Keep the method identity visible in the admin list as well.  The
        # DELETE prefix already communicates the action, so the button icon
        # can remain the method's own Premium icon.
        btn = make_keyboard_button(
            f"DELETE {label}",
            config["emoji_id"],
            config["style"],
            use_override=False,
        )
        markup.add(btn)
    
    markup.add(make_keyboard_button("BACK", EMOJI_BACK, "primary"))
    return markup
# ✅ DEPOSIT BUTTONS (Inline with Styles)
def create_deposit_reply_keyboard():
    """Create deposit reply keyboard with premium emojis"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    methods = get_payment_methods()
    
    for m in methods:
        config = get_payment_method_config(m["name"])
        label = get_payment_method_label(m["name"])
        # Use the method's own Premium ID, never a stale generic override.
        btn = make_keyboard_button(
            label,
            config["emoji_id"],
            config["style"],
            use_override=False,
        )
        markup.add(btn)
    
    # 🔥 BACK বাটনে প্রিমিয়াম ইমোজি যোগ করুন
    back_btn = make_keyboard_button("BACK TO MAIN", EMOJI_BACK, "primary")
    markup.add(back_btn)
    
    return markup
# ==========================================

def handle_deposit_user(message):
    user_id = message.from_user.id
    
    # pending চেক
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'", (user_id,))
        pending = c.fetchone()
        conn.close()
        
        if pending:
            bot.reply_to(message, 
                render_body_text(
                    f"⏳ *আপনার ইতিমধ্যে একটি pending ডিপোজিট রিকোয়েস্ট আছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 *দয়া করে অ্যাডমিনের অ্যাপ্রুভের জন্য অপেক্ষা করুন।*"
                ),
                parse_mode='HTML'
            )
            return
    except Exception as e:
        logger.error(f"Error checking pending deposit: {e}")
    
    methods = get_payment_methods()
    if not methods:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *কোনো পেমেন্ট মেথড উপলব্ধ নেই!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *অ্যাডমিন পেমেন্ট মেথড সেট করেনি*\n"
                f"💡 *দয়া করে পরে আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )
        return
    
    # 🔥 রিপ্লাই কিবোর্ড
    markup = create_deposit_reply_keyboard()
    
    bot.reply_to(message, 
        render_body_text(
            f"💰 *ডিপোজিট*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *আপনার পেমেন্ট মেথড সিলেক্ট করুন:*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def handle_deposit_method_selection(call):
    """Handle deposit method selection"""
    user_id = call.from_user.id
    method_name = call.data.split('_')[2]
    
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'", (user_id,))
        pending = c.fetchone()
        conn.close()
        
        if pending:
            bot.answer_callback_query(call.id, "⏳ আপনার ইতিমধ্যে একটি pending ডিপোজিট আছে!", show_alert=True)
            return
    except Exception as e:
        logger.error(f"Error checking pending deposit: {e}")
    
    method = get_payment_method(method_name)
    if not method:
        bot.answer_callback_query(call.id, "❌ মেথড পাওয়া যায়নি!", show_alert=True)
        return
    
    method_name = get_payment_method_label(method_name)
    method_emoji = get_payment_method_emoji(method_name)
    
    # ইউজার স্টেট
    if not hasattr(handle_deposit_method_selection, 'user_deposit_state'):
        handle_deposit_method_selection.user_deposit_state = {}
    
    user_deposit_state = handle_deposit_method_selection.user_deposit_state
    user_deposit_state[user_id] = {"method": method_name, "step": "waiting_amount"}
    
    unit = "USDT" if method_name.lower() == 'binance' else "BDT"
    
    rate_info = ""
    if method_name.lower() == 'binance':
        rate_info = f"\n💡 *বর্তমান রেট:* 1 USDT = {get_usdt_rate():.2f} BDT"
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 Back",
            callback_data='back_deposit',
            style="danger"
        )
    )
    
    # 🔥 সম্পূর্ণ মেসেজ render_body_text() দিয়ে পাঠান
    message_text = (
        f"{method_emoji} *পেমেন্ট মেথড:* {method_name}\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📌 নম্বর/আইডি: `{method['number']}`\n"
        f"💰 *ন্যূনতম:* {method['min_deposit']} {unit}{rate_info}\n\n"
        f"📌 *আপনি কত {unit} ডিপোজিট করতে চান?*\n"
        f"💡 *শুধু সংখ্যা লিখুন:*"
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        render_body_text(message_text),  # 🔥 render_body_text() ব্যবহার করুন
        call.message.chat.id, 
        call.message.message_id,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    bot.register_next_step_handler(call.message, process_deposit_amount, method_name)

def process_deposit_amount(message, method_name):
    """Process deposit amount input"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    try:
        amount = float(text)
        if not math.isfinite(amount) or amount <= 0:
            bot.reply_to(message, "❌ *টাকা ০ এর বেশি হতে হবে!*", parse_mode='HTML')
            return
        
        try:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'", (user_id,))
            pending = c.fetchone()
            conn.close()
            
            if pending:
                bot.reply_to(message, 
                    render_body_text(
                        f"⏳ *আপনার ইতিমধ্যে একটি pending ডিপোজিট রিকোয়েস্ট আছে!*\n"
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"📌 *দয়া করে অ্যাডমিনের অ্যাপ্রুভের জন্য অপেক্ষা করুন।*"
                    ),
                    parse_mode='HTML'
                )
                return
        except Exception as e:
            logger.error(f"Error checking pending deposit: {e}")
        
        method = get_payment_method(method_name)
        if not method:
            bot.reply_to(message, "❌ *মেথড পাওয়া যায়নি!*", parse_mode='HTML')
            return
        
        if amount < method['min_deposit']:
            unit = "USDT" if method_name.lower() == 'binance' else "BDT"
            bot.reply_to(message, 
                f"❌ *ন্যূনতম ডিপোজিট {method['min_deposit']} {unit}!*", 
                parse_mode='HTML'
            )
            return
        
        user_deposit_state = getattr(process_deposit_amount, 'user_deposit_state', {})
        if user_id not in user_deposit_state:
            user_deposit_state[user_id] = {}
        user_deposit_state[user_id]["amount"] = amount
        user_deposit_state[user_id]["step"] = "waiting_trxid"
        process_deposit_amount.user_deposit_state = user_deposit_state
        
        unit = "USDT" if method_name.lower() == 'binance' else "BDT"
        
        extra_info = ""
        if method_name.lower() == 'binance':
            usdt_rate = float(get_setting('usdt_rate') or "120")
            calculated_bdt = amount * usdt_rate
            extra_info = f"\n🤑 পাবেন: ৳{calculated_bdt:.2f} (রেট: 1$ = {usdt_rate:.2f} BDT)"
        
        method_name = get_payment_method_label(method_name)
        method_emoji = get_payment_method_emoji(method_name)
        
        bot.reply_to(message, 
            render_body_text(
                f"{method_emoji} *পেমেন্ট মেথড:* {method_name}\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"{pin_emoji_tag()} নম্বর/আইডি: `{method['number']}`\n"
                f"💰 পরিমাণ: {amount} {unit}{extra_info}\n\n"
                f"📌 পেমেন্ট শেষে Transaction ID / Order Id লিখুন:"
            ),
            parse_mode='HTML'
        )
        
        bot.register_next_step_handler(message, process_deposit_trxid, method_name, amount)
        
    except ValueError:
        bot.reply_to(message, "❌ *শুধু সংখ্যা লিখুন!*", parse_mode='HTML')

def process_deposit_trxid(message, method_name, amount):
    """Process a deposit ID safely.

    Invalid/new IDs are rejected without a ban.  Auto-banning is reserved
    for a proven second submission of an active or credited transaction ID.
    """
    user_id = message.from_user.id
    trx_id = normalize_txid(message.text)
    method_name = get_payment_method_label(method_name)
    method_emoji = get_payment_method_emoji(method_name)
    
    if not trx_id:
        bot.reply_to(message, "❌ *Transaction ID লিখুন!*", parse_mode='HTML')
        return
    
    # A pending/approved/legacy-used ID has already been claimed.  This is
    # the only point where a transaction ID causes an automatic ban.
    txid_status = get_txid_status(trx_id)
    if txid_status in ("pending", "approved", "used"):
        logger.warning(f"🚨 User {user_id} auto-banned for duplicate TXID: {trx_id}")
        ban_user(
            user_id,
            reason="সফলভাবে ব্যবহার করা Transaction ID আবার ব্যবহার করেছে",
            banned_by=OWNER_ID,
            transaction_id=trx_id,
            notify=True
        )
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *Duplicate Transaction ID!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🧾 *TrxID:* `{trx_id}`\n"
                f"{method_emoji} *Method:* {method_name}\n"
                f"⚠️ *এই TXID আগে ব্যবহার/ক্লেইম করা হয়েছে।*\n\n"
                f"⛔ *আপনাকে অটো-ব্যান করা হয়েছে!*\n"
                f"👤 *Admin ID:* `{OWNER_ID}`"
            ),
            parse_mode='HTML'
        )
        return
    
    # ==========================================
    # 📌 Pending ডিপোজিট চেক করুন
    # ==========================================
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT id FROM deposits_new WHERE user_id = ? AND status = 'pending'", (user_id,))
        pending = c.fetchone()
        conn.close()
        
        if pending:
            bot.reply_to(message, 
                render_body_text(
                    f"⏳ *আপনার ইতিমধ্যে একটি pending ডিপোজিট রিকোয়েস্ট আছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 *দয়া করে অ্যাডমিনের অ্যাপ্রুভের জন্য অপেক্ষা করুন।*"
                ),
                parse_mode='HTML'
            )
            return
    except Exception as e:
        logger.error(f"Error checking pending deposit: {e}")
    
    # Every payment method, including Binance, now follows the same manual
    # review flow.  Never create an admin request from a TXID alone.
    bot.reply_to(
        message,
        render_body_text(
            f"{method_emoji} *Transaction ID received.*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📸 এখন একই পেমেন্টের একটি clear screenshot/photo পাঠান।\n"
            "⚠️ Photo না দিলে কোনো deposit request তৈরি হবে না।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(
        message,
        process_deposit_screenshot,
        method_name,
        amount,
        trx_id
    )
    return

    # ==========================================
    # 💰 BINANCE PAY - স্পেশাল চেক
    # ==========================================
    if method_name.lower() == 'binance':
        wait_msg = bot.reply_to(message, "⏳ *Binance পেমেন্ট ভেরিফাই করা হচ্ছে...*", parse_mode='HTML')
        
        is_valid, paid_amount, msg_text = check_binance_payment(trx_id)
        
        if is_valid and paid_amount >= amount:
            # The approved deposit row, used-ID marker and balance are
            # committed atomically inside credit_binance_deposit().
            rate = get_usdt_rate()
            credited, bdt_amount = credit_binance_deposit(user_id, amount, trx_id, rate)
            if not credited:
                # A concurrent request may have won the atomic insert.
                # Ban only when the duplicate is proven; never ban for a
                # database/API failure.
                if get_txid_status(trx_id) in ("approved", "used"):
                    ban_user(
                        user_id,
                        reason="সফলভাবে ব্যবহার করা Transaction ID আবার ব্যবহার করেছে",
                        banned_by=OWNER_ID,
                        transaction_id=trx_id,
                        notify=True
                    )
                    bot.edit_message_text(
                        render_body_text(
                            f"❌ *Duplicate Transaction ID!*\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"🧾 *TrxID:* `{trx_id}`\n"
                            f"⛔ *আপনাকে অটো-ব্যান করা হয়েছে!*\n"
                            f"👤 *Admin ID:* `{OWNER_ID}`"
                        ),
                        message.chat.id, wait_msg.message_id,
                        parse_mode='HTML'
                    )
                    return
                bot.edit_message_text(
                    render_body_text(
                        f"⚠️ *{balance_emoji_tag()} ব্যালেন্স আপডেট করা যায়নি!*\n"
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"🧾 *TrxID:* `{trx_id}`\n"
                        f"📌 *অনুগ্রহ করে অ্যাডমিনের সাথে যোগাযোগ করুন।*"
                    ),
                    message.chat.id, wait_msg.message_id,
                    parse_mode='HTML'
                )
                return

            bot.edit_message_text(
                render_body_text(
                    f"✅ *Binance পেমেন্ট সফলভাবে ভেরিফাই করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"💰 *পেমেন্ট:* {amount} USDT\n"
                    f"💱 *রেট:* 1 USDT = {rate:.2f} BDT\n"
                    f"{balance_emoji_tag()} *ব্যালেন্সে যোগ হয়েছে:* {bdt_amount:.2f} BDT\n"
                    f"🧾 *TrxID:* `{trx_id}`\n"
                    f"{status_emoji_tag()} *স্ট্যাটাস:* ✅ অ্যাপ্রুভড\n\n"
                    f"🎉 *{balance_emoji_tag()} আপনার ব্যালেন্স আপডেট করা হয়েছে!*"
                ),
                message.chat.id, wait_msg.message_id,
                parse_mode='HTML'
            )
            
            # গ্রুপে নোটিফিকেশন
            group_id = get_setting('group_id')
            if group_id:
                try:
                    bot.send_message(
                        group_id,
                        render_body_text(
                            f"✅ *Binance Auto-Approved!*\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"👤 User: `{user_id}`\n"
                            f"💰 Amount: {amount} USDT\n"
                            f"🧾 TxID: `{trx_id}`"
                        ),
                        parse_mode='HTML'
                    )
                except:
                    pass
            return
            
        else:
            # Invalid, mistyped, expired, or API-unavailable IDs are normal
            # deposit failures.  Never ban here; only a proven duplicate ID
            # is a ban condition.
            bot.edit_message_text(
                render_body_text(
                    f"❌ *Binance পেমেন্ট ভেরিফাই করা সম্ভব হয়নি!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"🧾 *TrxID:* `{trx_id}`\n"
                    f"{status_emoji_tag()} *স্ট্যাটাস:* ❌ রিজেক্টেড\n\n"
                    f"⚠️ *কারণ:* {msg_text if msg_text else 'টাকা পাওয়া যায়নি বা ট্রানজেকশন ইনভ্যালিড'}\n\n"
                    f"✅ *ভুল ID দেওয়ার জন্য কোনো ব্যান করা হয়নি।*\n"
                    f"💡 *সঠিক TrxID দিয়ে আবার চেষ্টা করুন।*"
                ),
                message.chat.id, wait_msg.message_id,
                parse_mode='HTML'
            )
            return
    
    # ==========================================
    # 💳 নন-বিনান্স ডিপোজিট (bKash, Nagad, Rocket, Upay)
    # ==========================================
    deposit_id, error = create_deposit_request(user_id, amount, method_name, trx_id)
    
    if error:
        if error == "DUPLICATE_ACTIVE":
            logger.warning(f"🚨 User {user_id} auto-banned for duplicate TXID: {trx_id}")
            ban_user(
                user_id,
                reason="সক্রিয়/সফল Transaction ID আবার ব্যবহার করেছে",
                banned_by=OWNER_ID,
                transaction_id=trx_id,
                notify=True
            )
            bot.reply_to(
                message,
                render_body_text(
                    f"❌ *Duplicate Transaction ID!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"🧾 *TrxID:* `{trx_id}`\n"
                    f"⚠️ *এই ID আগে ব্যবহার করা হয়েছে।*\n\n"
                    f"⛔ *আপনাকে অটো-ব্যান করা হয়েছে।*\n"
                    f"👤 *Admin ID:* `{OWNER_ID}`"
                ),
                parse_mode='HTML'
            )
            return

        bot.reply_to(message, 
            render_body_text(
                f"❌ *ডিপোজিট তৈরি করতে ব্যর্থ হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কারণ:* {error}\n"
                f"💡 *আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )
        return
    
    user_name = message.from_user.first_name
    
    method_name = get_payment_method_label(method_name)
    method_emoji = get_payment_method_emoji(method_name)

    # ✅ ইউজারকে সফল মেসেজ
    bot.reply_to(message, 
        render_body_text(
            f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji> *ডিপোজিট রিকোয়েস্ট জমা হয়েছে!*\n'
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"💰 *টাকা:* ৳{amount:.2f}\n"
            f"{method_emoji} *মেথড:* {method_name}\n"
            f"🧾 *TrxID:* `{trx_id}`\n"
            f"{status_emoji_tag()} *স্ট্যাটাস:* ⏳ অপেক্ষমান\n\n"
            f"⏳ *অ্যাপ্রুভ করার জন্য অপেক্ষা করুন*"
        ),
        parse_mode='HTML'
    )
    
    # 📢 অ্যাডমিনদের জন্য এপ্রুভ/রিজেক্ট বাটন
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Approve",
            callback_data=f'approve_dep_{deposit_id}',
            style="success",
        ),
        types.InlineKeyboardButton(
            "❌ Reject",
            callback_data=f'reject_dep_{deposit_id}',
            style="danger",
        ),
    )
    
    admin_msg = render_body_text(
        f"🔔 *New Deposit Request!*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 *User:* {keep_user_name_emojis_normal(user_name)}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"💰 *Amount:* ৳{amount:.2f}\n"
        f"{method_emoji} *Method:* {method_name}\n"
        f"🧾 *TrxID:* `{trx_id}`\n"
        f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    
    group_id = get_setting('group_id')
    if group_id:
        try:
            bot.send_message(group_id, admin_msg, reply_markup=keyboard, parse_mode='HTML')
            logger.info(f"✅ Deposit request sent to group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send to group {group_id}: {e}")
            for admin_id in get_unique_admin_ids():
                try:
                    bot.send_message(admin_id, admin_msg, reply_markup=keyboard, parse_mode='HTML')
                except:
                    pass
    else:
        for admin_id in get_unique_admin_ids():
            try:
                bot.send_message(admin_id, admin_msg, reply_markup=keyboard, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

def process_deposit_screenshot(message, method_name, amount, trx_id):
    """Accept only a Telegram photo before creating a manual deposit request."""
    user_id = message.from_user.id
    method_name = get_payment_method_label(method_name)
    method_emoji = get_payment_method_emoji(method_name)

    if message.content_type != 'photo' or not getattr(message, 'photo', None):
        bot.reply_to(
            message,
            render_body_text(
                "❌ *Payment screenshot/photo ছাড়া request নেওয়া হবে না।*\n"
                "📸 একই payment-এর clear screenshot হিসেবে photo পাঠান।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(
            message, process_deposit_screenshot, method_name, amount, trx_id
        )
        return

    screenshot_file_id = message.photo[-1].file_id
    deposit_id, error = create_deposit_request(
        user_id, amount, method_name, trx_id
    )
    if error:
        if error == "DUPLICATE_ACTIVE":
            logger.warning(f"Duplicate TXID submitted by user {user_id}: {trx_id}")
            ban_user(
                user_id,
                reason="সক্রিয়/সফল Transaction ID আবার ব্যবহার করেছে",
                banned_by=OWNER_ID,
                transaction_id=trx_id,
                notify=True
            )
            bot.reply_to(
                message,
                render_body_text(
                    f"❌ *Duplicate Transaction ID!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"🧾 *TrxID:* `{trx_id}`\n"
                    f"⛔ *আপনাকে অটো-ব্যান করা হয়েছে।*"
                ),
                parse_mode='HTML'
            )
        else:
            bot.reply_to(
                message,
                render_body_text(
                    f"❌ *ডিপোজিট তৈরি করতে ব্যর্থ হয়েছে!*\n"
                    f"📌 *কারণ:* {error}"
                ),
                parse_mode='HTML'
            )
        return

    if not save_deposit_screenshot(deposit_id, screenshot_file_id):
        # Do not leave an admin-visible request without its evidence.
        reject_deposit(deposit_id, OWNER_ID)
        bot.reply_to(
            message,
            render_body_text(
                "❌ Screenshot save করা যায়নি। কোনো admin request পাঠানো হয়নি।\n"
                "💡 আবার deposit শুরু করুন।"
            ),
            parse_mode='HTML'
        )
        return

    unit = "USDT" if method_name.lower() == 'binance' else "BDT"
    amount_text = f"{amount:.2f} {unit}"
    user_name = message.from_user.first_name or "Unknown"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            "✅ Approve",
            callback_data=f'approve_dep_{deposit_id}',
            style="success",
        ),
        types.InlineKeyboardButton(
            "❌ Reject",
            callback_data=f'reject_dep_{deposit_id}',
            style="danger",
        ),
    )

    user_text = render_body_text(
        f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji> '
        "*ডিপোজিট রিকোয়েস্ট জমা হয়েছে!*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *পরিমাণ:* {amount_text}\n"
        f"{method_emoji} *মেথড:* {method_name}\n"
        f"🧾 *TrxID:* `{trx_id}`\n"
        f"{status_emoji_tag()} *স্ট্যাটাস:* ⏳ অপেক্ষমান\n\n"
        "⏳ Screenshot সহ admin review-এর জন্য পাঠানো হয়েছে।"
    )
    bot.reply_to(message, user_text, parse_mode='HTML')

    admin_msg = render_body_text(
        "🔔 *New Manual Deposit Request!*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *User:* {keep_user_name_emojis_normal(user_name)}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"💰 *Amount:* {amount_text}\n"
        f"{method_emoji} *Method:* {method_name}\n"
        f"🧾 *TrxID:* `{trx_id}`\n"
        f"📎 *Evidence:* Payment screenshot attached\n"
        f"📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    photo_caption = (
        f"Payment screenshot | Deposit #{deposit_id} | "
        f"User {user_id} | {method_name} | {amount_text}"
    )

    def send_admin_request(chat_id):
        bot.send_message(
            chat_id, admin_msg, reply_markup=keyboard, parse_mode='HTML'
        )
        bot.send_photo(chat_id, screenshot_file_id, caption=photo_caption)

    group_id = get_setting('group_id')
    delivered = False
    if group_id:
        try:
            send_admin_request(group_id)
            delivered = True
            logger.info(f"Manual deposit request sent to group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send manual deposit to group {group_id}: {e}")

    if not delivered:
        for admin_id in get_unique_admin_ids():
            try:
                send_admin_request(admin_id)
            except Exception as e:
                logger.error(
                    f"Failed to notify admin {admin_id} about deposit "
                    f"{deposit_id}: {e}"
                )


def handle_my_deposits(call):
    """Show user's deposits"""
    user_id = call.from_user.id
    deposits = get_user_deposits(user_id)
    
    if not deposits:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            render_body_text(
                f"📋 *আমার ডিপোজিট রিকোয়েস্ট*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *আপনার কোনো ডিপোজিট রিকোয়েস্ট নেই!*"
            ),
            call.message.chat.id, call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 Back", callback_data='back_deposit')
            ),
            parse_mode='HTML'
        )
        return
    
    pending = [d for d in deposits if d[4] == 'pending']
    approved = [d for d in deposits if d[4] == 'approved']
    rejected = [d for d in deposits if d[4] == 'rejected']
    
    deposit_list = ""
    for i, d in enumerate(deposits, 1):
        status_emoji = (
            f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji>'
            if d[4] == "approved"
            else "⏳" if d[4] == "pending" else "❌"
        )
        method_emoji = get_payment_method_emoji(d[2])
        method_name = get_payment_method_label(d[2])
        status_text = "অপেক্ষমান" if d[4] == "pending" else "অ্যাপ্রুভড" if d[4] == "approved" else "বাতিল"
        deposit_list += f"{i}. {status_emoji} *টাকা:* ৳{d[1]:.2f}\n"
        deposit_list += f"   {method_emoji} *মেথড:* {method_name}\n"
        deposit_list += f"   {status_emoji_tag()} *স্ট্যাটাস:* {status_text}\n"
        deposit_list += f"   📅 *তারিখ:* {d[5]}\n\n"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        render_body_text(
            f"📋 *আমার ডিপোজিট রিকোয়েস্ট*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"{deposit_list}"
            f"*মোট রিকোয়েস্ট:* {len(deposits)}\n"
            f"*⏳ অপেক্ষমান:* {len(pending)}"
        ),
        call.message.chat.id, call.message.message_id,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Back", callback_data='back_deposit')
        ),
        parse_mode='HTML'
    )

def handle_admin_deposit_panel(message):
    """Handle admin deposit panel"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    keyboard = create_otp_deposite_keyboard()
    
    bot.reply_to(message, 
        render_body_text(
            f"💰 *DEPOSITE SYSTEM*\n"  # <-- এখানে 💰 ব্যবহার করা হয়েছে
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def handle_admin_show_deposits(message):
    """Show all deposit requests for admin"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    pending_deposits = get_pending_deposits()
    
    if not pending_deposits:
        bot.reply_to(message, 
            render_body_text(
                f"📋 *SHOW ALL DEPOSITE REQUEST*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো ডিপোজিট রিকোয়েস্ট নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for dep in pending_deposits:
        dep_id = dep[0]
        user_id_dep = dep[1]
        amount = dep[2]
        method = dep[3]
        trx_id = dep[4]
        
        user_name = "Unknown"
        for u in all_users:
            if u["id"] == user_id_dep:
                user_name = u["name"]
                break
        
        keyboard.add(
            types.InlineKeyboardButton(
                f"✅ {user_name[:10]} - ৳{amount:.0f}",
                callback_data=f'approve_dep_{dep_id}'
            ),
            types.InlineKeyboardButton(
                f"❌ Reject",
                callback_data=f'reject_dep_{dep_id}'
            )
        )
    
    keyboard.add(types.InlineKeyboardButton("𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾", callback_data='back_admin_panel'))
    
    bot.reply_to(message, 
        render_body_text(
            f"📋 *সব ডিপোজিট রিকোয়েস্ট*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *{len(pending_deposits)} টি অপেক্ষমান রিকোয়েস্ট:*"
        ),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

def handle_admin_set_deposit(message):
    """Handle set deposit number and ID"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"⚙️ *SET DEPOSIT NUMBER AND ID*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *ফরম্যাট:* `মেথড_নাম: নম্বর/আইডি: ন্যূনতম_পরিমাণ`\n\n"
            f"Example:\n"
            f"`bKash: 017xxxxxxxx: 10`\n"
            f"`Nagad: 017xxxxxxxx: 10`\n"
            f"`Binance: binance_pay_id: 0.1`\n\n"
            f"💡 *একাধিক মেথড একসাথে দিন*\n"
            f"💡 *ন্যূনতম পরিমাণ BDT (Binance এর জন্য USDT)*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_admin_set_deposit)

def process_admin_set_deposit(message):
    """Process set deposit number and ID"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    lines = text.split('\n')
    success_count = 0
    
    for line in lines:
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                name = parts[0].strip()
                number = parts[1].strip()
                min_deposit = 10.0
                if len(parts) >= 3:
                    try:
                        min_deposit = float(parts[2].strip())
                    except:
                        pass
                
                if save_payment_method(name, number, min_deposit):
                    success_count += 1
    
    if success_count > 0:
        bot.reply_to(message, 
            render_body_text(
                f"✅ *{success_count} টি পেমেন্ট মেথড সেট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সফলভাবে আপডেট করা হয়েছে*"
            ),
            parse_mode='HTML'
        )
    else:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *কোনো মেথড সেট করা হয়নি!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সঠিক ফরম্যাট ব্যবহার করুন:*\n"
                f"`মেথড_নাম: নম্বর/আইডি: ন্যূনতম`"
            ),
            parse_mode='HTML'
        )

# ==================== DELETE PAYMENT METHOD ====================

# Keep payment-method deletion state separate from premium-plan deletion
# state.  Both flows use the same Bengali confirmation labels, so routing
# must be based on the active flow instead of the button text alone.
payment_delete_state = {}

def handle_admin_delete_payment_method(message):
    """Handle delete payment method - with colored reply buttons"""
    user_id = message.from_user.id
    # Starting this screen cancels any previous payment-delete confirmation.
    payment_delete_state.pop(user_id, None)
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    methods = get_payment_methods()
    if not methods:
        bot.reply_to(message, 
            render_body_text(f"❌ *কোনো পেমেন্ট মেথড নেই!*"), 
            parse_mode='HTML'
        )
        return
    
    # 🔥 রিপ্লাই কীবোর্ড তৈরি করুন - কালার সহ
    markup = create_delete_payment_keyboard()
    
    bot.reply_to(message, 
        render_body_text(
            f"🗑️ *DELETE PAYMENT METHOD*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *যে মেথড ডিলিট করতে চান সিলেক্ট করুন:*"
        ),
        reply_markup=markup,  # ✅ রিপ্লাই কীবোর্ড
        parse_mode='HTML'
    )

def process_delete_payment_method(call):
    """Process delete payment method"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    method_name = call.data.split('_')[2]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ হ্যাঁ, ডিলিট করুন", callback_data=f'confirm_delete_method_{method_name}'),
        types.InlineKeyboardButton("❌ না, বাতিল করুন", callback_data='cancel_delete_method')
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        render_body_text(
            f"⚠️ *আপনি কি নিশ্চিত?*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *মেথড:* `{method_name}`\n\n"
            f"❌ *এটি ডিলিট করলে আর ফেরত আসবে না!*"
        ),
        call.message.chat.id, call.message.message_id,
        reply_markup=markup,
        parse_mode='HTML'
    )

def process_confirm_delete_method(call):
    """Confirm delete payment method"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    method_name = call.data.split('_')[3]
    
    if delete_payment_method(method_name):
        bot.answer_callback_query(call.id, f"✅ {method_name} ডিলিট করা হয়েছে!", show_alert=True)
        bot.edit_message_text(
            render_body_text(
                f"✅ *পেমেন্ট মেথড ডিলিট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ *মেথড:* `{method_name}`\n"
                f"✅ *সফলভাবে রিমুভ করা হয়েছে!*"
            ),
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "❌ ডিলিট করতে ব্যর্থ হয়েছে!", show_alert=True)

def process_cancel_delete_method(call):
    """Cancel delete payment method"""
    bot.answer_callback_query(call.id, "❌ ডিলিট বাতিল করা হয়েছে!")
    bot.edit_message_text(
        render_body_text(f"❌ *ডিলিট বাতিল করা হয়েছে!*"),
        call.message.chat.id, call.message.message_id,
        parse_mode='HTML'
    )
    handle_admin_deposit_panel(call.message)

# ==================== APPROVE/REJECT DEPOSIT - COMPLETE FIX ====================

def handle_approve_deposit(call):
    """Handle approve deposit from admin"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    dep_id = int(call.data.split('_')[2])
    
    success, amount = approve_deposit(dep_id, user_id)
    
    if success:
        bot.answer_callback_query(call.id, f"✅ Deposit Approved! (৳{amount:.2f})", show_alert=True)
        
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT user_id, amount, method, trx_id FROM deposits_new WHERE id = ?", (dep_id,))
        dep = c.fetchone()
        conn.close()
        
        if dep:
            target_user = dep[0]
            dep_amount = dep[1]
            method = dep[2]
            trx_id = dep[3]
            method_name = get_payment_method_label(method)
            method_emoji = get_payment_method_emoji(method_name)
            
            try:
                bot.send_message(
                    target_user,
                    render_body_text(
                        f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji> *Deposit Approved!*\n'
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"💰 *Amount:* {dep_amount:.2f} "
                        f"{'USDT' if str(method).lower() == 'binance' else 'BDT'}\n"
                        f"💵 *Credited:* ৳{amount:.2f}\n"
                        f"{method_emoji} *Method:* {method_name}\n"
                        f"🧾 *TrxID:* `{trx_id}`\n\n"
                        f"🎉 *Your {balance_emoji_tag()} balance has been updated!*"
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to notify user {target_user}: {e}")
        
        # ✅ English Approve Message
        try:
            bot.edit_message_text(
                render_body_text(
                    f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji> *Deposit Approved!*\n'
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"🆔 *ID:* `{dep_id}`\n"
                    f"💰 *Amount:* ৳{amount:.2f}\n"
                    f'<tg-emoji emoji-id="{EMOJI_SUCCESS}">✅</tg-emoji> *Successfully approved!*'
                ),
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
        
    else:
        bot.answer_callback_query(call.id, "❌ Approve failed!", show_alert=True)

def handle_reject_deposit(call):
    """Handle reject deposit from admin"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    dep_id = int(call.data.split('_')[2])
    
    success = reject_deposit(dep_id, user_id)
    
    if success:
        bot.answer_callback_query(call.id, "❌ Deposit Rejected!", show_alert=True)
        
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT user_id, amount, method, trx_id FROM deposits_new WHERE id = ?", (dep_id,))
        dep = c.fetchone()
        conn.close()
        
        if dep:
            target_user = dep[0]
            dep_amount = dep[1]
            method = dep[2]
            method_name = get_payment_method_label(method)
            method_emoji = get_payment_method_emoji(method_name)
            
            try:
                bot.send_message(
                    target_user,
                    render_body_text(
                        f"❌ *Deposit Rejected!*\n"
                        f"━━━━━━━━━━━━━━━━━\n\n"
                        f"💰 *Amount:* ৳{dep_amount:.2f}\n"
                        f"{method_emoji} *Method:* {method_name}\n\n"
                        f"😞 *Please try again with correct information.*"
                    ),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to notify user {target_user}: {e}")
        
        try:
            bot.edit_message_text(
                render_body_text(
                    f"❌ *Deposit Rejected!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"🆔 *ID:* `{dep_id}`\n"
                    f"❌ *Successfully rejected!*"
                ),
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
    else:
        bot.answer_callback_query(call.id, "❌ Reject failed!", show_alert=True)

# ==================== SET GROUP FUNCTIONS ====================

def handle_set_group(message):
    """Handle set group ID for deposit notifications"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"👥 *SET GROUP FOR REQUEST*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *গ্রুপ আইডি লিখুন:*\n\n"
            f"💡 *গ্রুপ আইডি পেতে গ্রুপে একটি মেসেজ ফরওয়ার্ড করে @username_to_id_bot ব্যবহার করুন*\n"
            f"💡 *খালি রাখতে 'none' লিখুন*\n\n"
            f"📊 *বর্তমান গ্রুপ:* {get_setting('group_id') or 'সেট করা নেই'}"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_set_group)

def process_set_group(message):
    """Process set group ID"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text.lower() == 'none':
        set_setting('group_id', '')
        bot.reply_to(message, 
            render_body_text(
                f"✅ *গ্রুপ সেটিং রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *এখন থেকে রিকোয়েস্ট অ্যাডমিনদের কাছে যাবে*"
            ),
            parse_mode='HTML'
        )
        return
    
    if not text.startswith('-') and not text.isdigit():
        bot.reply_to(message, "❌ *ইনভ্যালিড গ্রুপ আইডি!*\n💡 গ্রুপ আইডি সাধারণত নেগেটিভ নাম্বার হয়", parse_mode='HTML')
        return
    
    set_setting('group_id', text)
    
    bot.reply_to(message, 
        render_body_text(
            f"✅ *গ্রুপ সেট করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *গ্রুপ আইডি:* `{text}`\n"
            f"✅ *সব ডিপোজিট রিকোয়েস্ট এখন ঐ গ্রুপে যাবে*\n"
            f"⚠️ *বটকে অবশ্যই গ্রুপে অ্যাডমিন দিতে হবে!*"
        ),
        parse_mode='HTML'
    )
#
@bot.message_handler(func=lambda message: any(
    plan.get('plan_name', '') in message.text for plan in premium_plans
) and "🗑️" not in (message.text or "")
   and "Back" not in (message.text or "")
   # A confirmation button also contains the plan name.  It must be handled
   # by handle_confirm_remove_plan, not treated as a fresh plan selection.
   and not (message.text or "").startswith("হ্যাঁ,")
   and (message.text or "") != "না, বাতিল করুন")
def handle_remove_plan_from_reply(message):
    """Handle remove plan from reply keyboard"""
    user_id = message.from_user.id
    text = message.text or ""
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    # প্লান নাম বের করুন
    for plan in premium_plans:
        if plan.get('plan_name', '') in text:
            # কনফার্মেশন জিজ্ঞেস করুন
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(
                make_keyboard_button(
                    f"✅ হ্যাঁ, {plan['plan_name']} ডিলিট করুন",
                    EMOJI_APPROVE,
                    "success"
                ),
                make_keyboard_button("না, বাতিল করুন", EMOJI_REJECT, "danger")
            )
            
            bot.reply_to(
                message,
                render_body_text(
                    f"⚠️ *আপনি কি নিশ্চিত?*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 *প্লান:* {plan['plan_name']}\n"
                    f"📁 ফাইল: {plan['file_limit']} টি\n"
                    f"📅 দিন: {plan['days']}\n"
                    f"{price_emoji_tag()} মূল্য: ৳{plan['price']}\n\n"
                    f"❌ *ডিলিট করলে আর ফেরত আসবে না!*"
                ),
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # ইউজার স্টেট সেভ করুন
            if not hasattr(handle_remove_plan_from_reply, 'user_state'):
                handle_remove_plan_from_reply.user_state = {}
            handle_remove_plan_from_reply.user_state[user_id] = {"plan_id": plan['id']}
            return
    
    bot.reply_to(message, "❌ *প্লান পাওয়া যায়নি!*", parse_mode='HTML')

@bot.message_handler(func=lambda message: (
    (
        (message.text or "").startswith("হ্যাঁ,")
        or (message.text or "") == "না, বাতিল করুন"
    )
    # Do not let this Premium Plan handler consume the same confirmation
    # labels used by the payment-method deletion flow.
    and message.from_user.id in getattr(handle_remove_plan_from_reply, "user_state", {})
))
def handle_confirm_remove_plan(message):
    """Handle confirm remove plan"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "না, বাতিল করুন":
        handle_remove_plan_from_reply.user_state.pop(user_id, None)
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ডিলিট বাতিল করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো প্লান ডিলিট করা হয়নি*"
            ),
            parse_mode='HTML'
        )
        handle_remove_premium_plan(message)
        return
    
    # প্লান আইডি বের করুন
    user_state = getattr(handle_remove_plan_from_reply, 'user_state', {})
    plan_id = user_state.get(user_id, {}).get('plan_id')
    
    if not plan_id:
        bot.reply_to(message, "❌ *প্লান পাওয়া যায়নি!*", parse_mode='HTML')
        return
    
    if remove_premium_plan(plan_id):
        bot.reply_to(message, 
            render_body_text(
                f"✅ *প্লান ডিলিট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ *প্লান আইডি:* `{plan_id}`\n"
                f"✅ *সফলভাবে রিমুভ করা হয়েছে!*"
            ),
            parse_mode='HTML'
        )
        # ইউজার স্টেট ক্লিয়ার করুন
        if user_id in user_state:
            del user_state[user_id]
    else:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ডিলিট করতে ব্যর্থ হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )
    
    # প্লান লিস্ট দেখান
    handle_remove_premium_plan(message)

@bot.message_handler(func=lambda message: message.text in (
    "🔙 Back to Premium Admin",
    "Back to Premium Admin",
))
def handle_back_to_premium_admin_from_remove(message):
    """Handle back to premium admin from remove plan"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    handle_premium_plan_admin(message)
# ==================== SET FILE FORWARD GROUP ====================

def handle_set_file_forward_group(message):
    """Handle set file forward group ID"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    current_group = get_file_forward_group() or "সেট করা নেই"
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"📤 *SET FILE FORWARD GROUP*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *গ্রুপ আইডি লিখুন যেখানে ফাইল ফরওয়ার্ড হবে:*\n\n"
            f"💡 *গ্রুপ আইডি পেতে গ্রুপে একটি মেসেজ ফরওয়ার্ড করে @username_to_id_bot ব্যবহার করুন*\n"
            f"💡 *খালি রাখতে 'none' লিখুন*\n\n"
            f"📊 *বর্তমান গ্রুপ:* `{current_group}`"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_set_file_forward_group)

def process_set_file_forward_group(message):
    """Process set file forward group ID"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text.lower() == 'none':
        set_file_forward_group('')
        bot.reply_to(message, 
            render_body_text(
                f"✅ *ফাইল ফরওয়ার্ড গ্রুপ রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *এখন থেকে কোনো ফাইল ফরওয়ার্ড হবে না*"
            ),
            parse_mode='HTML'
        )
        return
    
    if not text.startswith('-') and not text.isdigit():
        bot.reply_to(message, "❌ *ইনভ্যালিড গ্রুপ আইডি!*\n💡 গ্রুপ আইডি সাধারণত নেগেটিভ নাম্বার হয়", parse_mode='HTML')
        return
    
    set_file_forward_group(text)
    
    bot.reply_to(message, 
        render_body_text(
            f"✅ *ফাইল ফরওয়ার্ড গ্রুপ সেট করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *গ্রুপ আইডি:* `{text}`\n"
            f"✅ *সব ফাইল এখন ঐ গ্রুপে ফরওয়ার্ড হবে*\n"
            f"⚠️ *বটকে অবশ্যই গ্রুপে অ্যাডমিন দিতে হবে!*"
        ),
        parse_mode='HTML'
    )

# ==================== PREMIUM PLAN FUNCTIONS - COMPLETE FIX ====================

def show_all_plans(message):
    """Show all premium plans in a nice list with premium emojis"""
    if not premium_plans:
        bot.reply_to(message, 
            render_body_text(
                f"📋 *প্রিমিয়াম প্লান লিস্ট*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো প্লান যোগ করা নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    plan_text = render_body_text(f"📋 *প্রিমিয়াম প্লানসমূহ*\n")
    plan_text += f"━━━━━━━━━━━━━━━━━\n\n"
    
    for i, plan in enumerate(premium_plans, 1):
        plan_text += render_body_text(
            f"<blockquote>"
            f"📌 *প্লান #{i}*\n"
            f"   ├ 📁 *ফাইল লিমিট:* {plan['file_limit']} টি\n"
            f"   ├ 📅 *দিন:* {plan['days']} দিন\n"
            f"   └ {price_emoji_tag()} *মূল্য:* ৳{plan['price']}"
            f"</blockquote>\n\n"
        )
    
    plan_text += render_body_text(
        f"📊 *মোট প্লান:* {len(premium_plans)} টি"
    )
    
    bot.reply_to(message, plan_text, parse_mode='HTML')

def handle_premium_plan_user(message, user_id=None):
    # Callback messages are authored by the bot; use call.from_user when a
    # callback passes the real user ID explicitly.
    user_id = user_id if user_id is not None else message.from_user.id
    
    if not premium_plans:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *কোনো প্রিমিয়াম প্লান উপলব্ধ নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    # 🔥 2nd screenshot style টেক্সট
    plan_text = render_body_text(
        f'<tg-emoji emoji-id="{EMOJI_PREMIUM_PLAN_USER}">🌟</tg-emoji> '
        f"<b>ALL PRIMIUM PLAN</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i, plan in enumerate(premium_plans, 1):
        # 🔥 USDT রেট ক্যালকুলেট
        usdt_price = plan['price'] / get_usdt_rate()
        
        plan_text += render_body_text(
            f"<blockquote>"
            f"📌 *প্ল্যান: {plan.get('plan_name', 'Basic')}*\n"
            f"   ├ 📁 *ফাইল লিমিট:* {plan['file_limit']} টি\n"
            f"   ├ 📅 *মেয়াদ:* {plan['days']} দিন\n"
            f"   └ {price_emoji_tag()} *মূল্য:* ৳{plan['price']} (~{usdt_price:.2f} USDT)"
            f"</blockquote>\n\n"
        )
    
    # 🔥 বর্তমান প্ল্যান দেখান
    premium = get_user_premium_plan(user_id)
    if premium and premium["expiry"] > datetime.now():
        plan_text += render_body_text(
            f"〽️ *আপনার বর্তমান প্ল্যান:*\n"
            f"   ├ 📁 লিমিট: {premium['file_limit']} ফাইল\n"
            f"   └ 📅 শেষ: {premium['expiry'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    plan_text += render_body_text(
        f"👇 *নিচের বাটনে ক্লিক করে প্ল্যান কিনুন:*"
    )
    
    # 🔥 Reply Keyboard (MY INFO বাদ)
    markup = create_premium_plans_reply_keyboard()
    
    bot.reply_to(message, plan_text, reply_markup=markup, parse_mode='HTML')

def handle_buy_plan(message):
    """Handle buy plan"""
    user_id = message.from_user.id
    
    if not premium_plans:
        bot.reply_to(message, "❌ *কোনো প্লান উপলব্ধ নেই!*", parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for plan in premium_plans:
        plan_emoji = "📌"
        if "basic" in plan.get('plan_name', '').lower():
            plan_emoji = "📌"
        elif "vip" in plan.get('plan_name', '').lower():
            plan_emoji = "⭐"
        
        markup.add(types.InlineKeyboardButton(
            f"{plan_emoji} {plan.get('plan_name', 'Basic')} - {plan['days']} days - ৳{plan['price']}",
            callback_data=f'buy_plan_{plan["id"]}'
        ))
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_premium'))
    
    bot.reply_to(message, 
        render_body_text(
            f"💳 *প্লান সিলেক্ট করুন:*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *আপনি কোন প্লান কিনতে চান?*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def process_buy_plan(call):
    """Process buy plan with new balance system"""
    user_id = call.from_user.id
    plan_id = int(call.data.split('_')[2])
    
    plan = None
    for p in premium_plans:
        if p["id"] == plan_id:
            plan = p
            break
    
    if not plan:
        bot.answer_callback_query(call.id, "❌ প্লান পাওয়া যায়নি!")
        return
    
    balance = get_user_balance_db(user_id)
    
    if balance < plan["price"]:
        bot.answer_callback_query(call.id, f"❌ ব্যালেন্স কম! প্রয়োজন: ৳{plan['price']}", show_alert=True)
        return
    
    expiry = datetime.now() + timedelta(days=plan["days"])
    if not update_user_balance_db(user_id, -plan["price"]):
        bot.answer_callback_query(
            call.id,
            "❌ ব্যালেন্স আপডেট করা যায়নি। আবার চেষ্টা করুন।",
            show_alert=True,
        )
        return

    if not save_user_premium_plan(
        user_id, plan["id"], expiry, plan["file_limit"]
    ):
        update_user_balance_db(user_id, plan["price"])
        bot.answer_callback_query(
            call.id,
            "❌ প্লান অ্যাক্টিভেট করা যায়নি; টাকা ফেরত দেওয়া হয়েছে।",
            show_alert=True,
        )
        return
    
    for u in all_users:
        if u["id"] == user_id:
            u["balance"] = get_user_balance_db(user_id)
            break
    
    bot.answer_callback_query(call.id, "✅ প্লান অ্যাক্টিভেটেড!")
    bot.edit_message_text(
        render_body_text(
            f"🎉 *প্লান সফলভাবে অ্যাক্টিভেটেড!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📁 *ফাইল লিমিট:* {plan['file_limit']} ফাইল\n"
            f"📅 *দিন:* {plan['days']} দিন\n"
            f"{price_emoji_tag()} *মূল্য:* ৳{plan['price']}\n"
            f"📅 *শেষ তারিখ:* {expiry.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"{balance_emoji_tag()} *বর্তমান ব্যালেন্স:* ৳{get_user_balance_db(user_id):.2f}"
        ),
        call.message.chat.id, call.message.message_id,
        parse_mode='HTML'
    )

def handle_premium_plan_admin(message, user_id=None):
    """Handle premium plan admin"""
    user_id = user_id if user_id is not None else message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    # 🔥 অ্যাডমিনের জন্য টেক্সট
    admin_text = render_body_text(
        f'<tg-emoji emoji-id="{EMOJI_PREMIUM_PLAN_USER}">🌟</tg-emoji> '
        f"<b>ALL PRIMIUM PLAN</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉\n\n"
    )
    
    # 🔥 বর্তমান প্ল্যান দেখান
    if premium_plans:
        admin_text += render_body_text(
            f"📊 *বর্তমান প্ল্যানসমূহ:*\n"
            f"━━━━━━━━━━━━━━━━━\n"
        )
        for i, plan in enumerate(premium_plans, 1):
            admin_text += render_body_text(
                f"<blockquote>"
                f"📌 *প্ল্যান #{i}*\n"
                f"   ├ 📁 ফাইল লিমিট: {plan['file_limit']}\n"
                f"   ├ 📅 দিন: {plan['days']}\n"
                f"   └ {price_emoji_tag()} মূল্য: ৳{plan['price']}"
                f"</blockquote>\n\n"
            )
        admin_text += render_body_text(
            f"📊 *মোট প্ল্যান:* {len(premium_plans)} টি\n\n"
        )
    else:
        admin_text += render_body_text(
            f"📌 *কোনো প্ল্যান যোগ করা নেই!*\n\n"
        )
    
    admin_text += render_body_text(
        f"👇 *নিচের বাটনে ক্লিক করুন:*"
    )
    
    # 🔥 Reply Keyboard
    # Use the keyboard builder that is defined above.  The old function name
    # did not exist, so clicking "Set Premium Plan" raised NameError and the
    # bot sent no response.
    markup = create_premium_admin_keyboard()
    
    bot.reply_to(message, admin_text, reply_markup=markup, parse_mode='HTML')

def handle_add_premium_plan(message):
    """Handle add premium plan with plan name"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"➕ *Add Your Premium Plan*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *ফরম্যাট:* `প্লান_নাম ফাইল_লিমিট দিন মূল্য`\n\n"
            f"Example:\n"
            f"`Basic 100 30 500`\n"
            f"`VIP-1 200 60 1000`\n"
            f"`VIP-2 500 90 2000`\n\n"
            f"📁 *প্লান_নাম:* Basic, VIP-1, VIP-2 ইত্যাদি\n"
            f"📁 *ফাইল_লিমিট:* কয়টা ফাইল আপলোড করতে পারবে\n"
            f"📅 *দিন:* কত দিন থাকবে\n"
            f"{price_emoji_tag()} *মূল্য:* কত টাকা"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_add_premium_plan)

def process_add_premium_plan(message):
    """Process add premium plan with plan name"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    parts = text.split()
    if len(parts) != 4:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ভুল ফরম্যাট!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সঠিক ফরম্যাট:* `প্লান_নাম ফাইল_লিমিট দিন মূল্য`\n"
                f"Example: `Basic 100 30 500`"
            ),
            parse_mode='HTML'
        )
        return
    
    try:
        plan_name = parts[0]
        file_limit = int(parts[1])
        days = int(parts[2])
        price = int(parts[3])
        
        if file_limit <= 0:
            bot.reply_to(message, "❌ *ফাইল লিমিট ০ এর বেশি হতে হবে!*", parse_mode='HTML')
            return
        if days <= 0:
            bot.reply_to(message, "❌ *দিন ০ এর বেশি হতে হবে!*", parse_mode='HTML')
            return
        if price <= 0:
            bot.reply_to(message, "❌ *মূল্য ০ এর বেশি হতে হবে!*", parse_mode='HTML')
            return
        
        if save_premium_plan(file_limit, days, price, plan_name):
            show_all_plans(message)
        else:
            bot.reply_to(message, 
                render_body_text(
                    f"❌ *প্লান যোগ করতে ব্যর্থ হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 *ডাটাবেজ সংযোগ সমস্যা*\n"
                    f"💡 *দয়া করে আবার চেষ্টা করুন*"
                ),
                parse_mode='HTML'
            )
            
    except ValueError:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *শুধু সংখ্যা দিন!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সঠিক ফরম্যাট:* `প্লান_নাম ফাইল_লিমিট দিন মূল্য`\n"
                f"Example: `Basic 100 30 500`"
            ),
            parse_mode='HTML'
        )

def handle_remove_premium_plan(message):
    """Handle remove premium plan - REPLY KEYBOARD with premium emojis"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not premium_plans:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *কোনো প্লান নেই!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *প্রথমে প্লান যোগ করুন*"
            ),
            parse_mode='HTML'
        )
        return
    
    # 🔥 রিপ্লাই কীবোর্ড তৈরি করুন
    markup = create_remove_plan_reply_keyboard()
    
    # প্লান লিস্ট টেক্সট
    plan_list_text = render_body_text(
        f"🗑️ *Remove Plan*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *যে প্লান ডিলিট করতে চান সিলেক্ট করুন:*\n\n"
    )
    
    for i, plan in enumerate(premium_plans, 1):
        plan_emoji = "📌" if "basic" in plan.get('plan_name', '').lower() else "⭐"
        plan_list_text += render_body_text(
            f"{i}. {plan_emoji} *{plan.get('plan_name', 'Basic')}*\n"
            f"   ├ 📁 ফাইল: {plan['file_limit']} টি\n"
            f"   ├ 📅 দিন: {plan['days']}\n"
            f"   └ {price_emoji_tag()} মূল্য: ৳{plan['price']}\n\n"
        )
    
    plan_list_text += render_body_text(
        f"💡 *নিচের বাটনে ক্লিক করে প্লান ডিলিট করুন*"
    )
    
    bot.reply_to(message, plan_list_text, reply_markup=markup, parse_mode='HTML')

def process_remove_plan(call):
    """Process remove plan"""
    user_id = call.from_user.id
    plan_id = int(call.data.split('_')[2])
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    if remove_premium_plan(plan_id):
        bot.answer_callback_query(call.id, "✅ প্লান রিমুভ করা হয়েছে!")
        bot.edit_message_text(
            render_body_text(
                f"✅ *প্লান রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ প্লান আইডি: `{plan_id}`\n\n"
                f"✅ *সফলভাবে রিমুভ করা হয়েছে!*"
            ),
            call.message.chat.id, call.message.message_id,
            parse_mode='HTML'
        )
        show_all_plans(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ রিমুভ করতে ব্যর্থ হয়েছে!", show_alert=True)

def handle_reset_all_plans(message):
    """Handle reset all premium plans"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("✅ হ্যাঁ, রিসেট করুন", callback_data='confirm_reset_plans'),
        types.InlineKeyboardButton("❌ না, বাতিল করুন", callback_data='cancel_reset_plans')
    )
    
    bot.reply_to(message, 
        render_body_text(
            f"⚠️ *সব প্রিমিয়াম প্লান রিসেট করতে চান?*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *বর্তমানে {len(premium_plans)} টি প্লান আছে*\n\n"
            f"❌ *রিসেট করলে সব প্লান ডিলিট হয়ে যাবে!*\n"
            f"✅ *এরপর নতুন প্লান যোগ করতে পারবেন*\n\n"
            f"💡 *আপনি কি নিশ্চিত?*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def process_reset_plans(call):
    """Process reset all plans"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    try:
        if reset_all_plans():
            bot.answer_callback_query(call.id, "✅ সব প্লান রিসেট করা হয়েছে!")
            bot.edit_message_text(
                render_body_text(
                    f"✅ *সব প্রিমিয়াম প্লান রিসেট করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 *এখন নতুন প্লান যোগ করলে আইডি ১ থেকে শুরু হবে*\n\n"
                    f"💡 *প্লান যোগ করতে '𝘼𝙙𝙙 𝙋𝙡𝙖𝙣' বাটনে ক্লিক করুন*"
                ),
                call.message.chat.id, call.message.message_id,
                parse_mode='HTML'
            )
            logger.info(f"✅ All plans reset by Admin {user_id}")
        else:
            bot.answer_callback_query(call.id, "❌ রিসেট করতে ব্যর্থ হয়েছে!", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ রিসেট করতে ব্যর্থ হয়েছে!", show_alert=True)
        logger.error(f"❌ Error resetting plans: {e}")

def process_cancel_reset(call):
    """Process cancel reset"""
    bot.answer_callback_query(call.id, "❌ রিসেট বাতিল করা হয়েছে!")
    bot.edit_message_text(
        render_body_text(
            f"❌ *রিসেট বাতিল করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *আপনার প্লান নিরাপদ আছে*"
        ),
        call.message.chat.id, call.message.message_id,
        parse_mode='HTML'
    )
    handle_premium_plan_admin(call.message, user_id=call.from_user.id)

# ==================== OTP ADMIN FUNCTIONS ====================

def handle_otp_admin_panel(message):
    """Handle OTP admin panel"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    markup = create_otp_reply_keyboard(user_id)
    bot.reply_to(message, 
        render_body_text(
            f"🔴 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 \n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝘿𝙈𝙄𝙉❗\n"
            f"✅ 𝙔𝙊𝙐 𝙃𝘼𝙑𝙀 𝙁𝙐𝙇𝙇 𝘼𝘾𝘾𝙀𝙎𝙎 𝙏𝙊 𝘽𝙊𝙏 𝘾𝙊𝙉𝙏𝙍𝙊𝙇𝙎\n\n"
            f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )


# ==========================================
# ✅ LIVE BOT EMOJI EDITOR
# ==========================================
def build_edit_bot_buttons_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "📝 Edit Button Premium Emoji ID",
            callback_data="editbot:buttons"
        ),
        types.InlineKeyboardButton(
            "💬 Edit Reply Message Emoji ID",
            callback_data="editbot:replies"
        ),
        types.InlineKeyboardButton(
            "🔙 Back to GX Admin Panel",
            callback_data="editbot:home"
        )
    )
    return markup


def _short_edit_label(label, max_length=34):
    label = str(label)
    return label if len(label) <= max_length else f"{label[:max_length - 1]}…"


def build_editable_button_list():
    specs = get_editable_button_specs()
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(
        "💬 Edit Reply Message Emojis",
        callback_data="editbot:replies"
    ))
    for index, spec in enumerate(specs):
        markup.add(types.InlineKeyboardButton(
            f"{index + 1}. {_short_edit_label(spec['label'])}",
            callback_data=f"editbot:b:{index}"
        ))
    markup.add(types.InlineKeyboardButton(
        "🔙 Back to GX Admin Panel",
        callback_data="editbot:home"
    ))
    return markup


def build_editable_body_emoji_list():
    specs = get_editable_body_emoji_specs()
    markup = types.InlineKeyboardMarkup(row_width=2)
    row = []
    for index, spec in enumerate(specs):
        row.append(types.InlineKeyboardButton(
            f"{spec['label']}  {index + 1}",
            callback_data=f"editbot:r:{index}"
        ))
        if len(row) == 2:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    markup.add(types.InlineKeyboardButton(
        "🔙 Back",
        callback_data="editbot:menu"
    ))
    return markup


def handle_edit_bot_buttons(message):
    """Open the live button/reply emoji editor from the GX Admin Panel."""
    user_id = message.from_user.id
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return

    bot.reply_to(
        message,
        render_body_text(
            "🛠️ *EDIT BOT BUTTON*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "নিচে বটের সব reply-keyboard button দেখানো হলো। যেকোনো একটি "
            "select করে Premium Emoji ID পরিবর্তন করুন।\n"
            "Reply message-এর emoji বদলাতে উপরের button-টি ব্যবহার করুন।\n"
            "পরিবর্তনগুলো database-এ save হবে এবং bot restart ছাড়াই নতুন "
            "message/keyboard-এ কাজ করবে।"
        ),
        reply_markup=build_editable_button_list(),
        parse_mode='HTML'
    )


def _edit_bot_editor_message(call, text, markup):
    try:
        bot.edit_message_text(
            render_body_text(text),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Could not update emoji editor message: {e}")


def handle_edit_bot_callback(call):
    """Route the inline choices used by the live emoji editor."""
    user_id = call.from_user.id
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return

    data = call.data or ""
    if data in ("editbot:menu", "editbot:home"):
        bot.answer_callback_query(call.id)
        if data == "editbot:home":
            handle_otp_admin_panel(call.message)
        else:
            _edit_bot_editor_message(
                call,
                "🛠️ *EDIT BOT BUTTON*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "কোন ধরনের Premium Emoji ID পরিবর্তন করবেন?",
                build_edit_bot_buttons_menu()
            )
        return

    if data == "editbot:buttons":
        bot.answer_callback_query(call.id)
        _edit_bot_editor_message(
            call,
            "📝 *SELECT A BOT BUTTON*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "যে button-এর Premium Emoji ID পরিবর্তন করতে চান সেটি select করুন।",
            build_editable_button_list()
        )
        return

    if data == "editbot:replies":
        bot.answer_callback_query(call.id)
        _edit_bot_editor_message(
            call,
            "💬 *SELECT A REPLY EMOJI*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "Reply message-এ ব্যবহৃত emoji select করুন।",
            build_editable_body_emoji_list()
        )
        return

    if data.startswith("editbot:b:"):
        try:
            index = int(data.rsplit(":", 1)[1])
            spec = get_editable_button_specs()[index]
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "❌ Button পাওয়া যায়নি!", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        prompt = bot.send_message(
            call.message.chat.id,
            render_body_text(
                f"📝 *Button Emoji ID Change*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🔘 *Button:* `{spec['label']}`\n"
                f"🆔 *Current ID:* `{spec['current_id']}`\n\n"
                f"নতুন Premium Emoji ID পাঠান:\n"
                f"উদাহরণ: `6246919169120408471`\n\n"
                f"শুধু numeric ID পাঠাবেন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(
            prompt,
            process_edit_button_emoji_id,
            spec["label"]
        )
        return

    if data.startswith("editbot:r:"):
        try:
            index = int(data.rsplit(":", 1)[1])
            spec = get_editable_body_emoji_specs()[index]
        except (ValueError, IndexError):
            bot.answer_callback_query(call.id, "❌ Emoji পাওয়া যায়নি!", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        prompt = bot.send_message(
            call.message.chat.id,
            render_body_text(
                f"💬 *Reply Emoji ID Change*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"Emoji: {spec['label']}\n"
                f"🆔 *Current ID:* `{spec['current_id']}`\n\n"
                f"নতুন Premium Emoji ID পাঠান:\n"
                f"উদাহরণ: `6246919169120408471`\n\n"
                f"শুধু numeric ID পাঠাবেন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(
            prompt,
            process_edit_reply_emoji_id,
            spec["label"]
        )
        return

    bot.answer_callback_query(call.id, "Unknown editor action.", show_alert=True)


def process_edit_button_emoji_id(message, button_label):
    user_id = message.from_user.id
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return

    emoji_id = _clean_emoji_id(message.text)
    if not emoji_id:
        bot.reply_to(
            message,
            "❌ *Invalid Premium Emoji ID!*\nশুধু numeric ID পাঠান।",
            parse_mode='HTML'
        )
        return

    if not set_setting(_emoji_setting_key("button", button_label), emoji_id):
        bot.reply_to(message, "❌ *Emoji ID save করা যায়নি!*", parse_mode='HTML')
        return

    bot.reply_to(
        message,
        render_body_text(
            f"✅ *Button Emoji Updated*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔘 *Button:* `{button_label}`\n"
            f"🆔 *New ID:* `{emoji_id}`\n\n"
            f"পরেরবার keyboard দেখালে নতুন emoji ব্যবহার হবে।"
        ),
        parse_mode='HTML'
    )
    handle_edit_bot_buttons(message)


def process_edit_reply_emoji_id(message, emoji_label):
    user_id = message.from_user.id
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return

    emoji_id = _clean_emoji_id(message.text)
    if not emoji_id:
        bot.reply_to(
            message,
            "❌ *Invalid Premium Emoji ID!*\nশুধু numeric ID পাঠান।",
            parse_mode='HTML'
        )
        return

    if not set_setting(_emoji_setting_key("body", emoji_label), emoji_id):
        bot.reply_to(message, "❌ *Emoji ID save করা যায়নি!*", parse_mode='HTML')
        return

    bot.reply_to(
        message,
        render_body_text(
            f"✅ *Reply Emoji Updated*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"Emoji: {emoji_label}\n"
            f"🆔 *New ID:* `{emoji_id}`\n\n"
            f"এখন থেকে নতুন reply message-এ এই ID ব্যবহার হবে।"
        ),
        parse_mode='HTML'
    )
    handle_edit_bot_buttons(message)

def handle_otp_ban_unban(message):
    """Handle OTP ban/unban menu"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    bot.reply_to(message, 
        render_body_text(
            f"🔴 𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=create_otp_ban_keyboard(),
        parse_mode='HTML'
    )

def handle_otp_show_banned(message):
    """Show all banned users"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not banned_users:
        bot.reply_to(message, 
            render_body_text(
                f"✅ 𝑵𝑶 𝑩𝑨𝑵𝑵𝑬𝑫 𝑼𝑺𝑬𝑹𝑺\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 বর্তমানে কোনো ব্যান করা ইউজার নেই!"
            ),
            parse_mode='HTML'
        )
        return
    
    ban_list = ""
    for i, uid in enumerate(banned_users, 1):
        user_name = "Unknown"
        for user in all_users:
            if user["id"] == uid:
                user_name = user["name"]
                break
        ban_list += f"{i}. {keep_user_name_emojis_normal(user_name)} - `{uid}`\n"
    
    bot.reply_to(message, 
        render_body_text(
            f"📋 *Banned Users List*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"{ban_list}\n"
            f"*Total Banned:* {len(banned_users)}"
        ),
        parse_mode='HTML'
    )

def handle_otp_ban_user(message):
    """Handle ban user input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"🔴 𝑩𝑨𝑵 𝑼𝑺𝑬𝑹\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 𝑺𝑬𝑵𝑫 𝑻𝑯𝑬 𝑼𝑺𝑬𝑹 𝑰𝑫 𝑻𝑶 𝑩𝑨𝑵\n\n"
            f"Example: `123456789`"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_ban_user)

def process_otp_ban_user(message):
    """Process ban user"""
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if is_user_banned(target_user):
        bot.reply_to(message, 
            render_body_text(
                f"⚠️ *Already Banned!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"User ID: `{target_user}`"
            ),
            parse_mode='HTML'
        )
    else:
        ban_user(
            target_user,
            reason=f"অ্যাডমিন {user_id} কর্তৃক ম্যানুয়ালি ব্যান",
            banned_by=user_id,
            notify=True
        )
        bot.reply_to(message, 
            render_body_text(
                f"🔴 *User Banned!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"✅ User ID: `{target_user}`\n"
                f"🔒 *এই ইউজার সফলভাবে বান করা হয়েছে!*"
            ),
            parse_mode='HTML'
        )

def handle_otp_unban_user(message):
    """Handle unban user input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"🟢 *Unban User*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Send the User ID to unban:*\n\n"
            f"Example: `123456789`"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_unban_user)

def process_otp_unban_user(message):
    """Process unban user"""
    user_id = message.from_user.id
    text = message.text.strip()

    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if not is_user_banned(target_user):
        bot.reply_to(message, 
            render_body_text(
                f"⚠️ *Not Banned!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"User ID: `{target_user}`"
            ),
            parse_mode='HTML'
        )
    else:
        unban_user(target_user, unbanned_by=user_id, notify=True)
        bot.reply_to(message, 
            render_body_text(
                f"🟢 *User Unbanned!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"✅ User ID: `{target_user}`\n"
                f"🔓 *এই ইউজার সফলভাবে আনবান করা হয়েছে!*"
            ),
            parse_mode='HTML'
        )

def handle_unban_callback(call):
    """Handle the one-tap UNBAN button sent to admins."""
    admin_id = call.from_user.id
    if not is_otp_admin(admin_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return

    try:
        target_user = int(call.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        bot.answer_callback_query(call.id, "❌ Invalid user ID.", show_alert=True)
        return

    if not unban_user(target_user, unbanned_by=admin_id, notify=True):
        bot.answer_callback_query(call.id, "⚠️ User is already unbanned.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "✅ User unbanned successfully.", show_alert=True)
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=types.InlineKeyboardMarkup()
        )
    except Exception as e:
        logger.error(f"Failed removing unban button for {target_user}: {e}")

def handle_otp_all_users(message):
    """Show all users"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    filtered_users = [u for u in all_users if u["id"] not in admin_list and u["id"] != OWNER_ID]
    
    if not filtered_users:
        bot.reply_to(message, 
            render_body_text(
                f"👥 *ALL USERS*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো ইউজার নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    user_list = ""
    for i, user in enumerate(filtered_users, 1):
        balance = get_user_balance_db(user["id"])
        user_list += f"{i}. *{keep_user_name_emojis_normal(user['name'])}*\n"
        user_list += f"   🆔 `{user['id']}`\n"
        user_list += f"   📌 {keep_user_name_emojis_normal(user['username'])}\n"
        user_list += f"   📅 {user['joined']}\n"
        user_list += f"   {balance_emoji_tag()} ব্যালেন্স: ৳{balance:.2f}\n"
        user_list += f"   📁 ফাইল: {user.get('files_count', 0)}\n\n"
    
    bot.reply_to(message, 
        render_body_text(
            f"👥 *ALL USERS*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"{user_list}"
            f"*মোট ইউজার:* {len(filtered_users)}"
        ),
        parse_mode='HTML'
    )

# ==================== ALL FILES ====================

def handle_otp_all_files(message):
    """Show all files from all users"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    all_files_data = []
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, file_name, file_type, upload_time, is_stopped FROM user_files ORDER BY upload_time DESC')
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            user_id_f = row[0]
            file_name_f = row[1]
            file_type_f = row[2]
            upload_time_f = row[3]
            is_stopped_f = row[4]
            
            user_name = "Unknown"
            user_username = "unknown"
            for u in all_users:
                if u["id"] == user_id_f:
                    user_name = u["name"]
                    user_username = u["username"]
                    break
            
            if user_name == "Unknown":
                try:
                    chat = bot.get_chat(user_id_f)
                    user_name = chat.first_name or "Unknown"
                    user_username = chat.username or "unknown"
                except:
                    pass
            
            all_files_data.append({
                "user_id": user_id_f,
                "user_name": user_name,
                "username": user_username,
                "file_name": file_name_f,
                "file_type": file_type_f,
                "upload_time": upload_time_f,
                "is_stopped": is_stopped_f
            })
    except Exception as e:
        logger.error(f"Error getting all files: {e}")
        bot.reply_to(message, "❌ *Database error!*", parse_mode='HTML')
        return
    
    if not all_files_data:
        bot.reply_to(message, 
            render_body_text(
                f"📁 *ALL FILES*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো ফাইল আপলোড করা নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    total_files = len(all_files_data)
    running_count = 0
    stopped_count = 0
    
    for f in all_files_data:
        if f["is_stopped"]:
            stopped_count += 1
        elif is_bot_running(f["user_id"], f["file_name"]):
            running_count += 1
        else:
            stopped_count += 1
    
    # Build entries separately so a large file inventory can be split across
    # Telegram messages (Telegram rejects text longer than 4096 characters).
    file_entries = []
    for i, f in enumerate(all_files_data, 1):
        status_icon = "⏹️" if f["is_stopped"] else ("🟢" if is_bot_running(f["user_id"], f["file_name"]) else "🔴")
        status_text = "Stopped" if f["is_stopped"] else ("Running" if is_bot_running(f["user_id"], f["file_name"]) else "Stopped")
        file_entries.append(
            f"{i}. {status_icon} `{f['file_name']}` ({f['file_type']})\n"
            f"   👤 {keep_user_name_emojis_normal(f['user_name'])} (@{keep_user_name_emojis_normal(f['username'])})\n"
            f"   🆔 `{f['user_id']}` - {status_text}\n\n"
        )

    summary = (
        f"📁 *ALL FILES*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total Files:* {total_files}\n"
        f"🟢 *Running:* {running_count}\n"
        f"🔴 *Stopped:* {stopped_count}\n\n"
    )

    # Keep every outgoing message comfortably below Telegram's 4096-character
    # limit after premium-emoji tags are inserted by render_body_text().
    pages = []
    current_page = ""
    for entry in file_entries:
        candidate = current_page + entry
        if current_page and len(render_body_text(summary + candidate)) > 3800:
            pages.append(current_page)
            current_page = entry
        else:
            current_page = candidate
    if current_page:
        pages.append(current_page)

    for page_number, page in enumerate(pages):
        page_header = summary if page_number == 0 else f"📁 *ALL FILES* (page {page_number + 1}/{len(pages)})\n━━━━━━━━━━━━━━━━━\n\n"
        bot_method = bot.reply_to if page_number == 0 else bot.send_message
        bot_method(
            message if page_number == 0 else message.chat.id,
            render_body_text(page_header + page),
            parse_mode='HTML'
        )

# ==================== STOP & DELETE ====================

def handle_otp_stop_delete(message):
    """Stop and delete files with selection option"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    all_files_data = []
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT user_id, file_name, file_type, upload_time, is_stopped FROM user_files ORDER BY upload_time DESC')
        rows = c.fetchall()
        conn.close()
        
        for row in rows:
            user_id_f = row[0]
            file_name_f = row[1]
            file_type_f = row[2]
            upload_time_f = row[3]
            is_stopped_f = row[4]
            
            user_name = "Unknown"
            user_username = "unknown"
            for u in all_users:
                if u["id"] == user_id_f:
                    user_name = u["name"]
                    user_username = u["username"]
                    break
            
            if user_name == "Unknown":
                try:
                    chat = bot.get_chat(user_id_f)
                    user_name = chat.first_name or "Unknown"
                    user_username = chat.username or "unknown"
                except:
                    pass
            
            all_files_data.append({
                "user_id": user_id_f,
                "user_name": user_name,
                "username": user_username,
                "file_name": file_name_f,
                "file_type": file_type_f,
                "upload_time": upload_time_f,
                "is_stopped": is_stopped_f
            })
    except Exception as e:
        logger.error(f"Error getting files for stop/delete: {e}")
        bot.reply_to(message, "❌ *Database error!*", parse_mode='HTML')
        return
    
    if not all_files_data:
        bot.reply_to(message, 
            render_body_text(
                f"🗑️ *STOP & DELETE*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো ফাইল নেই!*"
            ),
            parse_mode='HTML'
        )
        return
    
    header = render_body_text(
        f"🗑️ *STOP & DELETE FILES*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *Select a file to stop or delete:*\n\n"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for f in all_files_data[:50]:
        status_icon = "⏹️" if f["is_stopped"] else ("🟢" if is_bot_running(f["user_id"], f["file_name"]) else "🔴")
        btn_text = (
            f"{status_icon} {f['file_name']} - "
            f"@{keep_user_name_emojis_normal(f['username'])}"
        )
        markup.add(types.InlineKeyboardButton(
            btn_text,
            callback_data=make_file_callback('stopdelete', f["user_id"], f["file_name"]),
            icon_custom_emoji_id=EMOJI_GREEN if not f["is_stopped"] and is_bot_running(f["user_id"], f["file_name"]) else EMOJI_RED
        ))
    
    markup.add(types.InlineKeyboardButton("𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾", callback_data='back_admin_panel'))
    
    bot.reply_to(message, header, reply_markup=markup, parse_mode='HTML')

# ==================== STOP & DELETE CONTROL ====================

def handle_stopdelete_control(call):
    """Handle stop/delete file control from STOP & DELETE menu"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'stopdelete')
    if not resolved:
        logger.error(f"Error parsing stopdelete callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    user_files_list = get_user_files_for_owner(target_user_id)
    file_info = next((f for f in user_files_list if f[0] == file_name), None)
    if not file_info:
        bot.answer_callback_query(call.id, "⚠️ File not found!", show_alert=True)
        return
    
    file_type = file_info[1]
    is_running = is_bot_running(target_user_id, file_name)
    is_stopped = target_user_id in file_stop_status and file_name in file_stop_status[target_user_id]
    
    user_name = "Unknown"
    for u in all_users:
        if u["id"] == target_user_id:
            user_name = u["name"]
            break
    if user_name == "Unknown":
        try:
            chat = bot.get_chat(target_user_id)
            user_name = chat.first_name or "Unknown"
        except:
            pass
    
    status_text = "⏹️ Stopped" if is_stopped else ("🟢 Running" if is_running else "🔴 Stopped")
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if is_stopped:
        markup.add(
            types.InlineKeyboardButton(
                "🟢 Start",
                callback_data=make_file_callback('admin_start', target_user_id, file_name),
                icon_custom_emoji_id=EMOJI_RED
            )
        )
    else:
        if is_running:
            markup.add(
                types.InlineKeyboardButton(
                    "🔴 Stop",
                    callback_data=make_file_callback('admin_stop', target_user_id, file_name),
                    icon_custom_emoji_id=EMOJI_GREEN
                ),
                types.InlineKeyboardButton("🔄 Restart", callback_data=make_file_callback('admin_restart', target_user_id, file_name))
            )
        else:
            markup.add(
                types.InlineKeyboardButton(
                    "🟢 Start",
                    callback_data=make_file_callback('admin_start', target_user_id, file_name),
                    icon_custom_emoji_id=EMOJI_RED
                )
            )
    
    markup.add(
        types.InlineKeyboardButton("🗑️ Delete", callback_data=make_file_callback('admin_delete', target_user_id, file_name)),
        types.InlineKeyboardButton(
            "📜 Logs",
            callback_data=make_file_callback('admin_logs', target_user_id, file_name),
            icon_custom_emoji_id=EMOJI_VIEW_LOGS
        )
    )
    
    markup.add(types.InlineKeyboardButton("🔙 Back", callback_data='back_stopdelete'))
    
    info_text = render_body_text(
        f"🗑️ *File Control*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📁 *File:* `{file_name}` ({file_type})\n"
        f"👤 *Owner:* {keep_user_name_emojis_normal(user_name)} (`{target_user_id}`)\n"
        f"{status_emoji_tag()} *Status:* {status_text}\n\n"
        f"⚙️ 𝑺𝒆𝒍𝒆𝒄𝒕 𝒂𝒏 𝒂𝒄𝒕𝒊𝒐𝒏:"
    )
    
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(
            info_text,
            call.message.chat.id, call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")

# ==================== ADMIN FILE ACTIONS ====================

def handle_admin_stop(call):
    """Admin stop a user's file"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'admin_stop')
    if not resolved:
        logger.error(f"Error parsing admin stop callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    if stop_user_file(target_user_id, file_name):
        bot.answer_callback_query(call.id, f"✅ '{file_name}' stopped!", show_alert=True)
        
        try:
            bot.send_message(
                target_user_id,
                render_body_text(
                    f"⏹️ *আপনার ফাইল অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📄 ফাইল: `{file_name}`\n"
                    f"👤 অ্যাডমিন: {user_id}\n\n"
                    f"⛔ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ নতুন ফাইল আপলোড করা যাবে না!*\n\n"
                    f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
                ),
                parse_mode='HTML'
            )
        except:
            pass
    else:
        bot.answer_callback_query(call.id, "❌ Stop failed!", show_alert=True)

def handle_admin_start(call):
    """Admin start a user's file"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'admin_start')
    if not resolved:
        logger.error(f"Error parsing admin start callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    user_files_list = get_user_files_for_owner(target_user_id)
    file_info = next((f for f in user_files_list if f[0] == file_name), None)
    if not file_info:
        bot.answer_callback_query(call.id, "⚠️ File not found!", show_alert=True)
        return
    
    file_type = file_info[1]
    user_folder = get_user_folder(target_user_id)
    file_path = os.path.join(user_folder, file_name)
    
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "⚠️ File missing!", show_alert=True)
        return
    
    start_user_file(target_user_id, file_name)
    
    if is_bot_running(target_user_id, file_name):
        bot.answer_callback_query(call.id, "⚠️ Already running!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, f"⏳ Starting '{file_name}'...")
    
    class FakeMessage:
        def __init__(self, chat_id):
            self.chat = type('obj', (object,), {'id': chat_id})()
    fake_msg = FakeMessage(call.message.chat.id)
    
    if file_type == 'py':
        threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, fake_msg)).start()
    elif file_type == 'js':
        threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, fake_msg)).start()
    
    try:
        bot.send_message(
            target_user_id,
            render_body_text(
                f"🟢 *আপনার ফাইল অ্যাডমিন দ্বারা স্টার্ট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📄 ফাইল: `{file_name}`\n"
                f"👤 অ্যাডমিন: {user_id}\n\n"
                f"✅ *এখন থেকে আবার নতুন ফাইল আপলোড করতে পারবেন!*"
            ),
            parse_mode='HTML'
        )
    except:
        pass

def handle_admin_restart(call):
    """Admin restart a user's file"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'admin_restart')
    if not resolved:
        logger.error(f"Error parsing admin restart callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    user_files_list = get_user_files_for_owner(target_user_id)
    file_info = next((f for f in user_files_list if f[0] == file_name), None)
    if not file_info:
        bot.answer_callback_query(call.id, "⚠️ File not found!", show_alert=True)
        return
    
    if target_user_id in file_stop_status and file_name in file_stop_status[target_user_id]:
        bot.answer_callback_query(call.id, "⚠️ File is stopped! Start it first.", show_alert=True)
        return
    
    script_key = f"{target_user_id}_{file_name}"
    if script_key in bot_scripts:
        kill_process_tree(bot_scripts[script_key])
        del bot_scripts[script_key]
        time.sleep(1)
    
    file_type = file_info[1]
    user_folder = get_user_folder(target_user_id)
    file_path = os.path.join(user_folder, file_name)
    
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, "⚠️ File missing!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, f"🔄 Restarting '{file_name}'...")
    
    class FakeMessage:
        def __init__(self, chat_id):
            self.chat = type('obj', (object,), {'id': chat_id})()
    fake_msg = FakeMessage(call.message.chat.id)
    
    if file_type == 'py':
        threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, fake_msg)).start()
    elif file_type == 'js':
        threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, fake_msg)).start()

def handle_admin_delete(call):
    """Admin delete a user's file"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'admin_delete')
    if not resolved:
        logger.error(f"Error parsing admin delete callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    script_key = f"{target_user_id}_{file_name}"
    if script_key in bot_scripts:
        kill_process_tree(bot_scripts[script_key])
        del bot_scripts[script_key]
    
    remove_user_file_db(target_user_id, file_name)
    
    user_folder = get_user_folder(target_user_id)
    file_path = os.path.join(user_folder, file_name)
    log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
    
    if os.path.exists(file_path):
        try: os.remove(file_path)
        except: pass
    if os.path.exists(log_path):
        try: os.remove(log_path)
        except: pass
    
    bot.answer_callback_query(call.id, f"🗑️ '{file_name}' deleted!", show_alert=True)
    
    try:
        bot.send_message(
            target_user_id,
            render_body_text(
                f"🗑️ *আপনার ফাইল অ্যাডমিন দ্বারা ডিলিট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📄 ফাইল: `{file_name}`\n"
                f"👤 অ্যাডমিন: {user_id}"
            ),
            parse_mode='HTML'
        )
    except:
        pass

def handle_admin_logs(call):
    """Admin view logs of a user's file"""
    user_id = call.from_user.id
    
    if not is_otp_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
        return
    
    resolved = resolve_file_callback(call.data, 'admin_logs')
    if not resolved:
        logger.error(f"Error parsing admin logs callback: {call.data}")
        bot.answer_callback_query(call.id, "❌ Invalid action!", show_alert=True)
        return
    target_user_id, file_name = resolved
    
    user_folder = get_user_folder(target_user_id)
    log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
    
    if not os.path.exists(log_path):
        bot.answer_callback_query(call.id, "📜 No logs found!", show_alert=True)
        return
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
        
        if len(log_content) > 4000:
            log_content = log_content[-4000:]
            log_content = "...\n" + log_content
        
        bot.send_message(
            call.message.chat.id,
            render_body_text(
                f"📜 *Logs for `{file_name}` (User: `{target_user_id}`)*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"```\n{log_content}\n```"
            ),
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id, "📜 Logs sent!")
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        bot.answer_callback_query(call.id, "❌ Error reading logs!", show_alert=True)

# ==================== ADMIN LIST - সম্পূর্ণ ফিক্সড ====================

def handle_otp_admin_list(message):
    """Handle admin list - shows all admins with details and sub-menu buttons"""
    user_id = message.from_user.id
    
    logger.info(f"📋 Admin list requested by user: {user_id}")
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not admin_list:
        bot.reply_to(message, 
            render_body_text(
                f"📌 *কোনো অ্যাডমিন নেই!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"💡 *এখনো কোনো অ্যাডমিন যোগ করা হয়নি।*"
            ),
            parse_mode='HTML'
        )
        return
    
    try:
        admin_text = render_body_text(f"👑 *অ্যাডমিন লিস্ট*\n")
        admin_text += f"━━━━━━━━━━━━━━━━━\n\n"
        
        for i, uid in enumerate(admin_list, 1):
            user_name = "❓ Unknown"
            username = "❌ @unknown"
            
            for user in all_users:
                if user["id"] == uid:
                    user_name = user["name"]
                    username = user["username"]
                    break
            
            if user_name == "❓ Unknown":
                try:
                    chat = bot.get_chat(uid)
                    user_name = chat.first_name or "Unknown"
                    username = f"@{chat.username}" if chat.username else "@unknown"
                except Exception as e:
                    logger.error(f"Could not get chat for {uid}: {e}")
            
            role = "👑 OWNER" if uid == OWNER_ID else "🔹 ADMIN"
            ban_status = "🔴 Banned" if uid in banned_users else "🟢 Active"
            
            admin_text += f"{i}. *{keep_user_name_emojis_normal(user_name)}*\n"
            admin_text += f"   🆔 `{uid}`\n"
            admin_text += f"   📌 {keep_user_name_emojis_normal(username)}\n"
            admin_text += f"   👑 {role}\n"
            admin_text += f"   📊 {ban_status}\n\n"
        
        total_admins = len(admin_list)
        owner_count = 1 if OWNER_ID in admin_list else 0
        admin_count = total_admins - owner_count
        
        admin_text += f"━━━━━━━━━━━━━━━━━\n"
        admin_text += f"📊 *মোট অ্যাডমিন:* {total_admins} জন\n"
        admin_text += f"👑 *ওনার:* {owner_count} জন\n"
        admin_text += f"🔹 *অ্যাডমিন:* {admin_count} জন\n\n"
        admin_text += f"👇 *নিচের বাটন ব্যবহার করুন:*"
        
        markup = create_admin_panel_keyboard()
        
        bot.reply_to(message, admin_text, reply_markup=markup, parse_mode='HTML')
        logger.info(f"✅ Admin list sent successfully to {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in admin list: {e}", exc_info=True)
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *Admin List এ সমস্যা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কারণ:* `{str(e)[:100]}`\n"
                f"💡 *দয়া করে আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )

def handle_otp_show_all_admins(message):
    """Show all admins in a nice list"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if not admin_list:
        bot.reply_to(message, render_body_text("📌 *কোনো অ্যাডমিন নেই!*"), parse_mode='HTML')
        return
    
    admin_show_list = ""
    for i, uid in enumerate(admin_list, 1):
        user_name = "Unknown"
        username = "@unknown"
        try:
            chat = bot.get_chat(uid)
            user_name = chat.first_name or "Unknown"
            username = f"@{chat.username}" if chat.username else "@unknown"
        except:
            pass
        
        for user in all_users:
            if user["id"] == uid:
                user_name = user["name"]
                username = user["username"]
                break
        
        # 🔥 ইমোজিগুলোকে প্রিমিয়াম ইমোজি স্ট্রিং হিসেবে ব্যবহার করুন
        role_emoji = "👑" if uid == OWNER_ID else "🔹"
        role_text = "OWNER" if uid == OWNER_ID else "ADMIN"
        ban_emoji = "🔴" if uid in banned_users else "🟢"
        ban_text = "Banned" if uid in banned_users else "Active"
        
        admin_show_list += f"{i}. *{keep_user_name_emojis_normal(user_name)}*\n"
        admin_show_list += f"   🆔 `{uid}`\n"
        admin_show_list += f"   📌 {keep_user_name_emojis_normal(username)}\n"
        admin_show_list += f"   {role_emoji} {role_text}\n"
        admin_show_list += f"   {ban_emoji} {ban_text}\n\n"
    
    total_admins = len(admin_list)
    owner_count = 1 if OWNER_ID in admin_list else 0
    admin_count = total_admins - owner_count
    
    # 🔥 সম্পূর্ণ মেসেজ render_body_text() এর ভিতরে দিন
    response = render_body_text(
        f"👑 *অ্যাডমিন লিস্ট*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"{admin_show_list}"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📊 *মোট অ্যাডমিন:* {total_admins} জন\n"
        f"👑 *ওনার:* {owner_count} জন\n"
        f"🔹 *অ্যাডমিন:* {admin_count} জন"
    )
    
    bot.reply_to(message, response, parse_mode='HTML')

def handle_otp_add_admin(message):
    """Handle add admin input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"➕ *Add Admin*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Send the User ID to add as admin:*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_add_admin)

def process_otp_add_admin(message):
    """Process add admin"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user in admin_list:
        bot.reply_to(message, f"⚠️ *User `{target_user}` is already an admin!*", parse_mode='HTML')
        return
    
    admin_list.append(target_user)
    add_admin_db(target_user)
    bot.reply_to(message, 
        render_body_text(
            f"✅ *Admin Added!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User ID: `{target_user}`\n"
            f"✅ *সফলভাবে অ্যাডমিন যোগ করা হয়েছে!*"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"🎉 *আপনাকে অ্যাডমিন করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *অ্যাডমিন:* {user_id}\n"
                f"✅ *এখন থেকে আপনি বট পরিচালনা করতে পারবেন!*"
            ),
            parse_mode='HTML'
        )
    except:
        pass

def handle_otp_remove_admin(message):
    """Handle remove admin input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"➖ *Remove Admin*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Send the User ID to remove from admin:*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_remove_admin)

def process_otp_remove_admin(message):
    """Process remove admin"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user == OWNER_ID:
        bot.reply_to(message, "❌ *Cannot remove Owner!*", parse_mode='HTML')
        return
    
    if target_user not in admin_list:
        bot.reply_to(message, f"⚠️ *User `{target_user}` is not an admin!*", parse_mode='HTML')
        return
    
    admin_list.remove(target_user)
    remove_admin_db(target_user)
    bot.reply_to(message, 
        render_body_text(
            f"✅ *Admin Removed!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 User ID: `{target_user}`\n"
            f"✅ *সফলভাবে অ্যাডমিন রিমুভ করা হয়েছে!*"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"⚠️ *আপনাকে অ্যাডমিন থেকে রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 *অ্যাডমিন:* {user_id}\n"
                f"❌ *এখন থেকে আপনি বট পরিচালনা করতে পারবেন না!*"
            ),
            parse_mode='HTML'
        )
    except:
        pass

def handle_otp_transfer_ownership(message):
    """Handle transfer ownership input"""
    user_id = message.from_user.id
    
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ *Only Owner Can Transfer Ownership!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"👑 *Transfer Ownership*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Send the User ID to transfer ownership:*\n\n"
            f"⚠️ *Warning: After transfer, you will lose Owner access!*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_transfer_ownership)

def process_otp_transfer_ownership(message):
    """Process transfer ownership"""
    global OWNER_ID
    
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ *Only Owner can transfer!*", parse_mode='HTML')
        return
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    if target_user == OWNER_ID:
        bot.reply_to(message, "⚠️ *You are already the Owner!*", parse_mode='HTML')
        return
    
    old_owner = OWNER_ID
    OWNER_ID = target_user
    
    if old_owner not in admin_list:
        admin_list.append(old_owner)
    
    bot.reply_to(message, 
        render_body_text(
            f"👑 *Ownership Transferred!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"✅ New Owner: `{target_user}`\n"
            f"👤 Previous Owner: `{old_owner}`\n"
            f"✅ *সফলভাবে ওনারশিপ ট্রান্সফার করা হয়েছে!*"
        ),
        parse_mode='HTML'
    )
    
    try:
        bot.send_message(
            target_user,
            render_body_text(
                f"👑 *আপনি এখন বটের নতুন ওনার!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"✅ *আপনি এখন বট সম্পূর্ণভাবে পরিচালনা করতে পারবেন!*"
            ),
            parse_mode='HTML'
        )
    except:
        pass

# ==================== OTP ADMIN LIST - বাটন হ্যান্ডলার ====================

@bot.message_handler(func=lambda message: message.text in [
    "𝙎𝙃𝙊𝙒 𝘼𝘿𝙈𝙄𝙉𝙎",
    "𝘼𝘿𝘿 𝘼𝘿𝙈𝙄𝙉",
    "𝙍𝙀𝙈𝙊𝙑𝙀 𝘼𝘿𝙈𝙄𝙉",
    "𝙏𝙍𝘼𝙉𝙎𝙁𝙀𝙍 𝙊𝙒𝙉𝙀𝙍𝙎𝙃𝙄𝙋",
    "𝙐𝙋𝘿𝘼𝙏𝙀 𝘽𝙊𝙏",
    UPDATE_CONFIRM_YES_TEXT,
    UPDATE_CONFIRM_NO_TEXT,
])
def handle_admin_buttons(message):
    """Handle all admin related buttons"""
    user_id = message.from_user.id
    text = message.text
    
    logger.info(f"🔘 Admin button clicked: '{text}' by {user_id}")
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "𝙎𝙃𝙊𝙒 𝘼𝘿𝙈𝙄𝙉𝙎":
        handle_otp_show_all_admins(message)
    elif text == "𝘼𝘿𝘿 𝘼𝘿𝙈𝙄𝙉":
        handle_otp_add_admin(message)
    elif text == "𝙍𝙀𝙈𝙊𝙑𝙀 𝘼𝘿𝙈𝙄𝙉":
        handle_otp_remove_admin(message)
    elif text == "𝙏𝙍𝘼𝙉𝙎𝙁𝙀𝙍 𝙊𝙒𝙉𝙀𝙍𝙎𝙃𝙄𝙋":
        handle_otp_transfer_ownership(message)
    elif text == "𝙐𝙋𝘿𝘼𝙏𝙀 𝘽𝙊𝙏":
        show_update_confirmation(message)
    elif text == UPDATE_CONFIRM_YES_TEXT:
        activate_bot_update(message)
    elif text == UPDATE_CONFIRM_NO_TEXT:
        cancel_bot_update(message)

def handle_otp_set_limit(message):
    """Handle set limit input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"⚙️ *SET LIMIT*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Send the User ID to set limit:*\n\n"
            f"Example: `123456789`"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_set_limit_user)

def process_otp_set_limit_user(message):
    """Process set limit user ID"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *Invalid User ID!*", parse_mode='HTML')
        return
    
    target_user = int(text)
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"⚙️ *SET LIMIT*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 *User ID:* `{target_user}`\n\n"
            f"📌 *Send the file limit for this user:*\n\n"
            f"Example: `10` (শুধু সংখ্যা)\n"
            f"💡 *0 = সীমাহীন*"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, lambda m: process_otp_set_limit_value(m, target_user))

def process_otp_set_limit_value(message, target_user):
    """Process set limit value"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text.isdigit():
        bot.reply_to(message, "❌ *শুধু সংখ্যা লিখুন!*", parse_mode='HTML')
        return
    
    limit_value = int(text)
    
    if limit_value == 0:
        if target_user in user_limits:
            del user_limits[target_user]
        limit_text = "সীমাহীন"
    else:
        user_limits[target_user] = limit_value
        limit_text = str(limit_value)
    
    bot.reply_to(message, 
        render_body_text(
            f"✅ *Limit Set Successfully!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👤 *User ID:* `{target_user}`\n"
            f"📊 *File Limit:* {limit_text}\n\n"
            f"✅ *সফলভাবে লিমিট সেট করা হয়েছে!*"
        ),
        parse_mode='HTML'
    )

def handle_otp_set_free_user_limit(message):
    """Handle set free user limit input"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    msg = bot.reply_to(message, 
        render_body_text(
            f"⚙️ *SET FREE USER LIMIT*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *সব ফ্রি ইউজারের জন্য সেটিংস সেট করুন*\n\n"
            f"📤 *ফরম্যাট:* `লিমিট ঘন্টা হোস্ট_সময়`\n"
            f"Example: `10 24 48`\n\n"
            f"📁 *লিমিট = ফাইল সংখ্যা* (কয়টা ফাইল আপলোড করতে পারবে)\n"
            f"⏰ *ঘন্টা = টাইম লিমিট* (কত ঘন্টার মধ্যে আপলোড করতে পারবে)\n"
            f"⏳ *হোস্ট_সময় = ফাইল কত ঘন্টা হোস্ট থাকবে*\n\n"
            f"📊 *বর্তমান সেটিংস:*\n"
            f"📁 লিমিট: {FREE_USER_LIMIT_SETTINGS['limit']} ফাইল\n"
            f"⏰ টাইম: {FREE_USER_LIMIT_SETTINGS['time']} ঘন্টা\n"
            f"⏳ হোস্ট সময়: {FREE_USER_LIMIT_SETTINGS['host_time']} ঘন্টা"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_otp_set_free_user_limit)

def process_otp_set_free_user_limit(message):
    """Process set free user limit"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    parts = text.split()
    if len(parts) != 3:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ভুল ফরম্যাট!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সঠিক ফরম্যাট:* `লিমিট ঘন্টা হোস্ট_সময়`\n"
                f"Example: `10 24 48`"
            ),
            parse_mode='HTML'
        )
        return
    
    if not parts[0].isdigit() or not parts[1].isdigit() or not parts[2].isdigit():
        bot.reply_to(message, 
            render_body_text(
                f"❌ *শুধু সংখ্যা দিন!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *সঠিক ফরম্যাট:* `লিমিট ঘন্টা হোস্ট_সময়`"
            ),
            parse_mode='HTML'
        )
        return
    
    limit_value = int(parts[0])
    time_value = int(parts[1])
    host_time = int(parts[2])
    
    if limit_value < 0 or time_value < 0 or host_time < 0:
        bot.reply_to(message, "❌ *মান ০ এর কম হতে পারে না!*", parse_mode='HTML')
        return
    
    if save_free_user_settings(limit_value, time_value, host_time):
        bot.reply_to(message, 
            render_body_text(
                f"✅ *FREE USER LIMIT SET SUCCESSFULLY!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📁 *ফাইল লিমিট:* {limit_value} ফাইল\n"
                f"⏰ *টাইম লিমিট:* {time_value} ঘন্টা\n"
                f"⏳ *হোস্ট সময়:* {host_time} ঘন্টা\n\n"
                f"✅ *সব ফ্রি ইউজারের জন্য আপডেট করা হয়েছে!*"
            ),
            parse_mode='HTML'
        )
    else:
        bot.reply_to(message, "❌ *সেটিংস সংরক্ষণ করতে ব্যর্থ হয়েছে!*", parse_mode='HTML')

def handle_otp_back_to_admin_panel(message):
    """Handle back to admin panel"""
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    handle_otp_admin_panel(message)

def go_back_to_main(message, menu_user_id=None):
    """Go back to the same main menu shown by /start."""
    source_user = getattr(message, "from_user", None)
    source_user_id = getattr(source_user, "id", None)
    user_id = menu_user_id if menu_user_id is not None else source_user_id
    chat_id = message.chat.id

    # Callback messages can be authored by the bot.  Use the real user's
    # profile when the caller supplies the owner ID (deployment does this).
    display_username = getattr(source_user, "username", None)
    if source_user_id != user_id:
        try:
            chat = bot.get_chat(user_id)
            display_username = getattr(chat, "username", None)
        except Exception as exc:
            logger.debug("Could not load user profile for main menu: %s", exc)
    
    markup = create_reply_keyboard_main_menu(user_id)
    
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    expiry_info = ""
    premium = get_active_premium_plan(user_id)
    if premium:
        user_status = premium_user_status_label()
        days_left = (premium["expiry"] - datetime.now()).days
        expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
    elif user_id == OWNER_ID: user_status = "👑 Owner"
    elif user_id in admin_ids: user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = premium_user_status_label(); days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
        else: user_status = free_user_status_label(expired=True)
    else: user_status = free_user_status_label()
    
    balance = get_user_balance_db(user_id)
    
    welcome_msg_text = render_body_text(
        f"〽️ Welcome back!\n\n🆔 Your User ID: `{user_id}`\n"
        f"✳️ Username: `@{keep_user_name_emojis_normal(display_username or 'Not set')}`\n"
        f"{status_emoji_tag()} Your Status: {user_status}{expiry_info}\n"
        f"{balance_emoji_tag()} Balance: ৳{balance:.2f}\n"
        f"📁 Files Uploaded: {current_files} / {limit_str}\n\n"
        f"🤖 Host & run Python (`.py`) or JS (`.js`) scripts.\n"
        f"   Upload single scripts or `.zip` archives.\n\n"
        f"👇 Use buttons or type commands."
    )
    
    bot.send_message(chat_id, welcome_msg_text, reply_markup=markup, parse_mode='HTML')

# ==================== LOGIC FUNCTIONS ====================

def _logic_run_all_scripts(message_or_call):
    """Show all scripts with status and user info"""
    if isinstance(message_or_call, telebot.types.Message):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.chat.id
        # ✅ parse_mode='HTML' যোগ করুন
        reply_func = lambda text, **kwargs: bot.reply_to(message_or_call, render_body_text(text), parse_mode='HTML', **kwargs)
    elif isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.message.chat.id
        bot.answer_callback_query(message_or_call.id)
        # ✅ parse_mode='HTML' যোগ করুন
        reply_func = lambda text, **kwargs: bot.send_message(admin_chat_id, render_body_text(text), parse_mode='HTML', **kwargs)
    else:
        logger.error("Invalid argument for _logic_run_all_scripts")
        return

    if admin_user_id not in admin_ids:
        reply_func("⚠️ Admin permissions required.")
        return

    reply_func(f"{checking_scripts_emoji_tag()} *Checking all scripts...*\n━━━━━━━━━━━━━━━━━")
    logger.info(f"Admin {admin_user_id} checked all scripts from chat {admin_chat_id}.")

    total_files = 0
    running_files = 0
    stopped_files = 0
    script_list = ""

    all_user_files_snapshot = dict(user_files)

    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        
        username = "Unknown"
        try:
            user_info = bot.get_chat(target_user_id)
            username = user_info.username or user_info.first_name or "Unknown"
        except:
            pass
        
        premium = get_user_premium_plan(target_user_id)
        is_premium = premium and premium["expiry"] > datetime.now()
        
        for file_name, file_type in files_for_user:
            total_files += 1
            is_running = is_bot_running(target_user_id, file_name)
            is_stopped = target_user_id in file_stop_status and file_name in file_stop_status[target_user_id]
            
            if is_stopped:
                status = "⏹️ Stopped"
                stopped_files += 1
            elif is_running:
                status = "🟢 Running"
                running_files += 1
            else:
                status = "🔴 Stopped"
                stopped_files += 1
            
            script_list += f"📄 `{file_name}` ({file_type})\n"
            script_list += (
                f"   👤 User: `{target_user_id}` "
                f"(@{keep_user_name_emojis_normal(username)})\n"
            )
            script_list += f"   {status_emoji_tag()} Status: {status}"
            if is_premium:
                script_list += f" 🌟"
            script_list += f"\n\n"

    if total_files == 0:
        script_list = "📌 No scripts found in the system."

    summary_msg = render_body_text(
        f"{all_scripts_status_emoji_tag()} *ALL SCRIPTS STATUS*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"📊 *Total Scripts:* {total_files}\n"
        f"🟢 *Running:* {running_files}\n"
        f"🔴 *Stopped:* {stopped_files}\n\n"
        f"📋 *Script Details:*\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"{script_list}"
    )

    # ✅ reply_func ইতিমধ্যে parse_mode='HTML' ব্যবহার করছে
    reply_func(summary_msg)
    logger.info(f"All scripts checked. Total: {total_files}, Running: {running_files}, Stopped: {stopped_files}")
def _logic_send_welcome(message):
    """Send welcome message with 100% premium emojis"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    logger.info(f"Welcome request from user_id: {user_id}, username: @{user_username}")

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, "⚠️ Bot locked by admin. Try later.")
        return
    
    was_new_user = user_id not in active_users
    add_otp_user(user_id, user_name, user_username)

    user_bio = "Could not fetch bio"; photo_file_id = None
    try: user_bio = bot.get_chat(user_id).bio or "No bio"
    except Exception: pass
    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos: photo_file_id = user_profile_photos.photos[0][-1].file_id
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            # Render the notification normally, but insert Bio only after
            # rendering so emojis written by the user remain ordinary
            # Unicode emojis instead of being converted to Premium tags.
            bio_placeholder = "__GX_PLAIN_BIO__"
            owner_notification = render_body_text(
                f"🎉 New user!\n"
                f"{profile_emoji_tag()} Name: {keep_user_name_emojis_normal(user_name)}\n"
                f"✳️ User: @{keep_user_name_emojis_normal(user_username or 'N/A')}\n"
                f"🆔 ID: `{user_id}`\nBio: {bio_placeholder}"
            ).replace(bio_placeholder, html_escape(str(user_bio or "No bio")))
            bot.send_message(OWNER_ID, owner_notification, parse_mode='HTML')
            if photo_file_id: bot.send_photo(OWNER_ID, photo_file_id, caption=f"Pic of new user {user_id}")
        except Exception as e: logger.error(f"⚠️ Failed to notify owner about new user {user_id}: {e}")

    # A valid referral is accepted only for a first-time user.  Suspicious
    # attempts are still inspected on later starts so the two-strike rule
    # cannot be bypassed by repeating a self-referral.
    register_referral_from_start(user_id, message, allow_new_user=was_new_user)
    if is_user_banned(user_id):
        send_banned_user_notice(chat_id, user_id)
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    expiry_info = ""
    
    premium = get_active_premium_plan(user_id)
    if premium:
        user_status = premium_user_status_label()
        days_left = (premium["expiry"] - datetime.now()).days
        expiry_info = f"\n⏳ Premium expires in: {days_left} days"
    elif user_id == OWNER_ID:
        user_status = "👑 Owner"
    elif user_id in admin_ids:
        user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = premium_user_status_label(); days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
        else: user_status = free_user_status_label(expired=True); remove_subscription_db(user_id)
    else: user_status = free_user_status_label()
    
    stop_warning = ""
    if user_id in file_stop_status and file_stop_status[user_id]:
        stop_warning = f"\n\n⚠️ *আপনার একটি ফাইল অ্যাডমিন দ্বারা স্টপ করা আছে!*\n📄 `{file_stop_status[user_id][0]}`\n💡 *অ্যাডমিনকে বলুন স্টার্ট করতে*"
    
    balance = get_user_balance_db(user_id)

    welcome_msg_text = render_body_text(
        f"🤖 Welcome, {keep_user_name_emojis_normal(user_name)}!\n\n"
        f"🆔 Your User ID: `{user_id}`\n"
        f"✳️ Username: `@{keep_user_name_emojis_normal(user_username or 'Not set')}`\n"
        f"{status_emoji_tag()} Your Status: {user_status}{expiry_info}\n"
        f"{balance_emoji_tag()} Balance: ৳{balance:.2f}\n"
        f"📁 Files Uploaded: {current_files} / {limit_str}\n"
        f"⏰ Host Time: {'Unlimited' if get_user_host_time(user_id) == float('inf') else str(get_user_host_time(user_id)) + ' hours'}{stop_warning}\n\n"
        f"🤖 Host & run Python (`.py`) or JS (`.js`) scripts.\n"
        f"   Upload single scripts or `.zip` archives.\n\n"
        f"👇 Use buttons or type commands."
    )
    
    markup = create_reply_keyboard_main_menu(user_id)
    picture_markup = create_picture_reply_keyboard(user_id)
    
    try:
        if photo_file_id: 
            bot.send_photo(
                chat_id,
                photo_file_id,
                reply_markup=picture_markup
            )
        bot.send_message(chat_id, welcome_msg_text, 
                        reply_markup=markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending welcome to {user_id}: {e}", exc_info=True)
        try: 
            bot.send_message(chat_id, welcome_msg_text, 
                            reply_markup=markup, parse_mode='HTML')
        except Exception as fallback_e: 
            logger.error(f"Fallback send_message failed for {user_id}: {fallback_e}")

def _logic_updates_channel(message):
    # ✅ ইনলাইন বাটন তৈরি - green style সহ
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇', 
            url=get_link('update_channel_link'),
            # Keep this action identical to the Reply Keyboard button.
            icon_custom_emoji_id=EMOJI_UPDATE_CHANNEL_USER,
            style="success"  # 🔥 green colour (success style)
        )
    )
    bot.reply_to(message, render_body_text("Visit our Updates Channel:"), reply_markup=markup, parse_mode='HTML')

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked by admin, cannot accept files.")
        return

    if user_id in file_stop_status and file_stop_status[user_id]:
        bot.reply_to(message, 
            render_body_text(
                f"⛔ *আপনার একটি ফাইল অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📄 স্টপ করা ফাইল: `{file_stop_status[user_id][0]}`\n"
                f"⏳ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ নতুন ফাইল আপলোড করা যাবে না!*\n\n"
                f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
            ),
            parse_mode='HTML'
        )
        return

    # This lifetime quota is deliberately separate from the existing
    # simultaneous-hosted-file limit below.
    if not is_file_action_quota_exempt(user_id) and is_file_action_limit_reached(user_id):
        bot.reply_to(message, file_action_limit_message(), parse_mode='HTML')
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, 
            render_body_text(
                f"⚠️ *ফাইল লিমিট শেষ!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📁 *আপনি {current_files}/{limit_str} ফাইল আপলোড করেছেন*\n\n"
                f"💡 *প্রিমিয়াম কিনতে ডিপোজিট করে প্রিমিয়াম প্লান কিনুন।*"
            ),
            parse_mode='HTML'
        )
        return
    
    pending_upload_modes[user_id] = {
        "mode": None,
        "stage": "select_mode",
        "created_at": datetime.now().isoformat(),
    }
    bot.reply_to(
        message,
        render_body_text(
            "📤 *SELECT MODULE INSTALL MODE*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "ফাইল upload করার আগে নিচের একটি mode select করুন।\n"
            "তারপর bot file পাঠাবেন।"
        ),
        reply_markup=create_upload_mode_keyboard(),
        parse_mode='HTML'
    )


@bot.message_handler(func=lambda message: message.text in [
    "𝘼𝙐𝙏𝙊 𝙈𝙊𝘿𝙐𝙇𝙀 𝙄𝙉𝙎𝙏𝘼𝙇𝙇",
    "𝙈𝘼𝙉𝙐𝘼𝙇 𝙈𝙊𝘿𝙐𝙇𝙀 𝙄𝙉𝙎𝙏𝘼𝙇𝙇",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉",
    "BACK TO MAIN",
])
def handle_upload_mode_selection(message):
    """Choose an upload mode or return to the main menu."""
    user_id = message.from_user.id

    if message.text in ("𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", "BACK TO MAIN"):
        pending_upload_modes.pop(user_id, None)
        go_back_to_main(message)
        return

    state = pending_upload_modes.get(user_id)

    if not state or state.get("stage") != "select_mode":
        bot.reply_to(
            message,
            render_body_text(
                "⚠️ আগে *UPLOAD FILE* button-এ click করুন, "
                "তারপর module mode select করুন।"
            ),
            parse_mode='HTML'
        )
        return

    if message.text == "𝘼𝙐𝙏𝙊 𝙈𝙊𝘿𝙐𝙇𝙀 𝙄𝙉𝙎𝙏𝘼𝙇𝙇":
        state.update({"mode": "auto", "stage": "waiting_file"})
        next_text = (
            "✅ *AUTO MODULE INSTALL selected*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "এখন আপনার `.py`, `.js`, অথবা `.zip` bot file পাঠান।\n"
            "সব missing module একসাথে install করে bot run করা হবে।"
        )
    else:
        state.update({"mode": "manual", "stage": "waiting_file"})
        next_text = (
            "✅ *MANUAL MODULE INSTALL selected*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "প্রথমে আপনার `.py`, `.js`, অথবা `.zip` bot file পাঠান।\n"
            "File নেওয়ার পর bot `requirements.txt` চাইবে।\n"
            "শুধু ওই file-এর module-গুলোই install হবে।"
        )

    bot.reply_to(
        message,
        render_body_text(next_text),
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode='HTML'
    )

def _logic_check_files(message):
    user_id = message.from_user.id
    user_files_list = get_user_files_for_owner(user_id)
    if not user_files_list:
        # ✅ প্রিমিয়াম ইমোজি সহ
        bot.reply_to(message, render_body_text("📂 Your files:\n\n(No files uploaded yet)"), parse_mode='HTML')
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        is_stopped = user_id in file_stop_status and file_name in file_stop_status[user_id]
        
        if is_stopped:
            status_icon = "⏹️ Stopped"
        elif is_running:
            status_icon = "🟢 Running"
        else:
            status_icon = "🔴 Stopped"
            
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(
            btn_text,
            callback_data=make_file_callback('file', user_id, file_name),
            icon_custom_emoji_id=EMOJI_GREEN if is_running and not is_stopped else EMOJI_RED
        ))
    
    # ✅ এখানেও render_body_text() যোগ করুন
    bot.reply_to(message, render_body_text("📂 Your files:\nClick to manage."), reply_markup=markup, parse_mode='HTML')

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()
    wait_msg = bot.reply_to(
        message,
        render_body_text(f"{bot_speed_emoji_tag()} Testing speed..."),
        parse_mode='HTML'
    )
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        status = "🔓 Unlocked" if not bot_locked else "🔒 Locked"
        if user_id == OWNER_ID: user_level = "👑 Owner"
        elif user_id in admin_ids: user_level = "🛡️ Admin"
        elif get_active_premium_plan(user_id) or (
            user_id in user_subscriptions
            and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now()
        ): user_level = premium_user_status_label()
        else: user_level = free_user_status_label()
        speed_msg = render_body_text(
            f"𝘽𝙊𝙏 𝙎𝙋𝙀𝙀𝘿 & {status_emoji_tag()} Status:\n\n⏱️ API Response Time: {response_time} ms\n"
            f"🤖 Bot {status_emoji_tag()} Status: {status}\n"
            f"👤 Your Level: {user_level}"
        )
        bot.edit_message_text(speed_msg, chat_id, wait_msg.message_id, parse_mode='HTML')  # ✅ parse_mode যোগ
    except Exception as e:
        logger.error(f"Error during speed test (cmd): {e}", exc_info=True)
        bot.edit_message_text(render_body_text("❌ Error during speed test."), chat_id, wait_msg.message_id, parse_mode='HTML')  # ✅ parse_mode যোগ

def _logic_support(message):
    """Open the support contact link configured in All Link Setup.

    Reply-keyboard buttons can only send text.  The follow-up inline URL
    button is therefore the native Telegram way to open the support chat.
    `get_link()` is evaluated on every click, so changes take effect
    immediately without restarting the bot.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            '𝙈𝙀𝙎𝙎𝘼𝙂𝙀 𝙎𝙐𝙋𝙋𝙊𝙍𝙏',
            url=get_link('support_link'),
            icon_custom_emoji_id=EMOJI_SUPPORT,
            style='primary'
        )
    )
    bot.reply_to(
        message,
        render_body_text(
            " *Support Center*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 সাপোর্ট পেতে নিচের বাটনে ক্লিক করুন।"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def _logic_subscriptions_panel(message):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Admin permissions required."), parse_mode='HTML')
        return
    
    # 🔥 Gift Box ইমোজি ব্যবহার করুন (bKash এর জায়গায়)
    bot.reply_to(
        message, 
        render_body_text(
            f"<tg-emoji emoji-id=\"{EMOJI_GIFT_BOX}\">🎁</tg-emoji> 𝑺𝒖𝒃𝒔𝒄𝒓𝒊𝒑𝒕𝒊𝒐𝒏 𝑴𝒂𝒏𝒂𝒈𝒆𝒎𝒆𝒏𝒕\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 𝑺𝒆𝒍𝒆𝒄𝒕 𝒂𝒏 𝒂𝒄𝒕𝒊𝒐𝒏:"
        ), 
        reply_markup=create_subscription_menu(), 
        parse_mode='HTML'
    )

def _logic_statistics(message):
    user_id = message.from_user.id
    total_users = len(active_users)
    total_files_records = sum(len(files) for files in user_files.values())

    running_bots_count = 0
    user_running_bots = 0

    for script_key_iter, script_info_iter in list(bot_scripts.items()):
        s_owner_id, _ = script_key_iter.split('_', 1)
        if is_bot_running(int(s_owner_id), script_info_iter['file_name']):
            running_bots_count += 1
            if int(s_owner_id) == user_id:
                user_running_bots +=1

    stats_msg_base = render_body_text(
        f"📊 Bot Statistics:\n\n"
        f"👥 Total Users: {total_users}\n"
        f"📂 Total File Records: {total_files_records}\n"
        f"🟢 Total Active Bots: {running_bots_count}\n"
    )

    if user_id in admin_ids:
        stats_msg_admin = render_body_text(
            f"🔒 Bot {status_emoji_tag()} Status: {'🔴 Locked' if bot_locked else '🟢 Unlocked'}\n"
            f"🤖 Your Running Bots: {user_running_bots}"
        )
        stats_msg = stats_msg_base + stats_msg_admin
    else:
        stats_msg = stats_msg_base + f"🤖 Your Running Bots: {user_running_bots}"

    bot.reply_to(message, stats_msg, parse_mode='HTML')  # ✅ parse_mode যোগ করুন

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, "⚠️ Admin permissions required.")
        return
    global bot_locked
    bot_locked = not bot_locked
    status = "locked" if bot_locked else "unlocked"
    logger.warning(f"Bot {status} by Admin {message.from_user.id} via command/button.")
    # ✅ parse_mode='HTML' যোগ করুন
    bot.reply_to(message, render_body_text(f"🔒 Bot has been {status}."), parse_mode='HTML')

# ==================== COMMAND HANDLERS ====================

@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message): _logic_send_welcome(message)

@bot.message_handler(commands=['status'])
def command_show_status(message): _logic_statistics(message)

BUTTON_TEXT_TO_LOGIC = {
    "𝙐𝙋𝘿𝘼𝙏𝙀𝙎 𝘾𝙃𝘼𝙉𝙉𝙀𝙇": _logic_updates_channel,
    "𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀": _logic_upload_file,
    "𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀𝙎": _logic_check_files,
    "𝘽𝙊𝙏 𝙎𝙋𝙀𝙀𝘿": _logic_bot_speed,
    "𝙎𝙐𝙋𝙋𝙊𝙍𝙏": _logic_support,
    "𝙎𝙏𝘼𝙏𝙄𝙎𝙏𝙄𝘾𝙎": _logic_statistics,
    "𝙎𝙐𝘽𝙎𝘾𝙍𝙄𝙋𝙏𝙄𝙊𝙉𝙎": _logic_subscriptions_panel,
    "𝙇𝙊𝘾𝙆 𝘽𝙊𝙏": _logic_toggle_lock_bot,
    "𝙍𝙐𝙉𝙉𝙄𝙉𝙂 𝘼𝙇𝙇 𝘾𝙊𝘿𝙀": _logic_run_all_scripts,
    "𝙍𝙀𝙁𝙁𝙀𝙍 & 𝘽𝙊𝙉𝙐𝙎": _logic_referral,
    "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏": _logic_free_host,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)
    else: logger.warning(f"Button text '{message.text}' matched but no logic func.")

# --- User Bengali Button Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝙐𝙋𝘿𝘼𝙏𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇",
    "𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀",
    "𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀"
])
def handle_user_bengali_buttons(message):
    text = message.text
    
    if text == "𝙐𝙋𝘿𝘼𝙏𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇":
        _logic_updates_channel(message)
    elif text == "𝙐𝙋𝙇𝙊𝘼𝘿 𝙁𝙄𝙇𝙀":
        _logic_upload_file(message)
    elif text == "𝘾𝙃𝙀𝘾𝙆 𝙁𝙄𝙇𝙀":
        _logic_check_files(message)

# --- OTP GURU Button Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
    "𝙈𝙔 𝙋𝙍𝙊𝙁𝙄𝙇𝙀",
    "𝘿𝙀𝙋𝙊𝙎𝙄𝙏",
    "𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙋𝙇𝘼𝙉𝙎",
    "𝙐𝙋𝘿𝘼𝙏𝙀 𝘽𝙊𝙏",
    UPDATE_CONFIRM_YES_TEXT,
    UPDATE_CONFIRM_NO_TEXT,
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉"
])
def handle_otp_buttons(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇":
        if not (is_otp_admin(user_id)):
            bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
            return
        handle_otp_admin_panel(message)
    elif text == "𝙈𝙔 𝙋𝙍𝙊𝙁𝙄𝙇𝙀":
        handle_otp_profile(message)
    elif text == "𝘿𝙀𝙋𝙊𝙎𝙄𝙏":
        handle_deposit_user(message)
    elif text == "𝙋𝙍𝙄𝙈𝙄𝙐𝙈 𝙋𝙇𝘼𝙉𝙎":
        handle_premium_plan_user(message)
    elif text == "𝙐𝙋𝘿𝘼𝙏𝙀 𝘽𝙊𝙏":
        if user_id not in admin_ids and not is_otp_admin(user_id):
            bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
            return
        show_update_confirmation(message)
    elif text == UPDATE_CONFIRM_YES_TEXT:
        if user_id not in admin_ids and not is_otp_admin(user_id):
            bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
            return
        activate_bot_update(message)
    elif text == UPDATE_CONFIRM_NO_TEXT:
        if user_id not in admin_ids and not is_otp_admin(user_id):
            bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
            return
        cancel_bot_update(message)
    elif text == "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉":
        go_back_to_main(message)

# --- Premium Plan User Sub-menu Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "Buy Plan", "Deposit"
])
def handle_premium_user_submenu(message):
    text = message.text
    
    if text == "Buy Plan":
        handle_buy_plan(message)
    elif text == "Deposit":
        handle_deposit_user(message)

# --- Destructive data and Google Sheets admin actions ---
def _delete_all_data_confirmation_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        make_keyboard_button(
            DELETE_ALL_DATA_CONFIRM_TEXT, EMOJI_APPROVE, "danger",
            use_override=False
        ),
        make_keyboard_button(
            DELETE_ALL_DATA_CANCEL_TEXT, EMOJI_REJECT, "primary",
            use_override=False
        ),
    )
    return markup


def handle_delete_all_data_request(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode="HTML")
        return
    bot.reply_to(
        message,
        render_body_text(
            "⚠️ *DELETE ALL DATA?*\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "এই action করলে user, subscription, balance, payment, "
            "referral, settings, file record এবং uploaded files মুছে যাবে।\n"
            "Google Sheets-ও নতুন empty/default state-এ sync হবে।\n\n"
            "🔒 Owner/admin access lockout এড়াতে environment-এর Owner/Admin "
            "access রাখা হবে।\n\n"
            "নিশ্চিত হলে নিচের লাল button চাপুন।"
        ),
        reply_markup=_delete_all_data_confirmation_keyboard(),
        parse_mode="HTML",
    )


def handle_google_sheets_status(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode="HTML")
        return
    if google_sheet_data_loaded and _google_sheets_configured():
        sync_to_google_sheets(force=True)
    bot.reply_to(
        message,
        render_body_text(google_sheets_status_text()),
        reply_markup=create_otp_reply_keyboard(message.from_user.id),
        parse_mode="HTML",
    )


@bot.message_handler(func=lambda message: message.text in (
    DELETE_ALL_DATA_CONFIRM_TEXT,
    DELETE_ALL_DATA_CANCEL_TEXT,
))
def handle_delete_all_data_confirmation(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode="HTML")
        return
    if message.text == DELETE_ALL_DATA_CANCEL_TEXT:
        bot.reply_to(
            message,
            "✅ Data safe আছে। Delete action বাতিল করা হয়েছে।",
            reply_markup=create_otp_reply_keyboard(message.from_user.id),
            parse_mode="HTML",
        )
        return

    try:
        result = delete_all_bot_data()
        sync_label = "✅ Google Sheets updated" if result["sync_ok"] else (
            f"⚠️ Google Sheets update failed: {google_sheet_last_error}"
        )
        bot.reply_to(
            message,
            render_body_text(
                "✅ *ALL DATA DELETE COMPLETED*\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ *Database tables cleared:* {result['tables']}\n"
                f"📁 *Drive backups removed:* {result['files']}\n"
                f"🛑 *Running bots stopped:* {result['processes']}\n"
                f"{sync_label}\n\n"
                "🔒 Owner/Admin access রাখা হয়েছে।"
            ),
            reply_markup=create_otp_reply_keyboard(message.from_user.id),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.error("Full data delete failed: %s", exc, exc_info=True)
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *FULL DELETE FAILED*\n━━━━━━━━━━━━━━━━━\n\n"
                f"<code>{html_escape(str(exc)[:1200])}</code>"
            ),
            reply_markup=create_otp_reply_keyboard(message.from_user.id),
            parse_mode="HTML",
        )


# --- OTP Admin Button Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉", "𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎",
    "𝘼𝙇𝙇 𝙁𝙄𝙇𝙀𝙎", "𝙎𝙏𝙊𝙋 & 𝘿𝙀𝙇𝙀𝙏𝙀",
    DELETE_ALL_DATA_BUTTON_TEXT, GOOGLE_SYNC_STATUS_BUTTON_TEXT,
    "𝙎𝙀𝙏 𝙇𝙄𝙈𝙄𝙏", "𝙁𝙍𝙀𝙀 𝙐𝙎𝙀𝙍 𝙇𝙄𝙈𝙄𝙏",
    "𝙎𝙚𝙩 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙋𝙡𝙖𝙣",
    "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙎𝙔𝙎𝙏𝙀𝙈",
    "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙂𝙍𝙐𝙋𝙀",
    "𝙁𝙄𝙇𝙀 𝙁𝙊𝙍𝙒𝘼𝙍𝘿 𝙂𝙍𝙊𝙐𝙋",
    "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏",
    "𝙁𝙊𝙍𝘾𝙀 𝙅𝙊𝙄𝙉",
    "𝘼𝙇𝙇 𝙇𝙄𝙉𝙆 𝙎𝙀𝙏𝙐𝙋",
    "𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾"
])
@bot.message_handler(func=lambda message: message.text in [
    "𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉", "𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎",
    "𝘼𝙇𝙇 𝙁𝙄𝙇𝙀𝙎", "𝙎𝙏𝙊𝙋 & 𝘿𝙀𝙇𝙀𝙏𝙀",
    DELETE_ALL_DATA_BUTTON_TEXT, GOOGLE_SYNC_STATUS_BUTTON_TEXT,
    "𝙎𝙀𝙏 𝙇𝙄𝙈𝙄𝙏", "𝙁𝙍𝙀𝙀 𝙐𝙎𝙀𝙍 𝙇𝙄𝙈𝙄𝙏",
    "𝙎𝙚𝙩 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙋𝙡𝙖𝙣",  # 🔥 এই লাইন যোগ করুন
    "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙎𝙔𝙎𝙏𝙀𝙈",
    "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙂𝙍𝙐𝙋𝙀",
    "𝙁𝙄𝙇𝙀 𝙁𝙊𝙍𝙒𝘼𝙍𝘿 𝙂𝙍𝙊𝙐𝙋",
    "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏",
    "𝙁𝙊𝙍𝘾𝙀 𝙅𝙊𝙄𝙉",
    "𝘼𝙇𝙇 𝙇𝙄𝙉𝙆 𝙎𝙀𝙏𝙐𝙋",
    "𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾"
])
def handle_otp_admin_buttons(message):
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "𝘽𝘼𝙉 / 𝙐𝙉𝘽𝘼𝙉":
        handle_otp_ban_unban(message)
    elif text == "𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎":
        handle_otp_all_users(message)
    elif text == "𝘼𝙇𝙇 𝙁𝙄𝙇𝙀𝙎":
        handle_otp_all_files(message)
    elif text == "𝙎𝙏𝙊𝙋 & 𝘿𝙀𝙇𝙀𝙏𝙀":
        handle_otp_stop_delete(message)
    elif text == DELETE_ALL_DATA_BUTTON_TEXT:
        handle_delete_all_data_request(message)
    elif text == GOOGLE_SYNC_STATUS_BUTTON_TEXT:
        handle_google_sheets_status(message)
    elif text == "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙎𝙔𝙎𝙏𝙀𝙈":
        handle_admin_deposit_panel(message)
    elif text == "𝙎𝙀𝙏 𝙇𝙄𝙈𝙄𝙏":
        handle_otp_set_limit(message)
    elif text == "𝙁𝙍𝙀𝙀 𝙐𝙎𝙀𝙍 𝙇𝙄𝙈𝙄𝙏":
        handle_otp_set_free_user_limit(message)
    elif text == "𝙎𝙚𝙩 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙋𝙡𝙖𝙣":  # 🔥 এই লাইন যোগ করুন
        handle_premium_plan_admin(message)      # 🔥 এই লাইন যোগ করুন
    elif text == "𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙂𝙍𝙐𝙋𝙀":
        handle_set_group(message)
    elif text == "𝙁𝙄𝙇𝙀 𝙁𝙊𝙍𝙒𝘼𝙍𝘿 𝙂𝙍𝙊𝙐𝙋":
        handle_set_file_forward_group(message)
    elif text == "𝙁𝙍𝙀𝙀 𝘽𝙊𝙏 𝙃𝙊𝙎𝙏":
        _logic_referral_admin_panel(message)
    elif text == "𝙁𝙊𝙍𝘾𝙀 𝙅𝙊𝙄𝙉":
        handle_force_join_panel(message)
    elif text == "𝘼𝙇𝙇 𝙇𝙄𝙉𝙆 𝙎𝙀𝙏𝙐𝙋":
        handle_link_setup_panel(message)
    elif text == "𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏":
        handle_broadcast_panel(message)
    elif text == "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇≾":
        handle_otp_back_to_admin_panel(message)

# --- Referral and free-host admin sub-menu handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝙎𝙀𝙏 𝙍𝙀𝙁𝙁𝙀𝙍 𝘽𝙊𝙉𝙐𝙎",
    "𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇"
])
def handle_referral_admin_buttons(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, render_body_text("⛔ Unauthorized!"), parse_mode='HTML')
        return
    if message.text == "𝙎𝙀𝙏 𝙍𝙀𝙁𝙁𝙀𝙍 𝘽𝙊𝙉𝙐𝙎":
        handle_set_referral_bonus(message)
    elif message.text == "𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉":
        handle_free_host_plan_admin(message)
    else:
        handle_otp_admin_panel(message)

@bot.message_handler(func=lambda message: message.text in [
    "𝘼𝘿𝘿 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
    "𝙍𝙀𝙈𝙊𝙑𝙀 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝙍𝙀𝙁𝙁𝙀𝙍 𝙎𝙀𝙏𝙏𝙄𝙉𝙂𝙎"
])
def handle_free_host_admin_buttons(message):
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, render_body_text("⛔ Unauthorized!"), parse_mode='HTML')
        return
    if message.text == "𝘼𝘿𝘿 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉":
        handle_add_free_host_plan(message)
    elif message.text == "𝙍𝙀𝙈𝙊𝙑𝙀 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏 𝙋𝙇𝘼𝙉":
        handle_remove_free_host_plan(message)
    else:
        _logic_referral_admin_panel(message)

# --- OTP Deposite Sub-menu Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙍𝙀𝙌𝙐𝙀𝙎𝙏", 
    "𝙎𝙀𝙏 𝘿𝙀𝙋𝙊𝙎𝙄𝙏 𝙉𝙐𝙈𝘽𝙀𝙍 𝘼𝙉𝘿 𝙄𝘿",
    "𝘿𝙀𝙇𝙀𝙏𝙀 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙈𝙀𝙏𝙃𝙊𝘿"
])
def handle_otp_deposite_submenu(message):
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘿𝙀𝙋𝙊𝙎𝙄𝙏𝙀 𝙍𝙀𝙌𝙐𝙀𝙎𝙏":
        handle_admin_show_deposits(message)
    elif text == "𝙎𝙀𝙏 𝘿𝙀𝙋𝙊𝙎𝙄𝙏 𝙉𝙐𝙈𝘽𝙀𝙍 𝘼𝙉𝘿 𝙄𝘿":
        handle_admin_set_deposit(message)
    elif text == "𝘿𝙀𝙇𝙀𝙏𝙀 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙈𝙀𝙏𝙃𝙊𝘿":
        handle_admin_delete_payment_method(message)

# --- Premium Plan Admin Sub-menu Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝘼𝙙𝙙 𝙋𝙡𝙖𝙣", 
    "𝙍𝙚𝙢𝙤𝙫𝙚 𝙋𝙡𝙖𝙣",
    "𝙍𝙚𝙨𝙚𝙩 𝘼𝙡𝙡 𝙋𝙡𝙖𝙣𝙨"
])
@bot.message_handler(func=lambda message: message.text in [
    "Add Plan",
    "Remove Plan",
    "Reset All Plans",
    "Show All Plans",
    "BACK TO ADMIN PANEL"
])
def handle_premium_admin_submenu(message):
    text = message.text
    
    if text == "Add Plan":
        handle_add_premium_plan(message)
    elif text == "Remove Plan":
        handle_remove_premium_plan(message)
    elif text == "Reset All Plans":
        handle_reset_all_plans(message)
    elif text == "Show All Plans":
        show_all_plans(message)
    elif text == "BACK TO ADMIN PANEL":
        handle_otp_admin_panel(message)

# --- OTP Ban Sub-menu Handlers ---
@bot.message_handler(func=lambda message: message.text in [
    "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "𝘽𝘼𝙉 𝙐𝙎𝙀𝙍", "𝙐𝙉𝘽𝘼𝙉 𝙐𝙎𝙀𝙍"
])
def handle_otp_ban_submenu(message):
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "𝙎𝙃𝙊𝙒 𝘼𝙇𝙇 𝘽𝘼𝙉 𝙐𝙎𝙀𝙍":
        handle_otp_show_banned(message)
    elif text == "𝘽𝘼𝙉 𝙐𝙎𝙀𝙍":
        handle_otp_ban_user(message)
    elif text == "𝙐𝙉𝘽𝘼𝙉 𝙐𝙎𝙀𝙍":
        handle_otp_unban_user(message)

# --- Command Handlers ---
@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message): _logic_updates_channel(message)
@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message): _logic_upload_file(message)
@bot.message_handler(commands=['checkfiles'])
def command_check_files(message): _logic_check_files(message)
@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message): _logic_bot_speed(message)
@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message):
    # Backward-compatible command alias; no legacy Contact Owner button is
    # exposed anywhere in the user/admin reply keyboards.
    _logic_support(message)

@bot.message_handler(commands=['support'])
def command_support(message): _logic_support(message)
@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message): _logic_subscriptions_panel(message)
@bot.message_handler(commands=['statistics'])
def command_statistics(message): _logic_statistics(message)
@bot.message_handler(commands=['lockbot']) 
def command_lock_bot(message): _logic_toggle_lock_bot(message)
@bot.message_handler(commands=['runningallcode'])
def command_run_all_code(message): _logic_run_all_scripts(message)

@bot.message_handler(commands=['ping'])
def ping(message):
    start_ping_time = time.time() 
    msg = bot.reply_to(message, "Pong!")
    latency = round((time.time() - start_ping_time) * 1000, 2)
    bot.edit_message_text(f"Pong! Latency: {latency} ms", message.chat.id, msg.message_id)

# ==================== ADMIN COMMANDS ====================

@bot.message_handler(commands=['addadmin'])
def command_add_admin(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ *শুধুমাত্র ওনার অ্যাডমিন যোগ করতে পারেন!*", parse_mode='HTML')
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ *সঠিক ফরম্যাট:* `/addadmin USER_ID`", parse_mode='HTML')
            return
        target_user = int(parts[1])
        
        if target_user in admin_list:
            bot.reply_to(message, f"⚠️ *ইউজার `{target_user}` ইতিমধ্যে অ্যাডমিন!*", parse_mode='HTML')
            return
        
        admin_list.append(target_user)
        add_admin_db(target_user)
        bot.reply_to(message, 
            render_body_text(
                f"✅ *অ্যাডমিন যোগ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 ইউজার আইডি: `{target_user}`\n"
                f"✅ সফলভাবে অ্যাডমিন করা হয়েছে!"
            ),
            parse_mode='HTML'
        )
        
        try:
            bot.send_message(
                target_user,
                render_body_text(
                    f"🎉 *আপনাকে অ্যাডমিন করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 অ্যাডমিন: {user_id}\n"
                    f"✅ এখন থেকে আপনি বট পরিচালনা করতে পারবেন!"
                ),
                parse_mode='HTML'
            )
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ *ইনভ্যালিড ইউজার আইডি!* শুধু সংখ্যা দিন।", parse_mode='HTML')

@bot.message_handler(commands=['removeadmin'])
def command_remove_admin(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ *শুধুমাত্র ওনার অ্যাডমিন রিমুভ করতে পারেন!*", parse_mode='HTML')
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ *সঠিক ফরম্যাট:* `/removeadmin USER_ID`", parse_mode='HTML')
            return
        target_user = int(parts[1])
        
        if target_user == OWNER_ID:
            bot.reply_to(message, "❌ *ওনারকে রিমুভ করা যাবে না!*", parse_mode='HTML')
            return
        
        if target_user not in admin_list:
            bot.reply_to(message, f"⚠️ *ইউজার `{target_user}` অ্যাডমিন নয়!*", parse_mode='HTML')
            return
        
        admin_list.remove(target_user)
        remove_admin_db(target_user)
        bot.reply_to(message, 
            render_body_text(
                f"✅ *অ্যাডমিন রিমুভ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 ইউজার আইডি: `{target_user}`\n"
                f"✅ সফলভাবে অ্যাডমিন রিমুভ করা হয়েছে!"
            ),
            parse_mode='HTML'
        )
        
        try:
            bot.send_message(
                target_user,
                render_body_text(
                    f"⚠️ *আপনাকে অ্যাডমিন থেকে রিমুভ করা হয়েছে!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 অ্যাডমিন: {user_id}\n"
                    f"❌ এখন থেকে আপনি বট পরিচালনা করতে পারবেন না!"
                ),
                parse_mode='HTML'
            )
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ *ইনভ্যালিড ইউজার আইডি!* শুধু সংখ্যা দিন।", parse_mode='HTML')

@bot.message_handler(commands=['admins', 'listadmins'])
def command_list_admins(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in admin_list:
        bot.reply_to(message, "⛔ *শুধুমাত্র অ্যাডমিনরা দেখতে পারেন!*", parse_mode='HTML')
        return
    
    if not admin_list:
        bot.reply_to(message, render_body_text("📌 *কোনো অ্যাডমিন নেই!*"), parse_mode='HTML')
        return
    
    admin_text = render_body_text(f"👑 *অ্যাডমিন লিস্ট*\n")
    admin_text += f"━━━━━━━━━━━━━━━━━\n\n"
    
    for i, uid in enumerate(admin_list, 1):
        try:
            chat = bot.get_chat(uid)
            name = chat.first_name or "Unknown"
            username = f"@{chat.username}" if chat.username else "@unknown"
        except:
            name = "Unknown"
            username = "@unknown"
        
        role = "👑 ওনার" if uid == OWNER_ID else "🔹 অ্যাডমিন"
        admin_text += f"{i}. *{keep_user_name_emojis_normal(name)}*\n"
        admin_text += f"   🆔 `{uid}`\n"
        admin_text += f"   📌 {keep_user_name_emojis_normal(username)}\n"
        admin_text += f"   👑 {role}\n\n"
    
    owner_count = 1 if OWNER_ID in admin_list else 0
    admin_count = len(admin_list) - owner_count
    
    admin_text += f"━━━━━━━━━━━━━━━━━\n"
    admin_text += f"📊 *মোট অ্যাডমিন:* {len(admin_list)} জন\n"
    admin_text += f"👑 *ওনার:* {owner_count} জন\n"
    admin_text += f"🔹 *অ্যাডমিন:* {admin_count} জন"
    
    bot.reply_to(message, admin_text, parse_mode='HTML')

@bot.message_handler(commands=['transferowner'])
def command_transfer_owner(message):
    global OWNER_ID
    
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        bot.reply_to(message, "⛔ *শুধুমাত্র ওনার ট্রান্সফার করতে পারেন!*", parse_mode='HTML')
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ *সঠিক ফরম্যাট:* `/transferowner USER_ID`", parse_mode='HTML')
            return
        target_user = int(parts[1])
        
        if target_user == OWNER_ID:
            bot.reply_to(message, "⚠️ *আপনি ইতিমধ্যে ওনার!*", parse_mode='HTML')
            return
        
        old_owner = OWNER_ID
        OWNER_ID = target_user
        
        if old_owner not in admin_list:
            admin_list.append(old_owner)
        
        bot.reply_to(message, 
            render_body_text(
                f"👑 *ওনারশিপ ট্রান্সফার করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"✅ নতুন ওনার: `{target_user}`\n"
                f"👤 পূর্ববর্তী ওনার: `{old_owner}`\n"
                f"✅ সফলভাবে ট্রান্সফার করা হয়েছে!"
            ),
            parse_mode='HTML'
        )
        
        try:
            bot.send_message(
                target_user,
                render_body_text(
                    f"👑 *আপনি এখন বটের নতুন ওনার!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"✅ আপনি এখন বট সম্পূর্ণভাবে পরিচালনা করতে পারবেন!"
                ),
                parse_mode='HTML'
            )
        except:
            pass
    except ValueError:
        bot.reply_to(message, "❌ *ইনভ্যালিড ইউজার আইডি!* শুধু সংখ্যা দিন।", parse_mode='HTML')

# ==================== DOCUMENT HANDLER ====================

# 🔥 পুরো ফাংশনটি কপি করে পেস্ট করুন (try-except সহ)

@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    doc = message.document
    logger.info(f"Doc from {user_id}: {doc.file_name} ({doc.mime_type}), Size: {doc.file_size}")

    upload_state = pending_upload_modes.get(user_id)
    if not upload_state or upload_state.get("stage") not in (
        "waiting_file", "waiting_requirements"
    ):
        bot.reply_to(
            message,
            render_body_text(
                "⛔ *এই file গ্রহণ করা হয়নি।*\n"
                "আগে *UPLOAD FILE* button-এ click করে "
                "AUTO অথবা MANUAL module mode select করুন।"
            ),
            parse_mode='HTML'
        )
        return

    upload_mode = upload_state.get("mode")
    upload_stage = upload_state.get("stage")
    forward_file_id = doc.file_id

    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, "⚠️ Bot locked, cannot accept files.")
        return

    file_name = doc.file_name
    if not file_name:
        bot.reply_to(message, "⚠️ No file name. Ensure file has a name.")
        return

    if user_id in file_stop_status and file_name in file_stop_status[user_id]:
        bot.reply_to(
            message,
            render_body_text(
                f"⛔ *এই ফাইলটি অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📄 ফাইল: `{file_name}`\n"
                f"⏳ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ আপলোড করা যাবে না!*\n\n"
                f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
            ),
            parse_mode='HTML'
        )
        return

    if user_id in file_stop_status and file_stop_status[user_id]:
        bot.reply_to(
            message,
            render_body_text(
                f"⛔ *আপনার একটি ফাইল অ্যাডমিন দ্বারা স্টপ করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📄 স্টপ করা ফাইল: `{file_stop_status[user_id][0]}`\n"
                f"⏳ *যতক্ষণ না অ্যাডমিন স্টার্ট করে ততক্ষণ নতুন ফাইল আপলোড করা যাবে না!*\n\n"
                f"💡 *অ্যাডমিনকে বলুন ফাইলটি স্টার্ট করতে*"
            ),
            parse_mode='HTML'
        )
        return

    # A requirements.txt document is an internal part of a manual upload.
    # It must not consume a separate lifetime upload/delete action.
    if (
        upload_stage == "waiting_file"
        and not is_file_action_quota_exempt(user_id)
        and is_file_action_limit_reached(user_id)
    ):
        bot.reply_to(message, file_action_limit_message(), parse_mode='HTML')
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, 
            render_body_text(
                f"⚠️ *ফাইল লিমিট শেষ!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📁 *আপনি {current_files}/{limit_str} ফাইল আপলোড করেছেন*\n\n"
                f"💡 *প্রিমিয়াম কিনতে ডিপোজিট করে প্রিমিয়াম প্লান কিনুন।*"
            ),
            parse_mode='HTML'
        )
        return

    file_ext = os.path.splitext(file_name)[1].lower()
    is_requirements_upload = upload_stage == "waiting_requirements"
    if is_requirements_upload:
        if os.path.basename(file_name).lower() != "requirements.txt":
            bot.reply_to(
                message,
                render_body_text(
                    "❌ Manual mode-এ প্রথম file-এর নাম অবশ্যই "
                    "`requirements.txt` হতে হবে।"
                ),
                parse_mode='HTML'
            )
            return
    elif file_ext not in ['.py', '.js', '.zip']:
        bot.reply_to(message, "⚠️ Unsupported type! Only `.py`, `.js`, `.zip` allowed.")
        return

    max_file_size = FILE_ACTION_SIZE_LIMIT_BYTES
    if (
        not is_file_action_quota_exempt(user_id)
        and (getattr(doc, "file_size", 0) or 0) > max_file_size
    ):
        bot.reply_to(
            message,
            "⚠️ File too large. Regular users can upload a maximum of 1 MB.",
            parse_mode='HTML'
        )
        return

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            bot.send_message(
                OWNER_ID,
                render_body_text(
                    f"📤 *New File Uploaded!*\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"📄 *File:* `{file_name}`\n"
                    f"👤 *User:* {keep_user_name_emojis_normal(message.from_user.first_name)}\n"
                    f"🆔 *User ID:* `{user_id}`"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to forward uploaded file to OWNER_ID {OWNER_ID}: {e}")

        download_wait_msg = bot.reply_to(
            message,
            render_body_text(
                f"{download_progress_emoji_tag()} Downloading `{file_name}`..."
            ),
            parse_mode='HTML'
        )
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)

        if (
            not is_file_action_quota_exempt(user_id)
            and len(downloaded_file_content) > FILE_ACTION_SIZE_LIMIT_BYTES
        ):
            bot.edit_message_text(
                render_body_text(
                    "⚠️ File too large. Regular users can upload a maximum of 1 MB."
                ),
                chat_id,
                download_wait_msg.message_id,
                parse_mode='HTML'
            )
            return
        
        if user_id != OWNER_ID:
            is_safe, reason = scan_file_for_malware(downloaded_file_content, file_name, user_id)
            if not is_safe:
                bot.edit_message_text(
                    render_body_text(
                        f"<tg-emoji emoji-id=\"{EMOJI_WARNING}\">⚠️</tg-emoji> Security Alert: {reason}"
                    ), 
                    chat_id, 
                    download_wait_msg.message_id,
                    parse_mode='HTML'
                )
                return

        # Normal users may host ordinary scripts, but uploading a hosting
        # panel/bot source is blocked and automatically bans that account.
        if (
            upload_stage != "waiting_requirements"
            and not is_bot_admin_user(user_id)
            and is_hosting_bot_file(downloaded_file_content, file_name)
        ):
            clear_pending_upload_state(user_id)
            ban_user(
                user_id,
                reason=f"Hosting bot file upload blocked: {file_name}",
                banned_by=OWNER_ID,
            )
            return
        
        bot.edit_message_text(
            render_body_text(
                f"<tg-emoji emoji-id=\"{EMOJI_SUCCESS}\">✅</tg-emoji> Downloaded `{file_name}`. Processing..."
            ), 
            chat_id, 
            download_wait_msg.message_id,
            parse_mode='HTML'
        )
        
        logger.info(f"Downloaded {file_name} for user {user_id}")
        user_folder = get_user_folder(user_id)

        # Manual mode intentionally stores the first bot file temporarily.
        # It is not counted, forwarded, or started until requirements.txt is
        # uploaded and installed successfully.
        if upload_mode == "manual" and upload_stage == "waiting_file":
            pending_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_manual_")
            pending_path = os.path.join(pending_dir, os.path.basename(file_name))
            with open(pending_path, 'wb') as pending_handle:
                pending_handle.write(downloaded_file_content)
            upload_state.update({
                "mode": "manual",
                "stage": "waiting_requirements",
                "pending_dir": pending_dir,
                "pending_file": {
                    "path": pending_path,
                    "file_name": file_name,
                    "file_ext": file_ext,
                    "file_id": doc.file_id,
                },
            })
            bot.reply_to(
                message,
                render_body_text(
                    f"✅ `{file_name}` received securely.\n"
                    "এখন `requirements.txt` file পাঠান।\n"
                    "Requirements install শেষ হলে এই bot file run হবে।"
                ),
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode='HTML'
            )
            return

        if is_requirements_upload:
            req_path = os.path.join(user_folder, "requirements.txt")
            with open(req_path, 'wb') as req_file_handle:
                req_file_handle.write(downloaded_file_content)

            if not install_python_requirements_file(req_path, message):
                return

            pending_file = upload_state.get("pending_file") or {}
            pending_path = pending_file.get("path")
            if not pending_path or not os.path.exists(pending_path):
                clear_pending_upload_state(user_id)
                bot.reply_to(
                    message,
                    "❌ Pending bot file পাওয়া যায়নি। আবার Upload File দিয়ে শুরু করুন।"
                )
                return

            try:
                with open(pending_path, 'rb') as pending_handle:
                    downloaded_file_content = pending_handle.read()
                file_name = pending_file["file_name"]
                file_ext = pending_file["file_ext"]
                forward_file_id = pending_file.get("file_id") or forward_file_id
                pending_dir = upload_state.get("pending_dir")
                if pending_dir and os.path.exists(pending_dir):
                    shutil.rmtree(pending_dir)
                upload_state.pop("pending_dir", None)
                upload_state.pop("pending_file", None)
            except Exception as e:
                logger.error(f"Could not restore pending manual upload for {user_id}: {e}", exc_info=True)
                clear_pending_upload_state(user_id)
                bot.reply_to(message, f"❌ Pending bot file restore failed: {e}")
                return

        # A valid script upload consumes one lifetime action.  Manual mode
        # reaches this point only after its requirements file is installed,
        # so requirements.txt does not consume a second action.
        if (
            not is_file_action_quota_exempt(user_id)
            and not consume_file_action_quota(
                user_id,
                getattr(message.from_user, "first_name", "Unknown")
            )
        ):
            clear_pending_upload_state(user_id)
            bot.reply_to(message, file_action_limit_message(), parse_mode='HTML')
            return

        # Consume the selected mode after the quota reservation succeeds.
        # If processing fails, the user can press Upload File again for a
        # fresh attempt, but the submitted action remains counted.
        pending_upload_modes.pop(user_id, None)

        if user_id not in user_upload_times:
            user_upload_times[user_id] = []
        user_upload_times[user_id].append(datetime.now())

        if file_ext == '.zip':
            handle_zip_file(
                downloaded_file_content, file_name, message,
                dependency_mode=upload_mode
            )
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(downloaded_file_content)
            logger.info(f"Saved single file to {file_path}")
            
            forward_file_to_group(user_id, file_name, file_ext[1:], message, forward_file_id)
            
            if file_ext == '.js':
                handle_js_file(
                    file_path, user_id, user_folder, file_name, message,
                    dependency_mode=upload_mode
                )
            elif file_ext == '.py':
                handle_py_file(
                    file_path, user_id, user_folder, file_name, message,
                    dependency_mode=upload_mode
                )
                
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Telegram API Error handling file for {user_id}: {e}", exc_info=True)
        if "file is too big" in str(e).lower():
            bot.reply_to(message, f"❌ Telegram API Error: File too large to download (~20MB limit).")
        else:
            bot.reply_to(message, f"❌ Telegram API Error: {str(e)}. Try later.")
    except Exception as e:
        logger.error(f"❌ General error handling file for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, f"❌ Unexpected error: {str(e)}")
##
# ==========================================
# ✅ FORCE JOIN REPLY KEYBOARD (Premium Emoji + Style)
# ==========================================
def create_force_join_reply_keyboard():
    """Create force join reply keyboard with premium emojis and colors"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # সারি ১: অ্যাড চ্যানেল + টগল
    markup.add(
        make_keyboard_button(
            "Add Channel", EMOJI_PLUS, "success", use_override=False
        ),
        make_keyboard_button(
            "Force Join চালু" if is_force_join_enabled() else "Force Join বন্ধ",
            EMOJI_FORCE_JOIN_ON if is_force_join_enabled() else EMOJI_FORCE_JOIN_OFF,
            "danger" if is_force_join_enabled() else "success",
            use_override=False
        )
    )
    
    # সারি ২: অ্যাডমিন বাইপাস
    markup.add(
        make_keyboard_button(
            "Admin Bypass: ON" if is_admin_bypass_enabled() else "Admin Bypass: OFF",
            EMOJI_SHIELD,
            "success" if is_admin_bypass_enabled() else "danger",
            use_override=False
        )
    )
    # Back is available only on the Force Join reply keyboard.
    markup.add(
        make_keyboard_button("Back", EMOJI_BACK, "primary", use_override=False)
    )
    
    return markup
# ==================== CALLBACK HANDLERS ====================

@bot.callback_query_handler(func=lambda call: True) 
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    logger.info(f"Callback: User={user_id}, Data='{data}'")

    # Inline buttons are also explicit new actions.  Cancel any stale
    # amount/TXID/screenshot prompt before routing the callback, otherwise a
    # later text message can still be consumed by the old next-step handler.
    try:
        bot.clear_step_handler_by_chat_id(call.message.chat.id)
    except Exception as exc:
        logger.debug(
            "Could not clear step handler before callback %s: %s",
            data,
            exc,
        )

    # Callback queries are handled by one catch-all route, so enforce the
    # ban here before any button action can run.
    if is_user_banned(user_id):
        bot.answer_callback_query(
            call.id,
            "⛔ You are banned from this bot.",
            show_alert=True
        )
        send_banned_user_notice(call.message.chat.id, user_id)
        return

    # Old inline keyboards must be unusable until this user presses the
    # restart button sent by the Update Bot broadcast.
    if is_restart_required(user_id):
        bot.answer_callback_query(
            call.id,
            "🔄 আগে RESTART BOT button-এ click করুন।",
            show_alert=True
        )
        send_restart_required_notice(call.message.chat.id)
        return

    if data.startswith("reset_file_quota_"):
        handle_reset_file_quota_callback(call)
        return

    # --- Force Join gate (verify button is the only allowed action) ---
    if data == 'fj_verify':
        handle_force_join_verify(call)
        return

    # Callback actions are another access path.  Always perform a fresh
    # membership check so a stale successful cache cannot unlock the bot.
    missing_channels = get_missing_force_channels(user_id, use_cache=False)
    if missing_channels:
        bot.answer_callback_query(
            call.id,
            "🔒 আগে required channel গুলোতে জয়েন করুন!",
            show_alert=True
        )
        send_force_join_prompt(call.message.chat.id, missing_channels,
                               call.from_user.first_name)
        return

    if data in ('referral', 'free_host', 'freehost_refresh'):
        bot.answer_callback_query(call.id)
        if data == 'referral':
            _logic_referral(call.message, user_id=user_id)
        else:
            _logic_free_host(call.message, user_id=user_id)
        return

    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'speed', 'stats']:
        bot.answer_callback_query(call.id, "⚠️ Bot locked by admin.", show_alert=True)
        return

    # --- Force Join admin callbacks ---
    if data in ('fj_add', 'fj_panel', 'fj_toggle', 'fj_test', 'fj_bypass') or data.startswith(('fj_edit_', 'fj_del_')):
        if not is_otp_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
            return
        if data == 'fj_add':
            handle_force_join_add(call)
        elif data == 'fj_toggle':
            handle_force_join_toggle(call)
        elif data == 'fj_bypass':
            handle_force_join_bypass_toggle(call)
        elif data == 'fj_test':
            handle_force_join_test(call)
        elif data == 'fj_panel':
            bot.answer_callback_query(call.id)
            refresh_force_join_panel(call)
        elif data.startswith('fj_edit_'):
            handle_force_join_edit(call, int(data.split('_')[-1]))
        else:
            handle_force_join_delete(call, int(data.split('_')[-1]))
        return

    # --- All Link Setup callbacks ---
    if data.startswith('link_set_') or data in ('link_rate', 'link_panel'):
        if not is_otp_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
            return
        if data == 'link_rate':
            handle_rate_set_request(call)
        elif data == 'link_panel':
            bot.answer_callback_query(call.id)
            refresh_link_setup_panel(call.message.chat.id, call.message.message_id)
        else:
            handle_link_set_request(call, data[len('link_set_'):])
        return

    # --- Broadcast callbacks ---
    if data in ('bc_single', 'bc_all'):
        if not is_otp_admin(user_id):
            bot.answer_callback_query(call.id, "⛔ Unauthorized!", show_alert=True)
            return
        if data == 'bc_single':
            handle_broadcast_single_request(call)
        else:
            handle_broadcast_all_request(call)
        return

    
    # --- STOP & DELETE Callbacks ---
    if data.startswith('stopdelete_'):
        handle_stopdelete_control(call)
        return
    
    if data == 'back_stopdelete':
        bot.answer_callback_query(call.id)
        handle_otp_stop_delete(call.message)
        return
    
    # --- Admin File Action Callbacks ---
    if data.startswith('admin_stop_'):
        handle_admin_stop(call)
        return
    
    if data.startswith('admin_start_'):
        handle_admin_start(call)
        return
    
    if data.startswith('admin_restart_'):
        handle_admin_restart(call)
        return
    
    if data.startswith('admin_delete_'):
        handle_admin_delete(call)
        return
    
    if data.startswith('admin_logs_'):
        handle_admin_logs(call)
        return
    
    # --- Deposit Callbacks ---
    if data.startswith('deposit_method_'):
        handle_deposit_method_selection(call)
        return
    
    if data == 'my_deposits':
        handle_my_deposits(call)
        return
    
    if data == 'back_deposit':
        bot.answer_callback_query(call.id)
        handle_deposit_user(call.message)
        return
    
    if data.startswith('approve_dep_'):
        handle_approve_deposit(call)
        return
    
    if data.startswith('reject_dep_'):
        handle_reject_deposit(call)
        return

    if data.startswith('unban_user_'):
        handle_unban_callback(call)
        return
    
    # --- DELETE PAYMENT METHOD CALLBACKS ---
    if data.startswith('delete_method_'):
        process_delete_payment_method(call)
        return
    
    if data.startswith('confirm_delete_method_'):
        process_confirm_delete_method(call)
        return
    
    if data == 'cancel_delete_method':
        process_cancel_delete_method(call)
        return
    
    if data == 'back_deposit_admin':
        bot.answer_callback_query(call.id)
        handle_admin_deposit_panel(call.message)
        return
    
    # --- Premium Plan Callbacks ---
    if data.startswith('buy_plan_'):
        process_buy_plan(call)
        return
    
    if data.startswith('remove_plan_'):
        process_remove_plan(call)
        return
    
    if data == 'confirm_reset_plans':
        process_reset_plans(call)
        return
    
    if data == 'cancel_reset_plans':
        process_cancel_reset(call)
        return
    
    if data == 'back_premium':
        bot.answer_callback_query(call.id)
        handle_premium_plan_user(call.message, user_id=call.from_user.id)
        return
    
    if data == 'back_premium_admin':
        bot.answer_callback_query(call.id)
        handle_premium_plan_admin(call.message, user_id=call.from_user.id)
        return
    
    # --- OTP Admin Callbacks ---
    if data == 'back_admin_panel':
        bot.answer_callback_query(call.id)
        handle_otp_admin_panel(call.message)
        return
    
    # --- Main Callbacks ---
    if data == 'upload': upload_callback(call)
    elif data == 'check_files': check_files_callback(call)
    elif data.startswith('file_'): file_control_callback(call)
    elif data.startswith('start_'): start_bot_callback(call)
    elif data.startswith('stop_'): stop_bot_callback(call)
    elif data.startswith('restart_'): restart_bot_callback(call)
    elif data.startswith('delete_'): delete_bot_callback(call)
    elif data.startswith('logs_'): logs_bot_callback(call)
    elif data == 'speed': speed_callback(call)
    elif data == 'back_to_main': back_to_main_callback(call)
    elif data == 'run_all_scripts': admin_required_callback(call, run_all_scripts_callback)
    elif data == 'gx_admin_panel': admin_required_callback(call, gx_admin_panel_callback)
    elif data == 'subscription': admin_required_callback(call, subscription_management_callback)
    elif data == 'stats': stats_callback(call)
    elif data == 'lock_bot': admin_required_callback(call, lock_bot_callback)
    elif data == 'unlock_bot': admin_required_callback(call, unlock_bot_callback)
    elif data == 'add_subscription': admin_required_callback(call, add_subscription_init_callback) 
    elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_init_callback) 
    elif data == 'check_subscription': admin_required_callback(call, check_subscription_init_callback) 
    else:
        bot.answer_callback_query(call.id, "Unknown action.")
        logger.warning(f"Unhandled callback data: {data} from user {user_id}")

# ==================== CALLBACK FUNCTIONS ====================
@bot.message_handler(func=lambda message: message.text in [
    "Add Plan",
    "Remove Plan",
    "Reset All Plans",
    "Show All Plans",
    "BACK TO ADMIN PANEL"
])
def handle_premium_admin_buttons(message):
    """Handle premium admin buttons"""
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "Add Plan":
        handle_add_premium_plan(message)
    elif text == "Remove Plan":
        handle_remove_premium_plan(message)
    elif text == "Reset All Plans":
        handle_reset_all_plans(message)
    elif text == "Show All Plans":
        show_all_plans(message)
    elif text == "BACK TO ADMIN PANEL":
        handle_otp_admin_panel(message)
# ==========================================
# ✅ BACK TO ADMIN PANEL BUTTON HANDLER
# ==========================================
@bot.message_handler(func=lambda message: message.text in [
    "DELETE bKash", "DELETE Nagad", "DELETE Rocket",
    "DELETE Upay", "DELETE Binance"
])
def handle_delete_method_click(message):
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    # বাটনের টেক্সট থেকে মেথড নাম বের করুন
    text = message.text
    method_name = text.replace("DELETE ", "", 1).strip()
    payment_delete_state[user_id] = {"method": method_name}
    
    # কনফার্মেশন
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        make_keyboard_button(
            f"✅ হ্যাঁ, {method_name} ডিলিট করুন", EMOJI_APPROVE, "success"
        ),
        make_keyboard_button("না, বাতিল করুন", EMOJI_REJECT, "primary")
    )
    
    bot.reply_to(message,
        render_body_text(
            f"⚠️ *আপনি কি নিশ্চিত?*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *মেথড:* `{method_name}`\n\n"
            f"❌ *এটি ডিলিট করলে আর ফেরত আসবে না!*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
@bot.message_handler(func=lambda message: message.text.startswith("DELETE "))
def handle_delete_method_selection(message):
    """Handle delete method selection from reply keyboard"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    # The trash icon is carried by the Premium button icon, not the label.
    if not text.startswith("DELETE "):
        bot.reply_to(message, "❌ *ইনভ্যালিড মেথড!*", parse_mode='HTML')
        return
    
    method_name = text.replace("DELETE ", "", 1).strip()
    payment_delete_state[user_id] = {"method": method_name}
    
    # BACK বাটন চেক করুন
    if text == "BACK":
        handle_admin_deposit_panel(message)
        return
    
    # কনফার্মেশন মেসেজ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        make_keyboard_button(
            f"✅ হ্যাঁ, {method_name} ডিলিট করুন", EMOJI_APPROVE, "success"
        ),
        make_keyboard_button("না, বাতিল করুন", EMOJI_REJECT, "primary")
    )
    
    bot.reply_to(message, 
        render_body_text(
            f"⚠️ *আপনি কি নিশ্চিত?*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *মেথড:* `{method_name}`\n\n"
            f"❌ *এটি ডিলিট করলে আর ফেরত আসবে না!*\n\n"
            f"💡 *নিশ্চিত হলে 'হ্যাঁ' বাটনে ক্লিক করুন*"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
    
    # ইউজার স্টেট সেভ করুন
    if not hasattr(handle_delete_method_selection, 'user_delete_state'):
        handle_delete_method_selection.user_delete_state = {}
    handle_delete_method_selection.user_delete_state[user_id] = {"method": method_name}

@bot.message_handler(func=lambda message: (
    (
        (message.text or "").startswith("হ্যাঁ,")
        or (message.text or "") == "না, বাতিল করুন"
    )
    # This handler is only active after a payment method was selected.
    and message.from_user.id in payment_delete_state
))
def handle_confirm_delete_method(message):
    """Handle confirm delete method"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ *Unauthorized!*", parse_mode='HTML')
        return
    
    if text == "না, বাতিল করুন":
        payment_delete_state.pop(user_id, None)
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ডিলিট বাতিল করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *কোনো মেথড ডিলিট করা হয়নি*"
            ),
            parse_mode='HTML'
        )
        handle_admin_delete_payment_method(message)
        return
    
    # Resolve the method from the active payment-delete flow.  Do not trust
    # the confirmation label because plan names can overlap with method names.
    method_name = payment_delete_state.get(user_id, {}).get("method")
    if not method_name:
        bot.reply_to(message, "❌ *ইনভ্যালিড রিকোয়েস্ট!*", parse_mode='HTML')
        return
    
    if delete_payment_method(method_name):
        bot.reply_to(message, 
            render_body_text(
                f"✅ *পেমেন্ট মেথড ডিলিট করা হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ *মেথড:* `{method_name}`\n"
                f"✅ *সফলভাবে রিমুভ করা হয়েছে!*"
            ),
            parse_mode='HTML'
        )
    else:
        bot.reply_to(message, 
            render_body_text(
                f"❌ *ডিলিট করতে ব্যর্থ হয়েছে!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *মেথড:* `{method_name}`\n"
                f"💡 *আবার চেষ্টা করুন*"
            ),
            parse_mode='HTML'
        )
    
    payment_delete_state.pop(user_id, None)
    # ডিপোজিট প্যানেলে ফিরে যান
    handle_admin_deposit_panel(message)    
@bot.message_handler(func=lambda message: message.text == "BACK")
def handle_back_from_deposit(message):
    """Handle back from deposit or delete"""
    user_id = message.from_user.id
    
    # যদি অ্যাডমিন হয় তাহলে ডিপোজিট প্যানেলে ফিরে যান
    if is_otp_admin(user_id):
        handle_admin_deposit_panel(message)
    else:
        handle_deposit_user(message)    
@bot.message_handler(func=lambda message: message.text in [
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
    "𝘽𝘼𝘾𝙆 𝙏𝙊 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇",
    "🔙 Back to Admin Panel",
    "Back to Admin Panel",
    "BACK TO ADMIN PANEL",
])
def handle_back_to_admin_panel(message):
    user_id = message.from_user.id
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, render_body_text("⛔ *Unauthorized!*"), parse_mode='HTML')
        return
    
    markup = create_otp_reply_keyboard(user_id)
    
    bot.reply_to(
        message, 
        render_body_text(
            f"🔴 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 \n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝘿𝙈𝙄𝙉❗\n"
            f"✅ 𝙔𝙊𝙐 𝙃𝘼𝙑𝙀 𝙁𝙐𝙇𝙇 𝘼𝘾𝘾𝙀𝙎𝙎 𝙏𝙊 𝘽𝙊𝙏 𝘾𝙊𝙉𝙏𝙍𝙊𝙇𝙎\n\n"
            f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )
    
    # অ্যাডমিন প্যানেল মেনু দেখান
    markup = create_otp_reply_keyboard(user_id)
    
    bot.reply_to(
        message, 
        render_body_text(
            f"🔴 𝙂𝙓 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 \n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"✅ 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 𝘼𝘿𝙈𝙄𝙉❗\n"
            f"✅ 𝙔𝙊𝙐 𝙃𝘼𝙑𝙀 𝙁𝙐𝙇𝙇 𝘼𝘾𝘾𝙀𝙎𝙎 𝙏𝙊 𝘽𝙊𝙏 𝘾𝙊𝙉𝙏𝙍𝙊𝙇𝙎\n\n"
            f"📌 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝙉 𝙊𝙋𝙏𝙄𝙊𝙉"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )

def run_all_scripts_callback(call):
    _logic_run_all_scripts(call)

def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin permissions required.", show_alert=True)
        return
    func_to_run(call)

def upload_callback(call):
    user_id = call.from_user.id
    
    if user_id in file_stop_status and file_stop_status[user_id]:
        bot.answer_callback_query(call.id, "⛔ আপনার একটি ফাইল স্টপ করা আছে! অ্যাডমিনকে বলুন স্টার্ট করতে।", show_alert=True)
        return
    
    if not is_file_action_quota_exempt(user_id) and is_file_action_limit_reached(user_id):
        bot.answer_callback_query(
            call.id,
            "⚠️ আপনার upload/delete limit শেষ। Admin reset করতে পারবেন।",
            show_alert=True
        )
        return

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.answer_callback_query(call.id, f"⚠️ File limit ({current_files}/{limit_str}) reached.", show_alert=True)
        return
    bot.answer_callback_query(call.id) 
    bot.send_message(call.message.chat.id, render_body_text("📤 Send your Python (`.py`), JS (`.js`), or ZIP (`.zip`) file."))

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id 
    user_files_list = get_user_files_for_owner(user_id)
    if not user_files_list:
        bot.answer_callback_query(call.id, "⚠️ No files uploaded.", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", callback_data='back_to_main'))
            bot.edit_message_text(render_body_text("📂 Your files:\n\n(No files uploaded)"), chat_id, call.message.message_id, reply_markup=markup)
        except Exception as e: logger.error(f"Error editing msg for empty file list: {e}")
        return
    bot.answer_callback_query(call.id) 
    markup = types.InlineKeyboardMarkup(row_width=1) 
    for file_name, file_type in sorted(user_files_list): 
        is_running = is_bot_running(user_id, file_name)
        is_stopped = user_id in file_stop_status and file_name in file_stop_status[user_id]
        
        if is_stopped:
            status_icon = "⏹️ Stopped"
        elif is_running:
            status_icon = "🟢 Running"
        else:
            status_icon = "🔴 Stopped"
            
        btn_text = f"{file_name} ({file_type}) - {status_icon}"
        markup.add(types.InlineKeyboardButton(
            btn_text,
            callback_data=make_file_callback('file', user_id, file_name),
            icon_custom_emoji_id=EMOJI_GREEN if is_running and not is_stopped else EMOJI_RED
        ))
    markup.add(types.InlineKeyboardButton("𝘽𝘼𝘾𝙆 𝙏𝙊 𝙈𝘼𝙄𝙉", callback_data='back_to_main'))
    try:
        bot.edit_message_text(render_body_text("📂 Your files:\nClick to manage."), chat_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e): logger.warning("Msg not modified (files).")
         else: logger.error(f"Error editing msg for file list: {e}")
    except Exception as e: logger.error(f"Unexpected error editing msg for file list: {e}", exc_info=True)

def file_control_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'file')
        if not resolved:
            raise ValueError("invalid file callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            logger.warning(f"User {requesting_user_id} tried to access file '{file_name}' of user {script_owner_id} without permission.")
            bot.answer_callback_query(call.id, "⚠️ You can only manage your own files.", show_alert=True)
            check_files_callback(call)
            return

        user_files_list = get_user_files_for_owner(script_owner_id)
        if not any(f[0] == file_name for f in user_files_list):
            logger.warning(f"File '{file_name}' not found for user {script_owner_id} during control.")
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True)
            check_files_callback(call) 
            return

        bot.answer_callback_query(call.id) 
        is_running = is_bot_running(script_owner_id, file_name)
        is_stopped = script_owner_id in file_stop_status and file_name in file_stop_status[script_owner_id]
        
        if is_stopped:
            status_text = '⏹️ Stopped'
        elif is_running:
            status_text = '🟢 Running'
        else:
            status_text = '🔴 Stopped'
            
        file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?') 
        try:
            bot.edit_message_text(
                render_body_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\n{status_emoji_tag()} Status: {status_text}"),
                call.message.chat.id, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_running and not is_stopped),
                parse_mode='HTML'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified (controls for {file_name})")
             else: raise 
    except (ValueError, IndexError) as ve:
        logger.error(f"Error parsing file control callback: {ve}. Data: '{call.data}'")
        bot.answer_callback_query(call.id, "Error: Invalid action data.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in file_control_callback for data '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "An error occurred.", show_alert=True)

def start_bot_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'start')
        if not resolved:
            raise ValueError("invalid start callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Start request: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied to start this script.", show_alert=True); return

        user_files_list = get_user_files_for_owner(script_owner_id)
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        if script_owner_id in file_stop_status and file_name in file_stop_status[script_owner_id]:
            bot.answer_callback_query(call.id, "⏰ এই ফাইলটি স্টপ করা হয়েছে!", show_alert=True)
            return

        file_type = file_info[1]
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)

        if not os.path.exists(file_path):
            if not _restore_one_hosted_file_from_drive(
                script_owner_id, file_name
            ):
                bot.answer_callback_query(
                    call.id,
                    "⚠️ File is missing and no usable Drive backup was found. "
                    "Please re-upload it; its database record has been kept.",
                    show_alert=True,
                )
                check_files_callback(call)
                return

        if is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"⚠️ Script '{file_name}' already running.", show_alert=True)
            try: bot.edit_message_reply_markup(chat_id_for_reply, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, True))
            except Exception as e: logger.error(f"Error updating buttons (already running): {e}")
            return

        bot.answer_callback_query(call.id, f"⏳ Attempting to start {file_name} for user {script_owner_id}...")

        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ Error: Unknown file type '{file_type}' for '{file_name}'."); return 

        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name) 
        status_text = '🟢 Running' if is_now_running else '🟡 Starting (or failed, check logs/replies)'
        try:
            bot.edit_message_text(
                render_body_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\n{status_emoji_tag()} Status: {status_text}"),
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='HTML'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified after starting {file_name}")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing start callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid start command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error starting script.", show_alert=True)
        try:
            resolved_err = resolve_file_callback(call.data, 'start')
            if not resolved_err:
                raise ValueError("invalid start callback")
            script_owner_id_err, file_name_err = resolved_err
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Failed to update buttons after start error: {e_btn}")

def stop_bot_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'stop')
        if not resolved:
            raise ValueError("invalid stop callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Stop request: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = get_user_files_for_owner(script_owner_id)
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1] 
        script_key = f"{script_owner_id}_{file_name}"

        if not is_bot_running(script_owner_id, file_name): 
            bot.answer_callback_query(call.id, f"⚠️ Script '{file_name}' already stopped.", show_alert=True)
            try:
                 bot.edit_message_text(
                     render_body_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\n{status_emoji_tag()} Status: 🔴 Stopped"),
                     chat_id_for_reply, call.message.message_id,
                     reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='HTML')
            except Exception as e: logger.error(f"Error updating buttons (already stopped): {e}")
            return

        bot.answer_callback_query(call.id, f"⏳ Stopping {file_name} for user {script_owner_id}...")
        process_info = bot_scripts.get(script_key)
        if process_info:
            kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]; logger.info(f"Removed {script_key} from running after stop.")
        else: logger.warning(f"Script {script_key} running by psutil but not in bot_scripts dict.")

        try:
            bot.edit_message_text(
                render_body_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\n{status_emoji_tag()} Status: 🔴 Stopped"),
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, False), parse_mode='HTML'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified after stopping {file_name}")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing stop callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid stop command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in stop_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error stopping script.", show_alert=True)

def restart_bot_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'restart')
        if not resolved:
            raise ValueError("invalid restart callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Restart: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = get_user_files_for_owner(script_owner_id)
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        if script_owner_id in file_stop_status and file_name in file_stop_status[script_owner_id]:
            bot.answer_callback_query(call.id, "⏰ এই ফাইলটি স্টপ করা হয়েছে!", show_alert=True)
            return

        file_type = file_info[1]; user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name); script_key = f"{script_owner_id}_{file_name}"

        if not os.path.exists(file_path):
            if not _restore_one_hosted_file_from_drive(
                script_owner_id, file_name
            ):
                bot.answer_callback_query(
                    call.id,
                    "⚠️ File is missing and no usable Drive backup was found. "
                    "Please re-upload it; its database record has been kept.",
                    show_alert=True,
                )
                check_files_callback(call)
                return

        bot.answer_callback_query(call.id, f"⏳ Restarting {file_name} for user {script_owner_id}...")
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Restart: Stopping existing {script_key}...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(1.5) 

        logger.info(f"Restart: Starting script {script_key}...")
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"❌ Unknown type '{file_type}' for '{file_name}'."); return

        time.sleep(1.5) 
        is_now_running = is_bot_running(script_owner_id, file_name) 
        status_text = '🟢 Running' if is_now_running else '🟡 Starting (or failed)'
        try:
            bot.edit_message_text(
                render_body_text(f"⚙️ Controls for: `{file_name}` ({file_type}) of User `{script_owner_id}`\n{status_emoji_tag()} Status: {status_text}"),
                chat_id_for_reply, call.message.message_id,
                reply_markup=create_control_buttons(script_owner_id, file_name, is_now_running), parse_mode='HTML'
            )
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified (restart {file_name})")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing restart callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid restart command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in restart_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error restarting.", show_alert=True)
        try:
            resolved_err = resolve_file_callback(call.data, 'restart')
            if not resolved_err:
                raise ValueError("invalid restart callback")
            script_owner_id_err, file_name_err = resolved_err
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Failed to update buttons after restart error: {e_btn}")

def delete_bot_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'delete')
        if not resolved:
            raise ValueError("invalid delete callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Delete: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = get_user_files_for_owner(script_owner_id)
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        # A user's own deletion is also one lifetime file action.  Admin
        # deletions are maintenance actions and do not consume that user's
        # quota.
        if (
            requesting_user_id == script_owner_id
            and not is_file_action_quota_exempt(script_owner_id)
            and not consume_file_action_quota(
                script_owner_id,
                getattr(call.from_user, "first_name", "Unknown")
            )
        ):
            bot.answer_callback_query(
                call.id,
                "⚠️ আপনার upload/delete limit শেষ। Admin reset করতে পারবেন।",
                show_alert=True
            )
            bot.send_message(
                chat_id_for_reply,
                file_action_limit_message(),
                parse_mode='HTML'
            )
            return

        bot.answer_callback_query(call.id, f"🗑️ Deleting {file_name} for user {script_owner_id}...")
        script_key = f"{script_owner_id}_{file_name}"
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Delete: Stopping {script_key}...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(0.5) 

        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        deleted_disk = []
        if os.path.exists(file_path):
            try: os.remove(file_path); deleted_disk.append(file_name); logger.info(f"Deleted file: {file_path}")
            except OSError as e: logger.error(f"Error deleting {file_path}: {e}")
        if os.path.exists(log_path):
            try: os.remove(log_path); deleted_disk.append(os.path.basename(log_path)); logger.info(f"Deleted log: {log_path}")
            except OSError as e: logger.error(f"Error deleting log {log_path}: {e}")

        remove_user_file_db(script_owner_id, file_name)
        deleted_str = ", ".join(f"`{f}`" for f in deleted_disk) if deleted_disk else "associated files"
        try:
            bot.edit_message_text(
                render_body_text(f"🗑️ Record `{file_name}` (User `{script_owner_id}`) and {deleted_str} deleted!"),
                chat_id_for_reply, call.message.message_id, reply_markup=None, parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error editing msg after delete: {e}")
            bot.send_message(chat_id_for_reply, render_body_text(f"🗑️ Record `{file_name}` deleted."), parse_mode='HTML')
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing delete callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid delete command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in delete_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error deleting.", show_alert=True)

def logs_bot_callback(call):
    try:
        resolved = resolve_file_callback(call.data, 'logs')
        if not resolved:
            raise ValueError("invalid logs callback")
        script_owner_id, file_name = resolved
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Logs: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = get_user_files_for_owner(script_owner_id)
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        user_folder = get_user_folder(script_owner_id)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, f"⚠️ No logs for '{file_name}'.", show_alert=True); return

        bot.answer_callback_query(call.id) 
        try:
            log_content = ""; file_size = os.path.getsize(log_path)
            max_log_kb = 100; max_tg_msg = 4096
            if file_size == 0: log_content = "(Log empty)"
            elif file_size > max_log_kb * 1024:
                 with open(log_path, 'rb') as f: f.seek(-max_log_kb * 1024, os.SEEK_END); log_bytes = f.read()
                 log_content = log_bytes.decode('utf-8', errors='ignore')
                 log_content = f"(Last {max_log_kb} KB)\n...\n" + log_content
            else:
                 with open(log_path, 'r', encoding='utf-8', errors='ignore') as f: log_content = f.read()

            if len(log_content) > max_tg_msg:
                log_content = log_content[-max_tg_msg:]
                first_nl = log_content.find('\n')
                if first_nl != -1: log_content = "...\n" + log_content[first_nl+1:]
                else: log_content = "...\n" + log_content 
            if not log_content.strip(): log_content = "(No visible content)"

            bot.send_message(chat_id_for_reply, render_body_text(f"📜 Logs for `{file_name}` (User `{script_owner_id}`):\n```\n{log_content}\n```"), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error reading/sending log {log_path}: {e}", exc_info=True)
            bot.send_message(chat_id_for_reply, f"❌ Error reading log for `{file_name}`.")
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing logs callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid logs command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in logs_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error fetching logs.", show_alert=True)

def speed_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    start_cb_ping_time = time.time() 
    try:
        bot.edit_message_text(
            render_body_text(f"{bot_speed_emoji_tag()} Testing speed..."),
            chat_id,
            call.message.message_id
        )
        bot.send_chat_action(chat_id, 'typing') 
        response_time = round((time.time() - start_cb_ping_time) * 1000, 2)
        status = "🔓 Unlocked" if not bot_locked else "🔒 Locked"
        if user_id == OWNER_ID: user_level = "👑 Owner"
        elif user_id in admin_ids: user_level = "🛡️ Admin"
        elif get_active_premium_plan(user_id) or (
            user_id in user_subscriptions
            and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now()
        ): user_level = premium_user_status_label()
        else: user_level = free_user_status_label()
        speed_msg = render_body_text(
            f"𝘽𝙊𝙏 𝙎𝙋𝙀𝙀𝘿 & {status_emoji_tag()} Status:\n\n⏱️ API Response Time: {response_time} ms\n"
            f"🤖 Bot {status_emoji_tag()} Status: {status}\n"
            f"👤 Your Level: {user_level}"
        )
        bot.answer_callback_query(call.id) 
        bot.edit_message_text(speed_msg, chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))
    except Exception as e:
         logger.error(f"Error during speed test (cb): {e}", exc_info=True)
         bot.answer_callback_query(call.id, "Error in speed test.", show_alert=True)
         try: bot.edit_message_text(render_body_text("〽️ Main Menu"), chat_id, call.message.message_id, reply_markup=create_main_menu_inline(user_id))
         except Exception: pass

def back_to_main_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    expiry_info = ""
    premium = get_active_premium_plan(user_id)
    if premium:
        user_status = premium_user_status_label()
        days_left = (premium["expiry"] - datetime.now()).days
        expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
    elif user_id == OWNER_ID: user_status = "👑 Owner"
    elif user_id in admin_ids: user_status = "🛡️ Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = premium_user_status_label(); days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n⏳ Subscription expires in: {days_left} days"
        else: user_status = free_user_status_label(expired=True)
    else: user_status = free_user_status_label()
    
    balance = get_user_balance_db(user_id)
    
    main_menu_text = render_body_text(
        f"〽️ Welcome back, {keep_user_name_emojis_normal(call.from_user.first_name)}!\n\n🆔 ID: `{user_id}`\n"
        f"{status_emoji_tag()} Status: {user_status}{expiry_info}\n{balance_emoji_tag()} Balance: ৳{balance:.2f}\n📁 Files: {current_files} / {limit_str}\n\n"
        f"👇 Use buttons or type commands."
    )
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(main_menu_text, chat_id, call.message.message_id,
                              reply_markup=create_main_menu_inline(user_id), parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e): logger.warning("Msg not modified (back_to_main).")
         else: logger.error(f"API error on back_to_main: {e}")
    except Exception as e: logger.error(f"Error handling back_to_main: {e}", exc_info=True)

def subscription_management_callback(call):
    bot.answer_callback_query(call.id)
    try:
        # 🔥 Gift Box ইমোজি ব্যবহার করুন
        bot.edit_message_text(
            render_body_text(
                f"<tg-emoji emoji-id=\"{EMOJI_GIFT_BOX}\">🎁</tg-emoji> 𝑺𝒖𝒃𝒔𝒄𝒓𝒊𝒑𝒕𝒊𝒐𝒏 𝑴𝒂𝒏𝒂𝒈𝒆𝒎𝒆𝒏𝒕\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "📌 𝑺𝒆𝒍𝒆𝒄𝒕 𝒂𝒏 𝒂𝒄𝒕𝒊𝒐𝒏:"
            ),
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=create_subscription_menu(),
            parse_mode='HTML'
        )
    except Exception as e: 
        logger.error(f"Error showing sub menu: {e}")

def stats_callback(call):
    bot.answer_callback_query(call.id)
    _logic_statistics(call.message)
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                      reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e:
        logger.error(f"Error updating menu after stats_callback: {e}")

def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    logger.warning(f"Bot locked by Admin {call.from_user.id}")
    bot.answer_callback_query(call.id, "🔒 Bot locked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Error updating menu (lock): {e}")

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    logger.warning(f"Bot unlocked by Admin {call.from_user.id}")
    bot.answer_callback_query(call.id, "🔓 Bot unlocked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Error updating menu (unlock): {e}")

def add_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, render_body_text("💳 Enter User ID & days (e.g., `12345678 30`).\n/cancel to abort."))
    bot.register_next_step_handler(msg, process_add_subscription_details)

def remove_subscription_init_callback(call):
    """Start the remove-subscription flow from the inline admin menu."""
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        render_body_text("❌ Enter User ID to remove subscription.\n/cancel to abort."),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_remove_subscription_id)

def check_subscription_init_callback(call):
    """Start the check-subscription flow from the inline admin menu."""
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        render_body_text("✅ Enter User ID to check subscription.\n/cancel to abort."),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(msg, process_check_subscription_id)

def process_add_subscription_details(message):
    """Process add subscription with premium emojis"""
    admin_id_check = message.from_user.id 
    if admin_id_check not in admin_ids:
        bot.reply_to(message, "⚠️ Not authorized.")
        return
    if _subscription_cancel_requested(message):
        bot.reply_to(
            message,
            render_body_text("❌ Subscription add বাতিল করা হয়েছে।"),
            parse_mode='HTML'
        )
        _logic_subscriptions_panel(message)
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("Incorrect format")
        sub_user_id = int(parts[0].strip())
        days = int(parts[1].strip())
        if sub_user_id <= 0 or days <= 0:
            raise ValueError("User ID/days must be positive")

        current_expiry = user_subscriptions.get(sub_user_id, {}).get('expiry')
        start_date_new_sub = datetime.now()
        if current_expiry and current_expiry > start_date_new_sub:
            start_date_new_sub = current_expiry
        new_expiry = start_date_new_sub + timedelta(days=days)
        save_subscription(sub_user_id, new_expiry)

        logger.info(f"Sub for {sub_user_id} by admin {admin_id_check}. Expiry: {new_expiry:%Y-%m-%d}")
        
        # ✅ প্রিমিয়াম ইমোজি সহ অ্যাডমিন কনফার্মেশন
        admin_msg = render_body_text(
            f"<tg-emoji emoji-id=\"{EMOJI_GIFT_BOX}\">🎁</tg-emoji> *Subscription Added!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"<tg-emoji emoji-id=\"{EMOJI_USER_ID}\">🆔</tg-emoji> *User ID:* `{sub_user_id}`\n"
            f"<tg-emoji emoji-id=\"{EMOJI_CALENDAR}\">📅</tg-emoji> *Days Added:* `{days}`\n"
            f"<tg-emoji emoji-id=\"{EMOJI_CLOCK}\">⏰</tg-emoji> *Expiry:* `{new_expiry.strftime('%Y-%m-%d %H:%M')}`\n\n"
            f"<tg-emoji emoji-id=\"{EMOJI_SUCCESS}\">✅</tg-emoji> Successfully activated!"
        )
        bot.reply_to(message, admin_msg, parse_mode='HTML')

        # ✅ ইউজারের জন্য প্রিমিয়াম ইমোজি সহ সুন্দর নোটিফিকেশন (৩টি লাইন বাদ)
        try:
            user_name = "User"
            try:
                chat = bot.get_chat(sub_user_id)
                user_name = chat.first_name or "User"
            except:
                pass
            
            user_msg = render_body_text(
                f"<tg-emoji emoji-id=\"{EMOJI_GIFT_BOX}\">🎁</tg-emoji> *Premium Activated!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"<tg-emoji emoji-id=\"{EMOJI_CROWN}\">👑</tg-emoji> *Hello {keep_user_name_emojis_normal(user_name)}!*\n\n"
                f"<tg-emoji emoji-id=\"{EMOJI_PREMIUM}\">〽️</tg-emoji> *Your subscription has been activated!*\n"
                f"<tg-emoji emoji-id=\"{EMOJI_CALENDAR}\">📅</tg-emoji> *Duration:* `{days} days`\n"
                f"<tg-emoji emoji-id=\"{EMOJI_CLOCK}\">⏰</tg-emoji> *Expires:* `{new_expiry.strftime('%Y-%m-%d %H:%M')}`\n\n"
                f"<tg-emoji emoji-id=\"{EMOJI_STAR}\">⭐</tg-emoji> *Enjoy Premium Features!*"
            )
            bot.send_message(sub_user_id, user_msg, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to notify {sub_user_id}: {e}")
            
    except ValueError as e:
        bot.reply_to(message, f"⚠️ Invalid: {e}. Format: `ID days` or /cancel.", parse_mode='HTML')
        msg = bot.send_message(message.chat.id, render_body_text("💳 Enter User ID & days, or /cancel."), parse_mode='HTML')
        bot.register_next_step_handler(msg, process_add_subscription_details)
    except Exception as e:
        logger.error(f"Error processing add sub: {e}", exc_info=True)
        bot.reply_to(message, "❌ Error.", parse_mode='HTML')

def process_remove_subscription_id(message):
    """Remove an admin-managed subscription by user ID."""
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Not authorized."), parse_mode='HTML')
        return

    if _subscription_cancel_requested(message):
        bot.reply_to(
            message,
            render_body_text("❌ Remove Subscription বাতিল করা হয়েছে।"),
            parse_mode='HTML'
        )
        _logic_subscriptions_panel(message)
        return

    text = (getattr(message, "text", "") or "").strip()
    if not re.fullmatch(r"\d{1,15}", text):
        bot.reply_to(
            message,
            render_body_text("❌ সঠিক numeric User ID দিন অথবা /cancel লিখুন।"),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, process_remove_subscription_id)
        return

    target_user_id = int(text)
    if target_user_id not in user_subscriptions:
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *এই User ID-এর কোনো subscription পাওয়া যায়নি!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🆔 User ID: `{target_user_id}`"
            ),
            parse_mode='HTML'
        )
        _logic_subscriptions_panel(message)
        return

    expiry = user_subscriptions[target_user_id].get("expiry")
    remove_subscription_db(target_user_id)
    bot.reply_to(
        message,
        render_body_text(
            f"✅ *Subscription সফলভাবে remove করা হয়েছে!*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 User ID: `{target_user_id}`\n"
            f"⏰ আগের expiry: `{expiry.strftime('%Y-%m-%d %H:%M') if expiry else 'N/A'}`"
        ),
        parse_mode='HTML'
    )

    try:
        bot.send_message(
            target_user_id,
            render_body_text("ℹ️ Admin আপনার premium subscription remove করেছেন।"),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.info(f"Could not notify removed-subscription user {target_user_id}: {e}")

    _logic_subscriptions_panel(message)

def process_check_subscription_id(message):
    """Show an admin the current subscription for a user ID."""
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids:
        bot.reply_to(message, render_body_text("⚠️ Not authorized."), parse_mode='HTML')
        return

    if _subscription_cancel_requested(message):
        bot.reply_to(
            message,
            render_body_text("❌ Check Subscription বাতিল করা হয়েছে।"),
            parse_mode='HTML'
        )
        _logic_subscriptions_panel(message)
        return

    text = (getattr(message, "text", "") or "").strip()
    if not re.fullmatch(r"\d{1,15}", text):
        bot.reply_to(
            message,
            render_body_text("❌ সঠিক numeric User ID দিন অথবা /cancel লিখুন।"),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(message, process_check_subscription_id)
        return

    target_user_id = int(text)
    subscription = user_subscriptions.get(target_user_id)
    if not subscription:
        bot.reply_to(
            message,
            render_body_text(
                f"❌ *এই User ID-এর কোনো subscription নেই!*\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🆔 User ID: `{target_user_id}`"
            ),
            parse_mode='HTML'
        )
        _logic_subscriptions_panel(message)
        return

    expiry = subscription.get("expiry")
    if not expiry or expiry <= datetime.now():
        remove_subscription_db(target_user_id)
        status_text = "❌ Expired (database থেকে remove করা হয়েছে)"
    else:
        days_left = max(0, (expiry - datetime.now()).days)
        status_text = f"✅ Active — {days_left} দিন বাকি"

    bot.reply_to(
        message,
        render_body_text(
            f"📋 *Subscription Details*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 User ID: `{target_user_id}`\n"
            f"{status_emoji_tag()} Status: {status_text}\n"
            f"⏰ Expiry: `{expiry.strftime('%Y-%m-%d %H:%M') if expiry else 'N/A'}`"
        ),
        parse_mode='HTML'
    )
    _logic_subscriptions_panel(message)

# ==========================================
# 🔒 FORCE JOIN - ADMIN PANEL
# ==========================================
def build_force_join_admin_markup():
    """Admin controls for the force join channel list."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    for channel in get_force_channels():
        markup.add(
            types.InlineKeyboardButton(
                channel['button_name'],
                callback_data=f"fj_edit_{channel['id']}",
                icon_custom_emoji_id=EMOJI_ALL_CHANNEL_BUTTON,
                style="primary"  # 🔵 নীল
            ),
            types.InlineKeyboardButton(
                "🗑️ Delete",
                callback_data=f"fj_del_{channel['id']}",
                style="danger"  # 🔴 লাল
            )
        )
    markup.add(
        types.InlineKeyboardButton(
            "Add Channel",
            callback_data='fj_add',
            icon_custom_emoji_id=EMOJI_PLUS,
            style="success"  # 🟢 সবুজ
        )
    )
    
    # Force Join Toggle - রঙ পরিবর্তন হবে স্ট্যাটাস অনুযায়ী
    fj_status = "চালু" if is_force_join_enabled() else "বন্ধ"
    fj_color = "danger" if is_force_join_enabled() else "success"
    markup.add(
        types.InlineKeyboardButton(
            f"Force Join {fj_status}",
            callback_data='fj_toggle',
            icon_custom_emoji_id=(
                EMOJI_FORCE_JOIN_ON if is_force_join_enabled()
                else EMOJI_FORCE_JOIN_OFF
            ),
            style=fj_color
        ),
    )
    
    # Admin Bypass Toggle
    bypass_status = "ON" if is_admin_bypass_enabled() else "OFF"
    bypass_color = "success" if is_admin_bypass_enabled() else "danger"
    markup.add(
        types.InlineKeyboardButton(
            f"👑 Admin Bypass: {bypass_status}",
            callback_data='fj_bypass',
            style=bypass_color
        )
    )
    
    return markup


def build_force_join_admin_text():
    """Readable summary of every configured force join channel."""
    channels = get_force_channels()
    status = "🟢 চালু" if is_force_join_enabled() else "🔴 বন্ধ"
    text = (
        f"🔒 Force Join Setup\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"⚙️ {status_emoji_tag()} স্ট্যাটাস: {status}\n"
        f"📢 মোট channel: {len(channels)}\n\n"
    )
    if not channels:
        text += "📌 এখনো কোনো channel যোগ করা হয়নি।\n\n"
    else:
        for index, channel in enumerate(channels, 1):
            ref = channel["chat_ref"] or channel["chat_id"] or "⚠️ verify করা যাবে না"
            text += (
                f"{index}. {channel['button_name']}\n"
                f"   🔗 {channel['channel_url']}\n"
                f"   🆔 {ref}\n\n"
            )
    text += (
        f"👑 Admin Bypass: {'✅ ON' if is_admin_bypass_enabled() else '❌ OFF'}\n"
        f"   (ON থাকলে Admin/Owner-কে join করতে হয় না)\n\n"
        "📌 নিচের বাটন ব্যবহার করুন:"
    )
    return text

##
@bot.message_handler(func=lambda message: message.text in [
    "Add Channel",
    "Force Join চালু",
    "Force Join বন্ধ",
    "Admin Bypass: ON",
    "Admin Bypass: OFF",
    "Back"
])
def handle_force_join_reply_buttons(message):
    """Handle force join reply keyboard buttons"""
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    if text == "Add Channel":
        # অ্যাড চ্যানেল প্রম্পট
        prompt = bot.send_message(
            message.chat.id,
            render_body_text(
                "➕ নতুন Force Join Channel\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "📌 এই ফরম্যাটে পাঠান:\n"
                "Join Channel / https://t.me/example\n\n"
                f"{private_channel_emoji_tag()} Private channel হলে শেষে channel ID দিন:\n"
                "Join Channel / https://t.me/+abc123 / -1001234567890\n\n"
                "🤖 বটকে আগে ওই channel-এ Admin বানাতে হবে।\n"
                "💡 বাতিল করতে /cancel লিখুন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(prompt, process_force_join_add)
        
    elif text in ["Force Join চালু", "Force Join বন্ধ"]:
        # টগল
        set_force_join_enabled(not is_force_join_enabled())
        bot.reply_to(
            message,
            render_body_text(
                "🟢 Force Join চালু!" if is_force_join_enabled() else "🔴 Force Join বন্ধ!"
            ),
            parse_mode='HTML'
        )
        # প্যানেল রিফ্রেশ
        handle_force_join_panel(message)
        
    elif text in ["Admin Bypass: ON", "Admin Bypass: OFF"]:
        # বাইপাস টগল
        set_admin_bypass_enabled(not is_admin_bypass_enabled())
        bot.reply_to(
            message,
            render_body_text(
                "👑 Admin Bypass ON" if is_admin_bypass_enabled() else "👑 Admin Bypass OFF"
            ),
            parse_mode='HTML'
        )
        handle_force_join_panel(message)
        
    elif text == "Back":
        handle_otp_admin_panel(message)
        
#
# ==========================================
# ✅ BROADCAST REPLY KEYBOARD (Premium Emoji + Style)
# ==========================================
def create_broadcast_reply_keyboard():
    """Create broadcast reply keyboard with premium emojis and colors"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # সারি ১: সিঙ্গেল ইউজার + অল ইউজার
    markup.add(
        make_keyboard_button("Single User", EMOJI_USER_ICON, "primary"),
        make_keyboard_button("All Users", EMOJI_MEGAPHONE, "success")
    )
    
    # সারি ২: ব্যাক (একা)
    markup.add(
        make_keyboard_button("Back", EMOJI_BACK, "primary")
    )
    
    return markup
#
def handle_force_join_panel(message):
    """Show the Force Join admin section with reply keyboard."""
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    # 🔥 রিপ্লাই কীবোর্ড ব্যবহার করুন
    markup = create_force_join_reply_keyboard()
    
    bot.reply_to(
        message,
        render_body_text(build_force_join_admin_text()),
        reply_markup=markup,
        parse_mode='HTML'
    )


def refresh_force_join_panel(call):
    """Redraw the Force Join panel in place."""
    bot.edit_message_text(
        render_body_text(build_force_join_admin_text()),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=build_force_join_admin_markup(),
        parse_mode='HTML'
    )


def handle_force_join_toggle(call):
    """Switch the whole force join requirement on or off."""
    set_force_join_enabled(not is_force_join_enabled())
    bot.answer_callback_query(
        call.id,
        "🟢 Force Join চালু!" if is_force_join_enabled() else "🔴 Force Join বন্ধ!"
    )
    refresh_force_join_panel(call)


def send_force_join_status(message):
    """Diagnostic report for admins."""
    user_id = message.from_user.id
    channels = get_force_channels()
    lines = [
        f"🩺 Force Join {status_emoji_tag()} Status",
        "━━━━━━━━━━━━━━━",
        "",
        f"⚙️ Force Join: {'🟢 ON' if is_force_join_enabled() else '🔴 OFF'}",
        f"👑 Admin Bypass: {'ON' if is_admin_bypass_enabled() else 'OFF'}",
        f"👤 আপনার ID: {user_id}",
        f"🔓 আপনি exempt: {'হ্যাঁ (আপনাকে button দেখাবে না)' if force_join_exempt(user_id) else 'না'}",
        f"📢 মোট channel: {len(channels)}",
        "",
    ]
    bot_id = get_bot_id()
    for index, channel in enumerate(channels, 1):
        target = channel.get('chat_id') or channel.get('chat_ref')
        if not target:
            state = "❌ ID/username নেই — আবার add করুন"
        else:
            try:
                member = bot.get_chat_member(target, bot_id)
                state = ("✅ বট Admin আছে"
                         if getattr(member, 'status', '') in ADMIN_STATUSES
                         else "❌ বট Admin নয়")
            except Exception as e:
                state = f"❌ {e}"
        lines.append(f"{index}. {channel['button_name']} — {state}")
    if not channels:
        lines.append("📌 কোনো channel যোগ করা হয়নি।")
    lines += [
        "",
        "💡 নিজে টেস্ট করতে Admin Bypass OFF করুন অথবা অন্য একটি account থেকে /start দিন।",
    ]
    bot.reply_to(message, render_body_text("\n".join(lines)), parse_mode='HTML')


def handle_force_join_bypass_toggle(call):
    """Turn the admin/owner bypass on or off."""
    set_admin_bypass_enabled(not is_admin_bypass_enabled())
    bot.answer_callback_query(
        call.id,
        "👑 Admin Bypass ON" if is_admin_bypass_enabled() else "👑 Admin Bypass OFF"
    )
    refresh_force_join_panel(call)


def handle_force_join_test(call):
    """Check that the bot can actually verify each configured channel."""
    bot.answer_callback_query(call.id, "🔍 চেক করা হচ্ছে...")
    channels = get_force_channels()
    if not channels:
        bot.send_message(call.message.chat.id, "📌 কোনো channel যোগ করা হয়নি।",
                         parse_mode='HTML')
        return

    bot_id = get_bot_id()
    lines = []
    for channel in channels:
        target = channel.get('chat_id') or channel.get('chat_ref')
        try:
            member = bot.get_chat_member(target, bot_id)
            if getattr(member, 'status', '') in ADMIN_STATUSES:
                lines.append(f"✅ {channel['button_name']} — ঠিক আছে")
            else:
                lines.append(f"❌ {channel['button_name']} — বট Admin নয়")
        except Exception as e:
            lines.append(f"❌ {channel['button_name']} — {e}")

    bot.send_message(
        call.message.chat.id,
        render_body_text(
            "🔍 Force Join Test\n"
            "━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines) +
            "\n\n💡 ❌ থাকলে বটকে ওই channel-এ Admin বানান।"
        ),
        parse_mode='HTML'
    )


def handle_force_join_add(call):
    """Ask the admin for the new channel."""
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            "➕ নতুন Force Join Channel\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 এই ফরম্যাটে পাঠান:\n"
            "Join Channel / https://t.me/example\n\n"
            f"{private_channel_emoji_tag()} Private channel হলে শেষে channel ID দিন:\n"
            "Join Channel / https://t.me/+abc123 / -1001234567890\n\n"
            "🤖 বটকে আগে ওই channel-এ Admin বানাতে হবে।\n"
            "💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_force_join_add)


def process_force_join_add(message):
    """Save a new force join channel."""
    if not is_otp_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return

    parsed, error = parse_force_join_input(text)
    if error:
        bot.reply_to(message, f"❌ {error}", parse_mode='HTML')
        return

    resolved, error = resolve_force_channel(parsed["chat_ref"], parsed["chat_id"])
    if error:
        bot.reply_to(message, f"❌ {error}", parse_mode='HTML')
        return

    channel_id, error = add_force_channel(
        parsed["button_name"], parsed["channel_url"],
        resolved["chat_ref"] or parsed["chat_ref"], resolved["chat_id"]
    )
    if error:
        bot.reply_to(message, f"❌ {error}", parse_mode='HTML')
        return

    clear_force_join_cache()
    bot.reply_to(
        message,
        render_body_text(
            f"✅ Channel যোগ করা হয়েছে!\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔘 Button: {parsed['button_name']}\n"
            f"📢 Channel: {resolved['title'] or parsed['channel_url']}\n"
            f"🆔 ID: {resolved['chat_id']}\n"
            f"🔗 URL: {parsed['channel_url']}\n\n"
            f"🔒 এখন থেকে সব ইউজারকে এই channel-এ জয়েন করতে হবে।"
        ),
        reply_markup=build_force_join_admin_markup(),
        parse_mode='HTML'
    )


def handle_force_join_edit(call, channel_id):
    """Ask the admin for the replacement channel details."""
    channel = get_force_channel(channel_id)
    if not channel:
        bot.answer_callback_query(call.id, "❌ Channel পাওয়া যায়নি!", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            f"✏️ Channel Edit\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔘 বর্তমান: {channel['button_name']} / {channel['channel_url']}\n\n"
            f"📌 নতুন তথ্য এই ফরম্যাটে পাঠান:\n"
            f"Join Channel / https://t.me/example\n\n"
            f"💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_force_join_edit, channel_id)


def process_force_join_edit(message, channel_id):
    """Persist the edited channel."""
    if not is_otp_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return

    parsed, error = parse_force_join_input(text)
    if error:
        bot.reply_to(message, f"❌ {error}", parse_mode='HTML')
        return

    resolved, error = resolve_force_channel(parsed["chat_ref"], parsed["chat_id"])
    if error:
        bot.reply_to(message, f"❌ {error}", parse_mode='HTML')
        return

    if not update_force_channel(
        channel_id, parsed["button_name"], parsed["channel_url"],
        resolved["chat_ref"] or parsed["chat_ref"], resolved["chat_id"]
    ):
        bot.reply_to(message, "❌ আপডেট করা যায়নি!", parse_mode='HTML')
        return

    clear_force_join_cache()
    bot.reply_to(
        message,
        render_body_text(
            f"✅ Channel আপডেট হয়েছে!\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔘 Button: {parsed['button_name']}\n"
            f"🔗 URL: {parsed['channel_url']}"
        ),
        reply_markup=build_force_join_admin_markup(),
        parse_mode='HTML'
    )


def handle_force_join_delete(call, channel_id):
    """Delete a force join channel."""
    if not delete_force_channel(channel_id):
        bot.answer_callback_query(call.id, "❌ Channel পাওয়া যায়নি!", show_alert=True)
        return
    clear_force_join_cache()
    bot.answer_callback_query(call.id, "🗑️ Channel ডিলিট হয়েছে!")
    refresh_force_join_panel(call)


def handle_force_join_verify(call):
    """Re-check membership when the user presses Verify."""
    user_id = call.from_user.id
    clear_force_join_cache(user_id)
    missing = get_missing_force_channels(user_id, use_cache=False)

    if missing:
        bot.answer_callback_query(
            call.id,
            f"❌ আরও {len(missing)}টি channel-এ join করা বাকি!",
            show_alert=True
        )
        try:
            bot.edit_message_text(
                render_body_text(build_force_join_text(missing, call.from_user.first_name)),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=build_force_join_markup(missing),
                parse_mode='HTML'
            )
        except Exception:
            pass
        return

    bot.answer_callback_query(call.id, "✅ ভেরিফাই সফল!")
    try:
        bot.edit_message_text(
            render_body_text(
                f"{bot_emoji_tag()} ভেরিফিকেশন সফল\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                f"আপনার বট অ্যাক্সেস আনলক হয়েছে। {green_on_emoji_tag()}"
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
    except Exception:
        pass
    try:
        # Reuse the normal /start flow so the user lands on the main menu.
        call.message.from_user = call.from_user
        _logic_send_welcome(call.message)
    except Exception as e:
        logger.warning(f"Could not show menu after verify: {e}")
        bot.send_message(call.message.chat.id, "👇 শুরু করতে /start চাপুন।",
                         parse_mode='HTML')


# ==========================================
# 🔗 ALL LINK SETUP - ADMIN PANEL
# ==========================================
def build_link_setup_markup():
    """Buttons for every configurable link plus the USDT rate."""
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, label in LINK_FIELDS:
        markup.add(
            types.InlineKeyboardButton(
                strip_normal_emojis(label),
                callback_data=f'link_set_{key}',
                icon_custom_emoji_id=EMOJI_PIN,
                style="primary"  # 🔵 নীল
            )
        )
    markup.add(
        types.InlineKeyboardButton(
            "💱 USDT → BDT Rate",
            callback_data='link_rate',
            style="success"  # 🟢 সবুজ
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Back",
            callback_data='back_admin_panel',
            style="danger"  # 🔴 লাল
        )
    )
    return markup


def build_link_setup_text():
    """Show the currently saved links and rate."""
    text = (
        "🔗 All Link Setup\n"
        "━━━━━━━━━━━━━━━━━\n\n"
    )
    for key, label in LINK_FIELDS:
        if key == "support_link":
            label = f"{support_link_emoji_tag()} Support Link"
        text += f"{label}\n   🔗 {get_link(key)}\n\n"
    text += (
        f"💱 Conversion Rate\n"
        f"   1 USDT = {get_usdt_rate():.2f} BDT\n\n"
        f"📌 পরিবর্তন করতে নিচের বাটনে ক্লিক করুন।"
    )
    return text

#
@bot.message_handler(func=lambda message: message.text in [
    "Admin Link",
    "Support Link",
    "Channel Link",
    "Update Channel Link",
    "Owner Link",
    "Group Link",
    "USDT → BDT Rate",
    "Back"
])
def handle_link_setup_reply_buttons(message):
    """Handle all link setup reply keyboard buttons"""
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    # লিংক ম্যাপিং
    link_map = {
        "Admin Link": "admin_link",
        "Support Link": "support_link",
        "Channel Link": "channel_link",
        "Update Channel Link": "update_channel_link",
        "Owner Link": "owner_link",
        "Group Link": "group_link",
    }
    
    if text == "USDT → BDT Rate":
        prompt = bot.send_message(
            message.chat.id,
            render_body_text(
                f"💱 USDT → BDT Rate\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"📌 বর্তমান রেট: 1 USDT = {get_usdt_rate():.2f} BDT\n\n"
                f"💡 নতুন রেট শুধু সংখ্যায় লিখুন (উদাহরণ: 125)\n"
                f"💡 বাতিল করতে /cancel লিখুন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(prompt, process_rate_set)
        
    elif text == "Back":
        handle_otp_admin_panel(message)
        
    elif text in link_map:
        key = link_map[text]
        label = dict(LINK_FIELDS).get(key, text)
        prompt = bot.send_message(
            message.chat.id,
            render_body_text(
                f"{label}\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"🔗 বর্তমান: {get_link(key)}\n\n"
                f"📌 নতুন link পাঠান (https://t.me/example অথবা @username)\n"
                f"💡 বাতিল করতে /cancel লিখুন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(prompt, process_link_set, key)
#
def handle_link_setup_panel(message):
    """Show the All Link Setup admin section with reply keyboard."""
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    # 🔥 রিপ্লাই কীবোর্ড ব্যবহার করুন
    markup = create_link_setup_reply_keyboard()
    
    bot.reply_to(
        message,
        render_body_text(build_link_setup_text()),
        reply_markup=markup,
        parse_mode='HTML'
    )


def refresh_link_setup_panel(chat_id, message_id=None):
    """Redraw the link panel, either in place or as a new message."""
    text = render_body_text(build_link_setup_text())
    markup = build_link_setup_markup()
    if message_id:
        bot.edit_message_text(text, chat_id, message_id,
                              reply_markup=markup, parse_mode='HTML')
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='HTML')


def handle_link_set_request(call, key):
    """Ask the admin for a new link value."""
    label = dict(LINK_FIELDS).get(key, key)
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            f"{label}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 বর্তমান: {get_link(key)}\n\n"
            f"📌 নতুন link পাঠান (https://t.me/example অথবা @username)\n"
            f"💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_link_set, key)


def process_link_set(message, key):
    """Save the new link value."""
    if not is_otp_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return

    value = normalize_link(text)
    if not set_link(key, value):
        bot.reply_to(
            message,
            "❌ লিংক সঠিক নয়! উদাহরণ: https://t.me/example",
            parse_mode='HTML'
        )
        return

    label = dict(LINK_FIELDS).get(key, key)
    bot.reply_to(
        message,
        render_body_text(
            f"✅ {label} আপডেট হয়েছে!\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 নতুন link: {value}"
        ),
        reply_markup=build_link_setup_markup(),
        parse_mode='HTML'
    )


def handle_rate_set_request(call):
    """Ask the admin for a new USDT rate."""
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            f"💱 USDT → BDT Rate\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 বর্তমান রেট: 1 USDT = {get_usdt_rate():.2f} BDT\n\n"
            f"💡 নতুন রেট শুধু সংখ্যায় লিখুন (উদাহরণ: 125)\n"
            f"💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_rate_set)


def process_rate_set(message):
    """Save the new USDT rate."""
    if not is_otp_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return

    ok, result = set_usdt_rate(text)
    if not ok:
        bot.reply_to(message, f"❌ {result}", parse_mode='HTML')
        return

    bot.reply_to(
        message,
        render_body_text(
            f"✅ রেট আপডেট হয়েছে!\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"💱 1 USDT = {float(result):.2f} BDT\n"
            f"📌 নতুন রেট পরবর্তী deposit থেকে প্রযোজ্য হবে।"
        ),
        reply_markup=build_link_setup_markup(),
        parse_mode='HTML'
    )


# ==========================================
# 📢 BROADCAST SYSTEM
# ==========================================
BROADCAST_SLEEP_SECONDS = 0.05
_broadcast_running = threading.Event()


def get_broadcast_targets():
    """Every known active user, banned users excluded."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT user_id FROM active_users")
        users = [row[0] for row in c.fetchall()]
        conn.close()
    except Exception as e:
        logger.error(f"Error loading broadcast targets: {e}")
        users = list(active_users)

    banned = set(banned_users)
    return [uid for uid in dict.fromkeys(users) if uid not in banned]


def build_broadcast_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "👤 Single User",
            callback_data='bc_single',
            style="primary"  # 🔵 নীল
        ),
        types.InlineKeyboardButton(
            "📢 All Users",
            callback_data='bc_all',
            style="success"  # 🟢 সবুজ
        ),
        types.InlineKeyboardButton(
            "🔙 Back",
            callback_data='back_admin_panel',
            style="danger"  # 🔴 লাল
        )
    )
    return markup

#
@bot.message_handler(func=lambda message: message.text in [
    "Single User",
    "All Users",
    "Back"
])
def handle_broadcast_reply_buttons(message):
    """Handle broadcast reply keyboard buttons"""
    user_id = message.from_user.id
    text = message.text
    
    if not is_otp_admin(user_id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    if text == "Single User":
        prompt = bot.send_message(
            message.chat.id,
            render_body_text(
                "👤 Single User Broadcast\n"
                "━━━━━━━━━━━━━━━━━\n\n"
                "📌 যাকে পাঠাতে চান তার User ID লিখুন।\n"
                "💡 বাতিল করতে /cancel লিখুন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(prompt, process_broadcast_single_target)
        
    elif text == "All Users":
        if _broadcast_running.is_set():
            bot.reply_to(message, "⏳ একটি broadcast এখনো চলছে!", parse_mode='HTML')
            return
        
        prompt = bot.send_message(
            message.chat.id,
            render_body_text(
                f"📢 All User Broadcast\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👥 প্রাপক: {len(get_broadcast_targets())} জন\n\n"
                f"✍️ যে মেসেজ পাঠাতে চান সেটি এখন পাঠান।\n"
                f"💡 বাতিল করতে /cancel লিখুন।"
            ),
            parse_mode='HTML'
        )
        bot.register_next_step_handler(prompt, process_broadcast_all_message)
        
    elif text == "Back":
        bot.clear_step_handler_by_chat_id(message.chat.id)
        handle_otp_admin_panel(message)
# ==========================================
# ✅ ALL LINK SETUP REPLY KEYBOARD (Premium Emoji + Style)
# ==========================================
def create_link_setup_reply_keyboard():
    """Create all link setup reply keyboard with premium emojis and colors"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # লিংক বাটনগুলো - ২টি করে লাইনে
    link_buttons = [
        ("Admin Link", "admin_link", "primary"),
        ("Support Link", "support_link", "primary"),
        ("Channel Link", "channel_link", "primary"),
        ("Update Channel Link", "update_channel_link", "primary"),
        ("Owner Link", "owner_link", "primary"),
        ("Group Link", "group_link", "primary"),
    ]
    
    # ২টি করে লাইনে যোগ করুন
    for i in range(0, len(link_buttons), 2):
        if i + 1 < len(link_buttons):
            markup.add(
                make_keyboard_button(
                    link_buttons[i][0], EMOJI_PIN, link_buttons[i][2],
                    use_override=False
                ),
                make_keyboard_button(
                    link_buttons[i+1][0], EMOJI_PIN, link_buttons[i+1][2],
                    use_override=False
                )
            )
        else:
            markup.add(
                make_keyboard_button(
                    link_buttons[i][0], EMOJI_PIN, link_buttons[i][2],
                    use_override=False
                )
            )
    
    # সারি: USDT Rate (একা)
    markup.add(
        make_keyboard_button("USDT → BDT Rate", EMOJI_DOLLAR, "success")
    )
    
    # সারি: ব্যাক (একা)
    markup.add(
        make_keyboard_button("Back", EMOJI_BACK, "primary")
    )
    
    return markup
#
def handle_broadcast_panel(message):
    """Show the Broadcast admin section with reply keyboard."""
    if not is_otp_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Unauthorized!", parse_mode='HTML')
        return
    
    # 🔥 রিপ্লাই কীবোর্ড ব্যবহার করুন
    markup = create_broadcast_reply_keyboard()
    
    bot.reply_to(
        message,
        render_body_text(
            f"📢 Broadcast\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👥 মোট active user: {len(get_broadcast_targets())}\n\n"
            f"📌 কোথায় পাঠাতে চান সিলেক্ট করুন:"
        ),
        reply_markup=markup,
        parse_mode='HTML'
    )


def handle_broadcast_single_request(call):
    """Ask for the target user ID."""
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            "👤 Single User Broadcast\n"
            "━━━━━━━━━━━━━━━━━\n\n"
            "📌 যাকে পাঠাতে চান তার User ID লিখুন।\n"
            "💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_broadcast_single_target)


def process_broadcast_single_target(message):
    """Validate the target user ID and ask for the message."""
    if not is_otp_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return
    if text == "Back":
        bot.clear_step_handler_by_chat_id(message.chat.id)
        handle_broadcast_panel(message)
        return

    if not re.fullmatch(r'-?\d{1,15}', text):
        bot.reply_to(message, "❌ সঠিক numeric User ID লিখুন!", parse_mode='HTML')
        return

    target_id = int(text)
    prompt = bot.reply_to(
        message,
        render_body_text(
            f"✍️ এখন মেসেজটি পাঠান (text, photo, video যেকোনো কিছু)।\n"
            f"👤 Target: {target_id}\n"
            f"💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_broadcast_single_message, target_id)


def process_broadcast_single_message(message, target_id):
    """Deliver the message to one user."""
    if not is_otp_admin(message.from_user.id):
        return
    incoming_text = (message.text or "").strip()
    if incoming_text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return
    if incoming_text == "Back":
        bot.clear_step_handler_by_chat_id(message.chat.id)
        handle_broadcast_panel(message)
        return

    ok, error = deliver_broadcast_message(target_id, message)
    if ok:
        bot.reply_to(
            message,
            render_body_text(
                f"✅ মেসেজ পাঠানো হয়েছে!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 User ID: {target_id}"
            ),
            parse_mode='HTML'
        )
    else:
        bot.reply_to(
            message,
            render_body_text(
                f"❌ মেসেজ পাঠানো যায়নি!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"👤 User ID: {target_id}\n"
                f"📌 কারণ: {error}"
            ),
            parse_mode='HTML'
        )


def handle_broadcast_all_request(call):
    """Ask for the message that goes to every user."""
    if _broadcast_running.is_set():
        bot.answer_callback_query(
            call.id, "⏳ একটি broadcast এখনো চলছে!", show_alert=True
        )
        return
    bot.answer_callback_query(call.id)
    prompt = bot.send_message(
        call.message.chat.id,
        render_body_text(
            f"📢 All User Broadcast\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👥 প্রাপক: {len(get_broadcast_targets())} জন\n\n"
            f"✍️ যে মেসেজ পাঠাতে চান সেটি এখন পাঠান।\n"
            f"💡 বাতিল করতে /cancel লিখুন।"
        ),
        parse_mode='HTML'
    )
    bot.register_next_step_handler(prompt, process_broadcast_all_message)


def process_broadcast_all_message(message):
    """Start the background broadcast."""
    if not is_otp_admin(message.from_user.id):
        return
    incoming_text = (message.text or "").strip()
    if incoming_text.lower() in ('/cancel', 'cancel'):
        bot.reply_to(message, "❌ বাতিল করা হয়েছে।", parse_mode='HTML')
        return
    if incoming_text == "Back":
        bot.clear_step_handler_by_chat_id(message.chat.id)
        handle_broadcast_panel(message)
        return
    if _broadcast_running.is_set():
        bot.reply_to(message, "⏳ একটি broadcast এখনো চলছে!", parse_mode='HTML')
        return

    targets = get_broadcast_targets()
    if not targets:
        bot.reply_to(message, "📌 কোনো active user নেই!", parse_mode='HTML')
        return

    status = bot.reply_to(
        message,
        render_body_text(
            f"📢 Broadcast শুরু হয়েছে\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"👥 মোট: {len(targets)}\n"
            f"⏳ অপেক্ষা করুন..."
        ),
        parse_mode='HTML'
    )

    thread = threading.Thread(
        target=run_broadcast,
        args=(message, targets, message.chat.id,
              getattr(status, 'message_id', None)),
        daemon=True
    )
    thread.start()


def deliver_broadcast_message(target_id, message):
    """Copy the admin message to one chat. Returns (ok, error_text)."""
    try:
        bot.copy_message(target_id, message.chat.id, message.message_id)
        return True, None
    except telebot.apihelper.ApiTelegramException as e:
        retry_after = getattr(e, 'result_json', {}) or {}
        retry_after = (retry_after.get('parameters') or {}).get('retry_after')
        if retry_after:
            time.sleep(min(int(retry_after) + 1, 60))
            try:
                bot.copy_message(target_id, message.chat.id, message.message_id)
                return True, None
            except Exception as retry_error:
                return False, str(retry_error)
        return False, str(e)
    except Exception as e:
        return False, str(e)


def run_broadcast(message, targets, status_chat_id, status_message_id):
    """Send a broadcast to every target without ever stopping on errors."""
    _broadcast_running.set()
    sent = 0
    failed = 0
    try:
        for index, user_id in enumerate(targets, 1):
            ok, error = deliver_broadcast_message(user_id, message)
            if ok:
                sent += 1
            else:
                failed += 1
                logger.info(f"Broadcast skipped {user_id}: {error}")

            if status_message_id and index % 50 == 0:
                try:
                    bot.edit_message_text(
                        render_body_text(
                            f"📢 Broadcast চলছে\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"👥 মোট: {len(targets)}\n"
                            f"✅ পাঠানো হয়েছে: {sent}\n"
                            f"❌ ব্যর্থ: {failed}"
                        ),
                        status_chat_id, status_message_id,
                        parse_mode='HTML'
                    )
                except Exception:
                    pass

            time.sleep(BROADCAST_SLEEP_SECONDS)
    except Exception as e:
        logger.error(f"Broadcast crashed: {e}", exc_info=True)
    finally:
        _broadcast_running.clear()

    summary = render_body_text(
        f"✅ Broadcast সম্পন্ন\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👥 মোট: {len(targets)}\n"
        f"✅ সফল: {sent}\n"
        f"❌ ব্যর্থ: {failed}"
    )
    try:
        if status_message_id:
            bot.edit_message_text(summary, status_chat_id, status_message_id,
                                  parse_mode='HTML')
        else:
            bot.send_message(status_chat_id, summary, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Failed to report broadcast summary: {e}")


# ==================== CLEANUP ====================

def _startup_reply_message(user_id):
    """Create a minimal message context for startup notifications."""
    return SimpleNamespace(
        chat=SimpleNamespace(id=user_id),
        message_id=None,
        from_user=SimpleNamespace(id=user_id, first_name="Startup Recovery")
    )

def restore_persisted_running_files():
    """Restart only files that were running before the bot went offline."""
    try:
        # Expired files are stopped first, so they are never resurrected.
        check_and_stop_expired_files()
    except Exception as e:
        logger.error(f"Could not check expired files before recovery: {e}", exc_info=True)

    try:
        with DB_LOCK:
            conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            rows = conn.execute(
                """SELECT user_id, file_name, file_type
                   FROM user_files WHERE is_stopped = 0
                   ORDER BY upload_time ASC"""
            ).fetchall()
            conn.close()
    except Exception as e:
        logger.error(f"Could not load files for startup recovery: {e}", exc_info=True)
        return

    restored = 0
    skipped = 0
    for user_id, file_name, file_type in rows:
        try:
            normalized_user_id = int(user_id)
            original_name = str(file_name or "")
            safe_name = os.path.basename(original_name.replace("\\", "/"))
            if not safe_name or safe_name != original_name:
                skipped += 1
                logger.error(
                    "Startup recovery skipped unsafe filename for user %s: %r",
                    user_id,
                    file_name,
                )
                continue
            user_folder = get_user_folder(normalized_user_id)
            file_path = os.path.join(user_folder, safe_name)
        except Exception:
            skipped += 1
            logger.exception(
                "Startup recovery could not prepare file record for "
                "user %r, file %r; continuing.",
                user_id,
                file_name,
            )
            continue
        if not os.path.isfile(file_path):
            # Preserve the database record; an admin can inspect/re-upload it
            # instead of an automatic recovery deleting user data.
            skipped += 1
            logger.error(
                f"Startup recovery skipped missing file: "
                f"user={normalized_user_id}, file={safe_name}, path={file_path}"
            )
            for admin_id in get_unique_admin_ids():
                try:
                    bot.send_message(
                        admin_id,
                        render_body_text(
                            "⚠️ *STARTUP RECOVERY: FILE NOT FOUND*\n"
                            "━━━━━━━━━━━━━━━━━\n\n"
                            f"🆔 User ID: `{normalized_user_id}`\n"
                            f"📄 File: `{safe_name}`\n"
                            "ℹ️ Database record রাখা হয়েছে; কোনো data delete করা হয়নি।"
                        ),
                        parse_mode='HTML'
                    )
                except Exception:
                    pass
            continue

        script_type = str(file_type or "").lower()
        if script_type not in ("py", "js"):
            script_type = os.path.splitext(safe_name)[1].lower().lstrip(".")
        if script_type not in ("py", "js"):
            skipped += 1
            logger.warning(
                f"Startup recovery skipped unsupported file type: "
                f"user={normalized_user_id}, file={safe_name}, type={file_type}"
            )
            continue

        script_key = f"{normalized_user_id}_{safe_name}"
        if script_key in bot_scripts:
            continue

        startup_message = _startup_reply_message(user_id)
        runner = run_script if script_type == "py" else run_js_script
        Thread(
            target=runner,
            args=(
                file_path,
                normalized_user_id,
                user_folder,
                safe_name,
                startup_message,
                1,
                "auto",
            ),
            daemon=True,
            name=f"startup-recovery-{user_id}-{file_name}",
        ).start()
        restored += 1
        logger.info(
            f"Startup recovery scheduled {script_type.upper()} file "
            f"'{safe_name}' for user {normalized_user_id}"
        )

    logger.info(
        f"Startup recovery complete: {restored} previously-running files "
        f"scheduled, {skipped} skipped. Manually stopped files were not started."
    )

def cleanup():
    logger.warning("Shutdown. Cleaning up processes...")
    stop_google_sheets_sync()
    script_keys_to_stop = list(bot_scripts.keys()) 
    if not script_keys_to_stop: logger.info("No scripts running. Exiting."); return
    logger.info(f"Stopping {len(script_keys_to_stop)} scripts...")
    for key in script_keys_to_stop:
        if key in bot_scripts: logger.info(f"Stopping: {key}"); kill_process_tree(bot_scripts[key])
        else: logger.info(f"Script {key} already removed.")
    logger.warning("Cleanup finished.")
atexit.register(cleanup)
# ==========================================

# ==================== MAIN EXECUTION ====================

def _local_database_is_ready():
    if not LOCAL_DATABASE_EXISTED_AT_START or not os.path.isfile(DATABASE_PATH):
        return False
    try:
        connection = sqlite3.connect(
            DATABASE_PATH, check_same_thread=False, timeout=10
        )
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            return {"active_users", "user_files", "settings"}.issubset(tables)
        finally:
            connection.close()
    except sqlite3.Error as exc:
        logger.error("Persistent SQLite cache is not usable: %s", exc)
        return False


if __name__ == '__main__':
    logger.info("="*40)
    logger.info("🤖 Bot Starting Up...")
    logger.info(f"🐍 Python: {sys.version.split()[0]}")
    logger.info(f"🔧 Base Dir: {BASE_DIR}")
    logger.info(f"📁 Upload Dir: {UPLOAD_BOTS_DIR}")
    logger.info("📊 Durable local database: %s", DATABASE_PATH)
    logger.info("📄 Google Sheets/Drive backup configured: %s", _google_sheets_configured())
    logger.info(
        "Google Drive destination: %s",
        "configured shared folder" if GOOGLE_DRIVE_FOLDER_ID
        else "service-account Drive root",
    )
    logger.info(f"🔑 Owner ID: {OWNER_ID}")
    logger.info(f"🛡️ Admins: {admin_ids}")
    logger.info(f"👑 OTP Admin List: {admin_list}")
    logger.info("="*40)
    
    init_db()
    keep_alive()

    local_database_ready = _local_database_is_ready()
    force_sheet_restore = (
        os.environ.get("RESTORE_GOOGLE_SHEETS_ON_START", "0")
        .strip()
        .lower()
        in {"1", "true", "yes", "on"}
        and _google_sheets_configured()
    )
    if force_sheet_restore and local_database_ready:
        logger.warning(
            "RESTORE_GOOGLE_SHEETS_ON_START is enabled; restoring the "
            "configured Google Sheet over the local cache."
        )

    if local_database_ready and not force_sheet_restore:
        # Prefer the mounted local database when available. This lets the bot
        # recover from brief Google outages without replacing good local data
        # with a partial/empty spreadsheet snapshot.
        google_sheet_data_loaded = True
        load_data()
        logger.info("Loaded existing persistent SQLite data.")
    else:
        if not _google_sheets_configured():
            if local_database_ready:
                logger.warning(
                    "Google Sheets restore was requested but Sheets is not "
                    "configured; using the existing local database."
                )
                google_sheet_data_loaded = True
                load_data()
            else:
                raise RuntimeError(
                    "No existing local database and Google backup is not "
                    "configured. Set GOOGLE_SHEET_ID and "
                    "GOOGLE_SERVICE_ACCOUNT_JSON before starting a fresh "
                    "instance."
                )
        else:
            while not load_google_sheet_data():
                if google_sheet_data_loaded:
                    logger.warning(
                        "Google data was restored locally; its write-back "
                        "failed. Starting with the restored data and retrying "
                        "sync in background."
                    )
                    break
                logger.critical(
                    "Google data could not be loaded. Keeping polling stopped "
                    "to protect existing records; retrying in 30 seconds."
                )
                time.sleep(30)
            load_data()

    restore_hosted_files_from_drive()
    restore_persisted_running_files()
    start_google_sheets_sync()
    start_auto_checker()
    
    logger.info("🚀 Starting polling...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout:
            logger.warning("Polling ReadTimeout. Restarting in 5s...")
            time.sleep(5)
        except requests.exceptions.ConnectionError as ce:
            logger.error(f"Polling ConnectionError: {ce}. Retrying in 15s...")
            time.sleep(15)
        except Exception as e:
            logger.critical(f"💥 Unrecoverable polling error: {e}", exc_info=True)
            logger.info("Restarting polling in 30s due to critical error...")
            time.sleep(30)
        finally:
            logger.warning("Polling attempt finished. Will restart if in loop.")
            time.sleep(1)