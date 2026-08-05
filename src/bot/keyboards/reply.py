from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.utils.i18n import gettext as _

keyboard_clear = ReplyKeyboardRemove()


def main_keyboard() -> ReplyKeyboardMarkup:
    """Built per request so the labels are translated for the current locale.
    The same msgids are matched in bot_messages.menu_handler."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("📸 Screenshot")), KeyboardButton(text=_("🤳 Webcam"))],
            [KeyboardButton(text=_("❌ Cancel"))],
            [KeyboardButton(text=_("🔒 Lock PC")), KeyboardButton(text=_("🔊 Play sound"))],
        ],
        resize_keyboard=True,
        selective=True,
    )
