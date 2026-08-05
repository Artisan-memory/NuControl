import os
import asyncio
import html
import re
import shutil
import tempfile

from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.i18n import gettext as _
from loguru import logger

from src.logging_setup import log_command, log_result
from src.bot.handlers.bot_messages import send_shots
from src.bot.handlers.user_commands_func import human_size
from src.bot.utils import browser, process

commands_router = Router(name="user_commands")

LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Русский", "de": "🇩🇪 Deutsch"}
# Ботам Telegram отдаёт заливать не больше 50 МБ
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# Длинные имена рвут лимит сообщения в 4096 символов
NAME_LIMIT = 60


# In a future for friends list
async def get_user_info(message: Message) -> str:
    from src.config import ADMIN_ID
    text = ''
    if message.from_user.id != ADMIN_ID:
        text = f'| ID={message.from_user.id}'
        if message.from_user.username:
            text += f" - @{message.from_user.username}"
    return text


@commands_router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, command: CommandObject):
    # Ссылки из /ls приходят сюда: payload - токен пути
    target = browser.path_for(command.args) if command.args else None
    if target:
        await open_target(message, bot, target)
        return

    log_command("/start")
    await message.answer(
        _("Hi! I'm the <b>NuControl</b> bot") +
        "\n\nhttps://github.com/Artisan-memory/NuControl 🌈"
    )


async def open_target(message: Message, bot: Bot, target: str):
    """Папку открываем, файл отдаём"""
    if os.path.isdir(target):
        log_command("/ls", target)
        set_cd(target)
        text, keyboard = await render_listing(bot)
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
        return

    if not os.path.isfile(target):
        await message.answer(_("Specified file does not exist."))
        return

    log_command("/download", target)
    size = os.path.getsize(target)
    if size > MAX_UPLOAD_BYTES:
        await message.answer(_("<b>{name}</b> is too big to send ({size})").format(
            name=os.path.basename(target), size=human_size(size)))
        return

    await message.answer_document(FSInputFile(target),
                                  caption=f"<code>{html.escape(os.path.basename(target))}</code>")


