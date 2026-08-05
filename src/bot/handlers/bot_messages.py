import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from src.config import TMP_DIR
from src.logging_setup import log_command, log_result
from src.bot.utils.audio import play
from loguru import logger

router = Router(name="bot_messages")


class Form(StatesGroup):
    audio_file = State()


async def send_shots(message: Message, shots):
    """Скрины уходят реплаем на команду, по файлу на монитор"""
    for index, (image, path) in enumerate(shots, start=1):
        caption = _("Monitor {index} of {total}").format(index=index, total=len(shots)) \
            if len(shots) > 1 else None
        await message.reply_document(document=image, caption=caption)
        os.remove(path)


@router.message(Form.audio_file, F.content_type.in_({'audio', 'voice'}))
async def documents_handler(message: Message, bot: Bot, state: FSMContext):
    audio = message.audio or message.voice
    if audio is None:
        await message.answer(_("Unsupported content type"))
        logger.warning("documents_handler: Unsupported content type.")
        return

    await state.clear()

    os.makedirs(TMP_DIR, exist_ok=True)
    file = await bot.get_file(audio.file_id)
    # У голосовых нет имени файла, а расширение важно для декодера
    suffix = os.path.splitext(file.file_path)[1] or ".ogg"
    path = os.path.join(TMP_DIR, f"{audio.file_unique_id}{suffix}")

    try:
        await bot.download_file(file.file_path, destination=path)
        await message.reply(_("Playing it on the speakers..."))
        await play(path)
        log_result(_("Audio played"))
        logger.info(f"documents_handler: played {path}")
    except Exception as e:
        logger.error(f"documents_handler: playback failed -> {e}")
        await message.answer(_("Could not play it: <b>{error}</b>").format(error=e))
    finally:
        if os.path.exists(path):
            os.remove(path)


@router.message(F.text)
async def menu_handler(message: Message, state: FSMContext):
    msg = message.text.lower()
    logger.info(f"menu_handler: Received message: {msg}")

    if msg == _("📸 Screenshot").lower():
        from src.bot.handlers.user_commands_func import screenshot
        log_command("/screen")

        shots = await screenshot()
        if not shots:
            await message.answer(_("Could not take a screenshot."))
            logger.warning("/screenshot: screenshot failed.")
        else:
            await send_shots(message, shots)

    elif msg == _("🤳 Webcam").lower():
        from src.bot.handlers.user_commands_func import webcam
        log_command("/webcam")

        text, image, path = await webcam()
        if image and path is not None:
            await message.reply_document(document=image)
            os.remove(path)
        else:
            await message.answer(text)
            logger.warning("/webcam: Webcam photo not taken, no image found.")

    elif msg == _("❌ Cancel").lower():
        from src.bot.handlers.user_commands_func import cancel
        log_command("/cancel")

        await message.answer(await cancel())

    elif msg == _("🔒 Lock PC").lower():
        from src.bot.handlers.user_commands_func import lock_screen
        log_command("/lock")

        await message.answer(await lock_screen())

    elif msg == _("🔊 Play sound").lower():
        log_command("/sound")

        await message.answer(_("Send an audio file\n<b>(.wav, .mp3, .oga, .ogg)</b>\n\n"
                               "voice messages are accepted too!"))
        await state.set_state(Form.audio_file)
