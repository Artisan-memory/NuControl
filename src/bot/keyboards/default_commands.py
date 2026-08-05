from __future__ import annotations
from typing import TYPE_CHECKING
from aiogram.types import BotCommand, BotCommandScopeDefault

if TYPE_CHECKING:
    from aiogram import Bot

# Telegram stores one command list per language code plus one unlabelled
# fallback, so these cannot go through gettext: they are pushed once at startup,
# outside any update context, and all languages are registered at the same time
FALLBACK_LANGUAGE = "en"

admins_commands: dict[str, dict[str, str]] = {
    "en": {
        "help": "Help",
        "clipboard": "Clipboard",
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
        "ls": "Browse the current directory",
        "msg": "Show a message box on the PC screen",
        "lang": "Change the bot language",
    },
    "ru": {
        "help": "Помощь",
        "clipboard": "Буфер обмена",
        "lock": "Заблокировать компьютер",
        "logout": "Выход из текущей учетной записи",
        "cancel": "Отменить запланированные действия (выключение ПК, перезагрузка, гибернация)",
        "check": "Проверить состояние компьютера",
        "cpu": "Состояние ПК (кратко)",
        "task": "Проверить, запущен ли процесс, или остановить его",
        "screen": "Сделать снимок экрана",
        "webcam": "Снимок с веб-камеры",
        "keyboard": "Показать клавиатуру",
        "wifi": "Показать SSID и пароль сохраненных Wi-Fi сетей",
        "ls": "Проводник по текущей директории",
        "msg": "Показать сообщение на экране ПК",
        "lang": "Сменить язык бота",
    },
    "de": {
        "help": "Hilfe",
        "clipboard": "Zwischenablage",
        "lock": "Computer sperren",
        "logout": "Von der aktuellen Sitzung abmelden",
        "cancel": "Geplante Aktionen abbrechen (Herunterfahren, Neustart, Ruhezustand)",
        "check": "Status des Computers prüfen",
        "cpu": "Wie check, aber kurz",
        "task": "Prüfen, ob ein Prozess läuft, oder ihn beenden",
        "screen": "Bildschirmfoto aufnehmen",
        "webcam": "Bild mit der Webcam aufnehmen",
        "keyboard": "Tastatur anzeigen",
        "wifi": "SSID und Passwort gespeicherter WLANs anzeigen",
        "ls": "Aktuelles Verzeichnis durchsuchen",
        "msg": "Ein Meldungsfenster am PC anzeigen",
        "lang": "Bot-Sprache ändern",
    },
}


def _commands(language_code: str) -> list[BotCommand]:
    return [
        BotCommand(command=command, description=description)
        for command, description in admins_commands[language_code].items()
    ]


async def set_default_commands(bot: Bot) -> None:
    await remove_default_commands(bot)

    # Without language_code this is the list Telegram shows to every client whose
    # language we do not translate; the per-language calls override it
    await bot.set_my_commands(_commands(FALLBACK_LANGUAGE), scope=BotCommandScopeDefault())

    for language_code in admins_commands:
        await bot.set_my_commands(
            _commands(language_code),
            scope=BotCommandScopeDefault(),
            language_code=language_code,
        )


async def remove_default_commands(bot: Bot) -> None:
    for language_code in admins_commands:
        await bot.delete_my_commands(scope=BotCommandScopeDefault(), language_code=language_code)
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
