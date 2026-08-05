from aiogram import Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    from .auth import AuthMiddleware
    from .logging import LoggingMiddleware
    from .i18n import ConfigI18nMiddleware
    from src.bot.core.loader import i18n

    dp.update.outer_middleware(LoggingMiddleware())

    ConfigI18nMiddleware(i18n=i18n).setup(dp)

    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(CallbackAnswerMiddleware())
