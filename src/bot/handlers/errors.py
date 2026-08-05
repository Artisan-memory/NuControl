import traceback
from datetime import datetime

from aiogram import Router
from aiogram.types import BufferedInputFile, ErrorEvent
from aiogram.utils.i18n import gettext as _
from loguru import logger

from src.config import ADMIN_ID
from src.logging_setup import log_result

errors_router = Router(name="errors")

CAPTION_LIMIT = 1024


@errors_router.errors()
async def on_error(event: ErrorEvent):
    """Ловит всё, что упало в хендлерах, и кидает трейсбек файлом в чат"""
    exception = event.exception
    logger.exception(f"on_error: {exception!r}")
    log_result(f"Ошибка: {type(exception).__name__}")

    if ADMIN_ID is None:
        return True

    text = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    stamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mmin-%Ssec")
    document = BufferedInputFile(text.encode("utf-8"), filename=f"traceback_{stamp}.txt")

    caption = _("💥 <b>{error}</b>\n<blockquote>{message}</blockquote>").format(
        error=type(exception).__name__, message=str(exception) or "-",
    )

    try:
        await event.bot.send_document(chat_id=ADMIN_ID, document=document,
                                      caption=caption[:CAPTION_LIMIT])
    except Exception as send_failure:
        logger.error(f"on_error: could not deliver the traceback -> {send_failure}")

    # True - апдейт разобран, aiogram не должен ронять поллинг дальше
    return True
