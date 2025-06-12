import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from src.logging_setup import log_easy
from loguru import logger

router = Router(name="bot_messages")



class Form(StatesGroup):
    audio_file = State()


@router.message(Form.audio_file, F.content_type.in_({'audio', 'voice'}))
async def documents_handler(message: Message, state: FSMContext):
    logger.info("documents_handler: Received a message with audio or voice content.")

    if message.audio:
        await message.answer("Это аудио файл")
        logger.info("documents_handler: The message is an audio file.")
    elif message.voice:
        await message.answer("Это голосовое сообщение")
        logger.info("documents_handler: The message is a voice message.")
    else:
        await message.answer("Тип не был определён и не поддерживается")
        logger.warning("documents_handler: Unsupported content type.")
        return

    log_easy("/sound - kb - completed")
    await state.clear()
    logger.info("documents_handler: State cleared.")


@router.message(F.text)
async def menu_handler(message: Message, bot: Bot, state: FSMContext):
    msg = message.text.lower()
    logger.info(f"menu_handler: Received message: {msg}")

    if msg == "📸 скриншот":
        from src.bot.handlers.user_commands_func import screenshot
        log_easy("/screenshot - kb")

        image, path = await screenshot()
        logger.info("/screenshot: Screenshot taken.")

        await bot.send_document(chat_id=message.chat.id, document=image)
        os.remove(path)
        logger.info("/screenshot: Screenshot sent and file removed.")

    elif msg == "🤳 снимок вебки":
        from src.bot.handlers.user_commands_func import webcam

        log_easy("/webcam - kb")

        text, image, path = await webcam()
        logger.info("/webcam: Webcam photo taken.")

        if image and path is not None:
            await bot.send_document(chat_id=message.chat.id, document=image)
            os.remove(path)
            logger.info("/webcam: Webcam photo sent and file removed.")
        else:
            await bot.send_message(chat_id=message.chat.id, text=text)
            logger.warning("/webcam: Webcam photo not taken, no image found.")

    elif msg == "❌ отмена":
        from src.bot.handlers.user_commands_func import cancel

        log_easy("/cancel - kb")

        text = await cancel()
        await message.answer(text)
        logger.info("/cancel: Operation canceled.")
        log_easy("/cancel - kb - completed")

    elif msg == "🔒 заблокировать комп":
        from src.bot.handlers.user_commands_func import lock_screen

        log_easy("/lock - kb")

        text = await lock_screen()
        await message.answer(text)
        logger.info("/lock: Computer locked.")
        log_easy("/lock - kb - completed")

    elif msg == "🔊 воспроизвести звук":
        log_easy("/sound - kb")

        await message.answer("Отправьте аудио файл \n<b>(.wav, mp3, .oga, .ogg)</b>\n\n"
                             "гс принимается тоже!")
        await state.set_state(Form.audio_file)
        logger.info("/sound: Prompted user to send an audio file and set state to audio_file.")
