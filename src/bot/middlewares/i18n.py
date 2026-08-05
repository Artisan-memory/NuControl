from __future__ import annotations
import configparser
from typing import Any

from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import I18nMiddleware

from src.config import CONFIG_FILE_PATH


def resolve_locale(i18n: I18n) -> str:
    """Language from config.ini, falling back to the default when it is unknown."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH, encoding="utf-8")
    locale = config.get("Settings", "language", fallback=i18n.default_locale)
    if locale not in i18n.available_locales:
        return i18n.default_locale
    return locale


class ConfigI18nMiddleware(I18nMiddleware):
    """Pick the interface language from config.ini, the same setting the GUI writes.

    Reading the file per update keeps the language in sync when it is changed in
    the GUI while the bot is running, without needing a restart.
    """

    async def get_locale(self, event: TelegramObject, data: dict[str, Any]) -> str:
        return resolve_locale(self.i18n)
