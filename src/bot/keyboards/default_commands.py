from __future__ import annotations
from typing import TYPE_CHECKING
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from src.config import ADMIN_ID

if TYPE_CHECKING:
    from aiogram import Bot

admins_commands: dict[str, dict[str, str]] = {
    "en": {
        "lock": "Lock the computer",
        "logout": "Log out of the current user session",
        "cancel": "Cancel any scheduled actions (shutdown, reboot, hibernation)",
        "check": "Check the computer's status",
        "cpu": "Same as check, but concise",
        "task": "Check if a process is running or stop it",
        "screen": "Take a screenshot of the current screen",
        "webcam": "Capture an image using the webcam",
        "keyboard": "Show a keyboard",
        "wifi": "Display SSID and password of saved Wi-Fi networks",
        "ls": "Show the contents of the current directory",
    },
    "ru": {
        "lock": "Заблокировать компьютер",
        "logout": "Выход из текущей учетной записи",
        "cancel": "Отменить запланированные действия (выключение ПК, перезагрузка, гибернация)",
        "check": "Проверить состояние компьютера",
        "cpu": "Состояние ПК(кратко)",
        "task": "Проверить, запущен ли процесс, или остановить его",
        "screen": "Сделать снимок экрана",
        "webcam": "Заняться вебкамом",
        "keyboard": "Показать клавиатуру",
        "wifi": "Показать SSID и пароль сохраненных Wi-Fi сетей",
        "ls": "Показать содержимое текущей директории",
    }
}


async def set_default_commands(bot: Bot) -> None:
    await remove_default_commands(bot)

    for language_code in admins_commands:
        await bot.set_my_commands(
            [
                BotCommand(command=command, description=description)
                for command, description in admins_commands[language_code].items()
            ],
            scope=BotCommandScopeDefault(),
        )


async def remove_default_commands(bot: Bot) -> None:
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
