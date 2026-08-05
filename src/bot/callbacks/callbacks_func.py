import configparser

from aiogram.utils.i18n import gettext as _
from loguru import logger
from src.config import CONFIG_FILE_PATH
from src.logging_setup import log_easy
from src.bot.utils import process


def set_language(code: str) -> bool:
    """Пишет язык в config.ini - оттуда его читают и бот, и GUI"""
    from src.bot.core.loader import i18n
    if code not in i18n.available_locales:
        return False

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH, encoding="utf-8")
    config.set("Settings", "language", code)
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
        config.write(config_file)
    return True


async def task_kill(task_name: str) -> str:
    """Terminate a process by image name - backs the inline 'Kill' button."""
    logger.info(f"Starting task_kill function for process: {task_name}")
    log_easy(f"Attempting to kill process: {task_name}")

    image_name = task_name if task_name.lower().endswith(".exe") else f"{task_name}.exe"

    try:
        result = await process.run_async(
            ["taskkill", "/F", "/IM", image_name],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            text = _("Process <b>{program}</b> has been killed").format(program=task_name)
            logger.info(text)
        else:
            text = _("Unable to kill process <b>{program}</b>. "
                     "It was not found or an error occurred").format(program=task_name)
            logger.warning(f"{text} | {result.stderr.strip()}")
        log_easy(text)
        return text

    except Exception as e:
        logger.error(f"task_kill error: {e}")
        log_easy("Error! Check full logs in logs/botLog")
        return _("Error: <b>{error}</b>").format(error=e)
