CHANNEL_ID = -1003389825855
SUBSCRIPTION_CHANNEL_ID = 5041499407
TARGET_CHANNEL_ID = -1002524312410

import re  
import logging
import os

logger = logging.getLogger(__name__)
banned_users = set()  
banned_users_file = 'База_Бота/banned_users.txt'
private_channel_ids = set()  
API_ID = 21826549
API_HASH = 'c1a19f792cfd9e397200d16c7e448160'
script_dir = os.path.dirname(os.path.abspath(__file__))
session_dir = os.path.join(script_dir, 'Session')
CHANNELS = {
    -1003389825855: "https://t.me/Legion_sweeta",
}

private_channel_ids = {2577459026, 2391815028}

# ниже цены 
VIP_PRICE = {
    "USDT": 10
}

CURRENCY_PRICES = {
    "1_day": {"USDT": 0.5},
    "2_days": {"USDT": 1.5},
    "5_days": {"USDT": 2.5},
    "30_days": {"USDT": 15.0},
    "1_year": {"USDT": 50.0},
    "forever": {"USDT": 100},
}

PRICES = {
        '1_day': 5,
        '2_days': 9,
        '5_days': 20,
        '30_days': 50,
        '1_year': 200,
        'forever': 500
    }

SESSION_DIR = 'Session'

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

storage = MemoryStorage()
bot_token = '8664908234:AAEpEKOwQFCKk_IF1V6tTOtPl8s0EQFqJ78'
bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
admin_chat_ids = [8592184380, 8777286812]
CRYPTO_PAY_TOKEN = '582351:AAgkOntVSrVHsDl2vGMmwWEBByDSXXZvWTH'

receivers = [
    'sms@telegram.org', 'dmca@telegram.org', 'abuse@telegram.org', 'sticker@telegram.org', 'support@telegram.org', 'support@telegram.org', 'dmca@telegram.org', 'security@telegram.org', 'sms@telegram.org', 'info@telegram.org', 'marta@telegram.org', 'spam@telegram.org', 'alex@telegram.org', 'abuse@telegram.org', 'pavel@telegram.org', 'durov@telegram.org', 'elies@telegram.org', 'ceo@telegram.org', 'mr@telegram.org', 'levlam@telegram.org', 'perekopsky@telegram.org', 'recover@telegram.org', 'germany@telegram.org', 'hyman@telegram.org', 'qa@telegram.org', 'Stickers@telegram.org', 'ir@telegram.org', 'vadim@telegram.org', 'shyam@telegram.org', 'stopca@telegram.org', '>support@telegram.org', 'ask@telegram.org', '125support@telegram.org', 'me@telegram.org', 'enquiries@telegram.org', 'api_support@telegram.org', 'marketing@telegram.org', 'ca@telegram.org', 'recovery@telegram.org', 'http@telegram.org', 'corp@telegram.org', 'corona@telegram.org', 'ton@telegram.org', 'sticker@telegram.org'
]

smtp_servers = {
    "gmail.com": ("smtp.gmail.com", 587),
    "yandex.ru": ("smtp.yandex.ru", 465),
    "mail.ru": ("smtp.mail.ru", 465),
    "rambler.ru": ("smtp.rambler.ru", 465),
    "yahoo.com": ("smtp.mail.yahoo.com", 465),
    "outlook.com": ("smtp.office365.com", 587),
    "icloud.com": ("smtp.mail.me.com", 587),
    "aol.com": ("smtp.aol.com", 587),
    "zoho.com": ("smtp.zoho.com", 587),
    "protonmail.com": ("smtp.protonmail.com", 587),
    "t-online.de": ("secure.emailsrvr.com", 587),
    "gmx.de": ("mail.gmx.com", 587),
    "hotmail.de": ("smtp.live.com", 587),
    "web.de": ("smtp.web.de", 587),
    "gmx.net": ("mail.gmx.net", 587),
    "posteo.de": ("posteo.de", 587),
    "mailbox.org": ("smtp.mailbox.org", 587),
    "1und1.de": ("smtp.1und1.de", 587),
    "strato.de": ("smtp.strato.de", 465),
    "fastmail.com": ("smtp.fastmail.com", 587),
    "tutanota.com": ("smtp.tutanota.de", 587),
    "runbox.com": ("smtp.runbox.com", 587),
    "hushmail.com": ("smtp.hushmail.com", 587),
    "countermail.com": ("smtp.countermail.com", 465),
    "lavabit.com": ("smtp.lavabit.com", 465),
    "cock.li": ("mail.cock.li", 587),
    "migadu.com": ("smtp.migadu.com", 587),
    "mailfence.com": ("smtp.mailfence.com", 587),
    "kolabnow.com": ("smtp.kolabnow.com", 587),
    "mailnesia.com": ("smtp.mailnesia.com", 587),
    "mailcatch.com": ("smtp.mailcatch.com", 587),
    "mintemail.com": ("smtp.mintemail.com", 587),
    "spamgourmet.com": ("smtp.spamgourmet.com", 587),
    "mytemp.email": ("smtp.mytemp.email", 587),
    "temp-mail.org": ("smtp.temp-mail.org", 587),
    "mailtemp.info": ("smtp.mailtemp.info", 587),
    "fakemail.net": ("smtp.fakemail.net", 587),
    "sharklasers.com": ("smtp.sharklasers.com", 587)
}

clients = [  
    {"name": "Public MacOs Beta", "api_id": 2834, "api_hash": "68875f756c9b437a8b916ca3de215815"},
    {"name": "@XP_Diablo_XP", "api_id": 21826549, "api_hash": "c1a19f792cfd9e397200d16c7e448160"}
]