from __future__ import annotations
import asyncio
from datetime import datetime

from loguru import logger
from src.config import LOGS_FILE_PATH, ADMIN_ID
from src.bot.callbacks import get_callbacks_router
from src.bot.core.loader import bot, dp
from src.bot.handlers import get_handlers_router
from src.bot.keyboards.default_commands import remove_default_commands, set_default_commands
from src.bot.middlewares import register_middlewares
from src.bot.utils.timer import Timer
from src.bot.utils.startup_message import fetch_currency

# Preparation
timer = Timer()
stop_event = asyncio.Event()


async def handle_client(reader, writer):
    logger.debug("handle_client: client connected")

    data = await reader.read(1024)
    message = data.decode().strip()

    logger.debug(f"handle_client: received message -> {message}")

    if message == "stop":
        logger.info("handle_client: stop command received")
        writer.close()
        await writer.wait_closed()
        stop_event.set()
        await dp.stop_polling()
        logger.info("handle_client: stop_event set")


async def command_listener():
    logger.debug("command_listener: starting server")
    server = await asyncio.start_server(handle_client, '127.0.0.1', 9999)
    logger.info(f"command_listener: Listening on {server.sockets[0].getsockname()}")


async def on_startup() -> None:
    await timer.start()

    logger.info("on_startup: bot starting...")

    register_middlewares(dp)
    dp.include_routers(get_handlers_router(), get_callbacks_router())

    await set_default_commands(bot)
    bot_info = await bot.get_me()
    logger.info(f"Bot Info - Name: {bot_info.full_name}, Username: @{bot_info.username}, ID: {bot_info.id}")

    states: dict[bool | None, str] = {
        True: "Enabled",
        False: "Disabled",
        None: "Unknown (not a bot)"
    }

    logger.info(f"Modes - Groups: {states[bot_info.can_join_groups]}, "
                f"Privacy: {states[not bot_info.can_read_all_group_messages]}, "
                f"Inline: {states[bot_info.supports_inline_queries]}")

    logger.info("on_startup: Bot started")

    global bot_use_name
    bot_use_name = bot_info.username

    usd, eur = await fetch_currency()
    startup_message = f"""Добрый день! Время {datetime.now().strftime("%H:%M:%S")}\n\n💵Доллар: <b>{usd}</b>
💶Евро: <b>{eur}</b>"""

    await bot.send_message(chat_id=ADMIN_ID, text=startup_message)


async def on_shutdown():
    logger.info("on_shutdown: Shutting down bot...")
    await remove_default_commands(bot)
    await bot.session.close()
    logger.info("on_shutdown: Bot has stopped.")


async def main():
    logger.add(
        f"{LOGS_FILE_PATH}/botLog/telegram_bot.log",
        level="DEBUG",
        format="{time} | {level} | {message}",
        rotation="3 day",
        compression="zip",
        enqueue=True
    )

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.debug("main: Starting command_listener")
    asyncio.create_task(command_listener())

    try:
        logger.debug("main: Entering gather loop")
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            stop_event.wait()
        )
        logger.debug("main: gather finished")
    except Exception as e:
        logger.exception(f"main: Unexpected exception -> {e}")
    finally:
        logger.debug("main: calling on_shutdown() from finally")
        await on_shutdown()
        logger.info("main: Bot ended.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        exit(1)
    except KeyboardInterrupt:
        logger.warning("Bot interrupted by user.")
        exit(0)
