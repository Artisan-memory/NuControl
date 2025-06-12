from aiogram import Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware

# from src.bot.core.loader import i18n as _i18n


def register_middlewares(dp: Dispatcher) -> None:
    from .auth import AuthMiddleware
#   from .i18n import ACLMiddleware
    from .logging import LoggingMiddleware  

    dp.update.outer_middleware(LoggingMiddleware())

    dp.message.middleware(AuthMiddleware())

    # ACLMiddleware(i18n=_i18n).setup(dp)

    dp.callback_query.middleware(CallbackAnswerMiddleware())
