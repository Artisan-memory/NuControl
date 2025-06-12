import subprocess

from aiogram import Router
from loguru import logger
from src.logging_setup import log_easy

callbacks_router = Router()

async def task_kill(task_name: str) -> str:
    """Process stop function"""
    logger.info(f"Starting task_kill function for process: {task_name}")
    log_easy(f"Attempting to kill process: {task_name}")

    try:
        ret = subprocess.run(f"tskill {task_name}").returncode
        if ret == 0:
            text = f"Process <b>{task_name}</b> has been killed"
            logger.info(text)
            log_easy(text)
        else:
            text = f"Unable to kill process <b>{task_name}</b>. Process not found or an error occurred"
            logger.warning(text)
            log_easy(text)
        return text

    except Exception as e:
        text = f'Error: {str(e)}'
        logger.error(text)
        log_easy("Error! Check full logs in logs/botLog")
        return text
