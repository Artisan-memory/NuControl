from __future__ import annotations
import asyncio
import os
from datetime import datetime

from aiogram.utils.i18n import gettext as _
from loguru import logger
from src.config import LOGS_FILE_PATH, TMP_DIR, ADMIN_ID, APP_VERSION, CONTROL_HOST, CONTROL_PORT
from src.bot.callbacks import get_callbacks_router
from src.bot.core.loader import bot, dp, i18n
from src.bot.handlers import get_handlers_router
from src.bot.keyboards.default_commands import remove_default_commands, set_default_commands
from src.bot.middlewares import register_middlewares
from src.bot.middlewares.i18n import resolve_locale
from src.bot.utils.timer import Timer
from src.bot.utils.startup_message import fetch_currency
from src.bot.utils.version_check import check_for_update

# Preparation
timer = Timer()
stop_event = asyncio.Event()
os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(os.path.join(LOGS_FILE_PATH, "botLog"), exist_ok=True)


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
    try:
        server = await asyncio.start_server(handle_client, CONTROL_HOST, CONTROL_PORT)
    except OSError as e:
        logger.error(f"command_listener: cannot bind {CONTROL_HOST}:{CONTROL_PORT} ({e}); "
                     f"another bot instance is probably already running. "
                     f"Set a different control_port in config.ini to run both.")
        return
    logger.info(f"command_listener: Listening on {server.sockets[0].getsockname()}")
    async with server:
        await server.serve_forever()


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

    if ADMIN_ID is None:
        logger.warning("on_startup: admin_id is not set, skipping startup message")
        return

    # The startup message is built outside any update, so the locale the i18n
    # middleware would normally provide has to be set up by hand here
    with i18n.context(), i18n.use_locale(resolve_locale(i18n)):
        startup_message = _("NuControl {version} started at {time}").format(
            version=APP_VERSION, time=datetime.now().strftime('%H:%M:%S'),
        )

        try:
            newer = await check_for_update()
            if newer:
                startup_message += "\n\n" + _(
                    "🔔 Update available: <b>{latest}</b> (you have {current})"
                ).format(latest=newer, current=APP_VERSION)
        except Exception as e:
            logger.warning(f"on_startup: update check failed -> {e}")

        try:
            usd, eur = await fetch_currency()
            startup_message += "\n\n" + _("💵 USD: <b>{usd}</b>\n💶 EUR: <b>{eur}</b>").format(
                usd=usd, eur=eur,
            )
        except Exception as e:
            logger.warning(f"on_startup: could not fetch currency rates -> {e}")

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