@commands_router.message(Command("lang", "language"))
async def cmd_language(message: Message):
    log_command("/lang")

    buttons = [
        [InlineKeyboardButton(text=title, callback_data=f"lang_{code}")]
        for code, title in LANGUAGES.items()
    ]
    await message.answer(
        _("Choose the bot language:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@commands_router.message(Command("msg", "notify"))
async def cmd_message_on_screen(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import show_on_screen
    log_command("/msg", command.args)

    if not command.args:
        await message.answer(_("<i>No text provided</i>\n"
                               "<blockquote><b>Example:</b> /msg + text</blockquote>"))
        return

    await show_on_screen(command.args)
    await message.answer(_("Shown on the screen"))


@commands_router.message(Command("kb", "keyboard"))
async def cmd_keyboard(message: Message):
    from src.bot.keyboards.reply import main_keyboard
    log_command("/keyboard")

    await message.answer(_("Keyboard raised"), reply_markup=main_keyboard())


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    log_command("/help")

    text = _(
        "<b>Available commands:</b>\n\n"
        "<b>/shutdown</b> or <b>/s</b> — shut down the computer\n"
        "<b>/reboot</b> or <b>/r</b> — restart the computer\n"
        "<b>/hibernate</b> or <b>/h</b> — put the computer to sleep\n"
        "<b>/lock</b> or <b>/l</b> — lock the computer\n"
        "<b>/logout</b> — log out of the current session\n"
        "<b>/cancel</b> — cancel scheduled actions (shutdown, reboot, hibernate)\n"
        "<b>/check</b> — check the computer status\n"
        "<b>/cpu</b> — same as /check, but concise\n"
        "<b>/launch</b> <i>program</i> — launch a program (e.g. <code>/launch notepad</code>)\n"
        "<b>/link</b> <i>url</i> — open a link (e.g. <code>/link google.com</code>)\n"
        "<b>/task</b> <i>process</i> — check whether a process is running or stop it (e.g. <code>/task chrome</code>)\n"
        "<b>/screen</b> — take a screenshot\n"
        "<b>/keyboard</b> or <b>/kb</b> — show the keyboard\n"
        "<b>/webcam</b> or <b>/web</b> or <b>/photo</b> — capture a webcam image\n"
        "<b>/download</b> <i>path</i> — send a file from the computer (e.g. <code>/download C:/file.txt</code>)\n"
        "<b>/say</b> <i>text</i> — speak the text through the speakers (e.g. <code>/say Hello World!</code>)\n"
        "<b>/clipboard</b> [<i>text</i>] — show or set the clipboard contents\n"
        "<b>/wifi</b> — show SSID and password of saved Wi-Fi networks\n"
        "<b>/ls</b> — browse the current directory, tap a name to open or download it\n"
        "<b>/cd</b> <i>path</i> — change the current directory\n"
        "<b>/msg</b> <i>text</i> — show a message box on the PC screen\n"
        "<b>/lang</b> — change the bot language\n\n"
        "<b>Tip:</b> add a delay in minutes to shutdown/reboot/hibernate/lock, e.g. <i>/shutdown 2</i>."
    )
    await message.answer(text=text)


@commands_router.message(Command("lock", "l"))
async def cmd_lock(message: Message):
    from src.bot.handlers.user_commands_func import lock_screen
    log_command("/lock")

    text = await lock_screen()
    await message.answer(text)


@commands_router.message(Command("logout"))
async def cmd_logout(message: Message):
    from src.bot.handlers.user_commands_func import logout
    log_command("/logout")

    text = await logout()
    await message.answer(text)


@commands_router.message(Command("shutdown", "s"))
async def cmd_shutdown(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import shutdown
    log_command("/shutdown", command.args)

    text = await shutdown(args=command.args)
    await message.answer(text)


@commands_router.message(Command("reboot", "r"))
async def cmd_reboot(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import reboot
    log_command("/reboot", command.args)

    text = await reboot(args=command.args)
    await message.answer(text)


@commands_router.message(Command("hibernate", "h"))
async def cmd_hibernate(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import hibernate
    log_command("/hibernate", command.args)

    text = await hibernate(args=command.args)
    await message.answer(text)


@commands_router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    from src.bot.handlers.user_commands_func import cancel
    log_command("/cancel")

    text = await cancel()
    await message.answer(text)


CAPTION_LIMIT = 1024


@commands_router.message(Command("check"))
async def cmd_check(message: Message):
    from src.bot.handlers.user_commands_func import check_hardware
    log_command("/check")

    text, image_path = await check_hardware()
    if image_path is None:
        await message.answer(text=text)
        return

    card = FSInputFile(image_path)
    if len(text) <= CAPTION_LIMIT:
        await message.answer_photo(card, caption=text)
    else:
        # Too many drives to fit a caption; the report follows the card
        await message.answer_photo(card)
        await message.answer(text=text)
    os.remove(image_path)


@commands_router.message(Command("cpu"))
async def cmd_cpu(message: Message):
    from src.bot.handlers.user_commands_func import get_system_info
    log_command("/cpu")

    text = await get_system_info()
    await message.answer(text)


@commands_router.message(Command("screen", "screenshot"))
async def cmd_screen(message: Message, bot: Bot):
    from src.bot.handlers.user_commands_func import screenshot
    log_command("/screen")

    shots = await screenshot()
    if not shots:
        await message.answer(_("Could not take a screenshot."))
        return

    await send_shots(message, shots)


@commands_router.message(Command('webcam', 'web', 'photo'))
async def cmd_webcam(message: Message, bot: Bot):
    from src.bot.handlers.user_commands_func import webcam
    log_command("/webcam")

    text, image, path = await webcam()
    if image and path is not None:
        await message.reply_document(document=image)
        os.remove(path)
    else:
        await message.answer(text)


@commands_router.message(Command("launch"))
async def cmd_launch(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import launch
    log_command("/launch", command.args)

    try:
        text = await asyncio.wait_for(launch(args=command.args), timeout=5)
    except asyncio.TimeoutError:
        text = _("Something went wrong...\nYour program was not found on the computer")
        log_result(_("Program not found"))

    await bot.send_message(chat_id=message.chat.id, text=text)


@commands_router.message(Command("link"))
async def cmd_link(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import link
    log_command("/link", command.args)

    text = await link(args=command.args)
    await bot.send_message(chat_id=message.chat.id, text=text)


@commands_router.message(Command('clipboard'))
async def clipboard_command(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import clipboard, replace_tags
    log_command("/clipboard", command.args)

    text = await clipboard(args=command.args)

    try:
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode='Markdown')
    except TelegramBadRequest:
        text = await replace_tags(text, '*', '<b>', '</b>')
        text = await replace_tags(text, '`', '<pre>', '</pre>')
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode='html')


@commands_router.message(Command("task"))
async def cmd_task(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import task
    log_command("/task", command.args)

    task_kb = None
    try:
        text, task_kb = await asyncio.wait_for(task(args=command.args), timeout=5)
    except asyncio.TimeoutError:
        text = _("Something went wrong...\ntimeout exceeded 😨")
        logger.error("/task timeout exceeded")

    if text.strip():  # Check if the text is empty
        if task_kb is not None:
            await message.answer(text=text, reply_markup=task_kb)
        else:
            await message.answer(text=text)
    else:
        logger.info(f"Empty text received for /task. {text}")


@commands_router.message(Command("say"))
async def cmd_say(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import say
    log_command("/say", command.args)

    text = await say(command.args)
    await message.answer(text=text)


cd = os.path.expanduser("~")


def set_cd(path: str) -> None:
    global cd
    cd = os.path.abspath(path)


async def render_listing(bot: Bot, page: int = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    """Страница содержимого текущей папки. Имена - ссылки вида ?start=<токен>:
    в callback_data путь не влезает, а по такой ссылке бот сам получит команду"""
    username = (await bot.me()).username
    entries = await asyncio.to_thread(browser.read_dir, cd)

    header = _("<b>📂 {path}</b>").format(path=cd)
    if not entries:
        return f"{header}\n\n{_('The folder is empty.')}", None

    pages = browser.page_count(len(entries))
    page = max(0, min(page, pages - 1))

    lines = [header, ""]
    parent = os.path.dirname(cd)
    if page == 0 and parent != cd:
        lines.append(f'📁 <a href="https://t.me/{username}?start={browser.token_for(parent)}">..</a>')

    for entry in browser.slice_page(entries, page):
        icon = "📁" if entry.is_dir() else "📄"
        link = f"https://t.me/{username}?start={browser.token_for(entry.path)}"
        # Имя идёт в HTML, а в нём легально бывают & и скобки
        name = html.escape(entry.name[:NAME_LIMIT])
        lines.append(f'{icon} <a href="{link}">{name}</a>')

    if pages == 1:
        return "\n".join(lines), None

    lines.append("")
    lines.append(_("{count} items").format(count=len(entries)))

    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="«", callback_data=f"ls_page_{page - 1}"))
    row.append(InlineKeyboardButton(text=f"{page + 1} / {pages}", callback_data="ls_noop"))
    if page < pages - 1:
        row.append(InlineKeyboardButton(text="»", callback_data=f"ls_page_{page + 1}"))

    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=[row])


@commands_router.message(Command("ls"))
async def list_directory(message: Message, bot: Bot):
    log_command("/ls")

    try:
        text, keyboard = await render_listing(bot)
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"/ls error: {str(e)}")
        await message.answer(_("Error: <b>{error}</b>").format(error=e))


@commands_router.message(Command("cd"))
async def change_directory(message: Message, bot: Bot, command: CommandObject):
    log_command("/cd", command.args)

    try:
        if not command.args:
            await message.answer(_("<i>Wrong command usage!</i>\n"
                                   "<blockquote><b>Example:</b> /cd + folder name or path</blockquote>\n\n"
                                   "You are in:\n<code>{path}</code>").format(path=cd))
            return

        new_path = os.path.abspath(os.path.join(cd, command.args))
        if not os.path.isdir(new_path):
            await message.answer(_("Directory does not exist."))
            return

        set_cd(new_path)
        text, keyboard = await render_listing(bot)
        await message.answer(text, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"/cd error: {str(e)}")
        await message.answer(_("Error: <b>{error}</b>").format(error=e))


@commands_router.message(Command('download'))
async def handle_download_command(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import download
    log_command("/download", command.args)

    text, file = await download(args=command.args)
    if file is not None:
        await bot.send_document(chat_id=message.chat.id, document=file)
    await bot.send_message(chat_id=message.chat.id, text=text)


@commands_router.message(Command('wifi'))
async def get_wifi_passwords(message: Message):
    log_command("/wifi")

    export_dir = tempfile.mkdtemp(prefix="nucontrol_wifi_")
    try:
        result = await process.run_async(
            ['netsh', 'wlan', 'export', 'profile', 'key=clear', f'folder={export_dir}'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            await message.answer(_("Error running netsh: {error}").format(error=result.stderr.strip()))
            logger.debug(f'Error running netsh command: {result.stderr}')
            return

        message_text = ""
        for file in os.listdir(export_dir):
            if not file.endswith(".xml"):
                continue
            try:
                with open(os.path.join(export_dir, file), 'r', encoding='utf-8') as xml_file:
                    xml_content = xml_file.read()
            except Exception as e:
                logger.error(f"Error reading Wi-Fi profile {file}: {e}")
                continue

            ssid_match = re.search(r'<name>(.*?)</name>', xml_content)
            password_match = re.search(r'<keyMaterial>(.*?)</keyMaterial>', xml_content)
            if ssid_match and password_match:
                ssid = ssid_match.group(1)
                password = password_match.group(1)
                message_text += f"SSID: <code>{ssid}</code>\nPASS: <tg-spoiler>{password}</tg-spoiler>\n\n"

        if message_text:
            await message.answer(message_text)
        else:
            await message.answer(_("No saved Wi-Fi networks with a password were found."))
    except Exception as e:
        logger.error(f"/wifi error: {str(e)}")
        await message.answer(_("Error: <b>{error}</b>").format(error=e))
    finally:
        shutil.rmtree(export_dir, ignore_errors=True)
