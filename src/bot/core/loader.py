import configparser
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n.core import I18n
from src.config import TOKEN




BOT_DIR = Path(__file__).absolute().parent.parent.parent
LOCALES_DIR = f"{BOT_DIR}/locales"
# I18N_DOMAIN = "messages"
# DEFAULT_LOCALE = "en"



bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

# i18n: I18n = I18n(path=LOCALES_DIR, default_locale=DEFAULT_LOCALE, domain=I18N_DOMAIN)

