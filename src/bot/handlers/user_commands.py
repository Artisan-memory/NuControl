import os
import asyncio
import clipboard
from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from watchdog.watchmedo import command
from loguru import logger
from src.logging_setup import log_easy
from src.config import project_root

commands_router = Router(name="user_commands")


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
async def cmd_start(message: Message):
    text_user = await get_user_info(message)
    log_easy(f"/start {text_user}")
    logger.info(f"Received /start {text_user}")

    await message.answer(
        "Привет! Я бот <b>NuControl</b>\n\n"
        "https://github.com/Artisan-memory/NuControl🌈\n"
    )


@commands_router.message(Command("kb", "keyboard"))
async def cmd_keyboard(message: Message):
    from src.bot.keyboards.reply import main
    text_user = await get_user_info(message)
    log_easy(f"/keyboard {text_user}")
    logger.info(f"Received /keyboard {text_user}")

    await message.answer("Клавиатура поднята", reply_markup=main)


@commands_router.message(Command("help"))
async def cmd_help(message: Message):
    text_user = await get_user_info(message)
    log_easy(f"/help {text_user}")
    logger.info(f"Received /help {text_user}")

    text = "<b>Доступные команды:</b>\n"
    text += ("""
<b>/shutdown</b> или <b>/s</b> - Выключить компьютер  
<b>/reboot</b> или <b>/r</b> - Перезагрузить компьютер  
<b>/hibernate</b> или <b>/h</b> - Перевести компьютер в спящий режим  
<b>/lock</b> или <b>/l</b> - Заблокировать компьютер  
<b>/logout</b> - Выход из текущей учетной записи  
<b>/cancel</b> - Отменить запланированные действия (выключение ПК, перезагрузка, гибернация)  
<b>/check</b> - Проверить состояние компьютера  
<i>/cpu</i> - То же самое, но сжато  
<b>/launch</b> <i>{program_name}</i> - Запустить программу  
<i>Пример:</i> <code>/launch notepad</code>  
<b>/link</b> <i>{url}</i> - Открыть ссылку  
<i>Пример:</i> <code>/link http://google.com</code> или <code>/link google.com</code> (не используйте "www", можете просто указать название сайта)  
<b>/task</b> <i>{process_name}</i> - Проверить, запущен ли процесс в данный момент, или остановить его  
<i>Пример:</i> <code>/task chrome</code>  
<b>/screen</b> - Сделать снимок экрана и получить его  
<b>/keyboard</b> или <b>/kb</b> - Показать клавиатуру  
<b>/webcam</b> или <b>/web</b> или <b>/photo</b> - Снять изображение с веб-камеры  
<b>/download</b> <i>{file_path}</i> - Отправить указанный файл с компьютера пользователю  
<i>Пример:</i> <code>/download C:/Users/Name/Documents/file.txt</code>  
<b>/say</b> <i>{text}</i> - Проиграть указанный текст через динамики компьютера  
<i>Находится в бета-версии.</i>  
<i>Пример:</i> <code>/say Hello World!</code>  
<b>/clipboard</b> или <b>/clipboard</b> <i>{text}</i> - Показать или изменить содержимое буфера обмена  
<i>Если передан аргумент (текст), он обновит буфер обмена</i>  
<i>Если аргумент не указан, просто отобразит текущее содержимое буфера обмена</i>  
<b>/wifi</b> - Показать SSID и пароль сохраненных Wi-Fi сетей на компьютере  
<i>Пример:</i> <code>/wifi</code>  
<b>/ls</b> - Показать содержимое текущей директории (как команда <code>ls</code> в Linux)  
<i>Пример:</i> <code>/ls</code>  
<b>/cd</b> <i>{directory_path}</i> - Перейти в указанную директорию (как команда <code>cd</code> в Windows)  
<i>Пример:</i> <code>/cd C:/Users/Name/Documents</code>


<b>Вы можете установить время задержки для выполнения первых четырех команд, используя <i>название команды + время в минутах</i> после команды.</b>  
<i>Пример: /shutdown 2</i> или <i>/s 2</i> (выключение через 2 минуты).""")
    await message.answer(text=text)


@commands_router.message(Command("lock", "l"))
async def cmd_lock(message: Message):
    from src.bot.handlers.user_commands_func import lock_screen
    text_user = await get_user_info(message)
    log_easy(f"/lock {text_user}")
    logger.info(f"Received /lock {text_user}")

    text = await lock_screen()
    await message.answer(text)


@commands_router.message(Command("shutdown", "s"))
async def cmd_shutdown(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import shutdown
    text_user = await get_user_info(message)
    log_easy(f"/shutdown {text_user}")
    logger.info(f"Received /shutdown {text_user}")

    text = await shutdown(args=command.args)
    await message.answer(text)


@commands_router.message(Command("reboot", "r"))
async def cmd_reboot(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import reboot
    text_user = await get_user_info(message)
    log_easy(f"/reboot {text_user}")
    logger.info(f"Received /reboot {text_user}")

    text = await reboot(args=command.args)
    await message.answer(text)


@commands_router.message(Command("hibernate", "h"))
async def cmd_hibernate(message: Message, command: CommandObject):
    from src.bot.handlers.user_commands_func import hibernate
    text_user = await get_user_info(message)
    log_easy(f"/hibernate {text_user}")
    logger.info(f"Received /hibernate {text_user}")

    text = await hibernate(args=command.args)
    await message.answer(text)


@commands_router.message(Command("cancel"))
async def cmd_cancel(message: Message):
    from src.bot.handlers.user_commands_func import cancel
    text_user = await get_user_info(message)
    log_easy(f"/cancel {text_user}")
    logger.info(f"Received /cancel {text_user}")

    text = await cancel()
    await message.answer(text)
    log_easy(f"/cancel completed {text_user}")


@commands_router.message(Command("check"))
async def cmd_check(message: Message):
    from src.bot.handlers.user_commands_func import check_hardware
    text_user = await get_user_info(message)
    log_easy(f"/check {text_user}")
    logger.info(f"Received /check {text_user}")

    hardware_info = await check_hardware()
    await message.answer(text=hardware_info)


@commands_router.message(Command("cpu"))
async def cmd_check(message: Message):
    from src.bot.handlers.user_commands_func import get_system_info
    text_user = await get_user_info(message)
    log_easy(f"/check {text_user}")
    logger.info(f"Received /check {text_user}")

    text = await get_system_info()
    await message.answer(text)


@commands_router.message(Command("screen", "screenshot"))
async def cmd_screen(message: Message, bot: Bot):
    from src.bot.handlers.user_commands_func import screenshot
    text_user = await get_user_info(message)
    log_easy(f"/screen {text_user}")
    logger.info(f"Received /screen {text_user}")

    image, path = await screenshot()
    await bot.send_document(chat_id=message.chat.id, document=image)
    os.remove(path)


@commands_router.message(Command('webcam', 'web', 'photo'))
async def cmd_webcam(message: Message, bot: Bot):
    from src.bot.handlers.user_commands_func import webcam
    text_user = await get_user_info(message)
    log_easy(f"/webcam {text_user}")
    logger.info(f"Received /webcam {text_user}")

    text, image, path = await webcam()
    if image and path is not None:
        await bot.send_document(chat_id=message.chat.id, document=image)
        os.remove(path)
    else:
        await bot.send_message(chat_id=message.chat.id, text=text)


@commands_router.message(Command("launch"))
async def cmd_launch(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import launch
    text_user = await get_user_info(message)
    log_easy(f"/launch {text_user}")
    logger.info(f"Received /launch {text_user}")

    try:
        text = await asyncio.wait_for(launch(args=command.args), timeout=5)
    except asyncio.TimeoutError:
        text = "Что-то пошло не так...\n" \
               "Ваша программа не была найдена на вашем компьютере"
        log_easy(f"/launch timeout exceeded {text_user}")

    await bot.send_message(chat_id=message.chat.id, text=text)


@commands_router.message(Command("link"))
async def cmd_link(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import link
    text_user = await get_user_info(message)
    log_easy(f"/link {text_user}")
    logger.info(f"Received /link {text_user}")

    text = await link(args=command.args)
    await bot.send_message(chat_id=message.chat.id, text=text)
    log_easy(f"/link completed {text_user}")


@commands_router.message(Command('clipboard'))
async def clipboard_command(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import clipboard, replace_tags
    text_user = await get_user_info(message)
    log_easy(f"/clipboard {text_user}")
    logger.info(f"Received /clipboard {text_user}")

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
    text_user = await get_user_info(message)
    log_easy(f"/task {text_user}")
    logger.info(f"Received /task {text_user}")

    task_kb = None
    try:
        text, task_kb = await asyncio.wait_for(task(args=command.args), timeout=5)
    except asyncio.TimeoutError:
        text = "Smth went wrong...\n" \
               "timeout exceeded 😨"
        logger.error(f"/task timeout exceeded {text_user}")

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
    text_user = await get_user_info(message)
    log_easy(f"/say {text_user}")
    logger.info(f"Received /say {text_user}")

    text = await say(command.args)
    await message.answer(text=text)
    log_easy(f"/say completed {text_user}")


###################################### TESTING CODE BELOW, DO NOT MODIFY

cd = os.path.expanduser("~")
from aiogram.utils.deep_linking import decode_payload


@commands_router.message(Command("ls"))
async def list_directory(message: Message):
    text_user = await get_user_info(message)
    log_easy(f"/ls {text_user}")
    logger.info(f"Received /ls {text_user}")

    try:
        contents = os.listdir(cd)
        if not contents:
            await message.answer("Папка пуста.")
            log_easy(f"/ls - directory is empty {text_user}")
        else:
            response = f"<b>Вы находитесь в директории:\n <code>{cd}</code>\n\n" \
                       "Директория содержит</b>:\n\n"
            for item in contents:
                response += f"<b>-</b> <code>{item}</code>\n"
            await message.answer(response)
    except Exception as e:
        logger.error(f"/ls error: {str(e)} {text_user}")
        await message.answer(f"Произошла ошибка: <b>{str(e)}</b>")


@commands_router.message(Command("cd"))
async def change_directory(message: Message, bot: Bot, command: CommandObject):
    text_user = await get_user_info(message)
    log_easy(f"/cd {text_user}")
    logger.info(f"Received /cd {text_user}")

    a = message.text
    print(a)
    try:
        global cd
        args = command.args
        if args:
            new_directory = args
            logger.info(new_directory)
            new_path = os.path.join(cd, new_directory)
            if os.path.exists(new_path) and os.path.isdir(new_path):
                cd = new_path
                await bot.send_message(message.chat.id, f"Вы в: <code>{cd}</code>")
            else:
                await bot.send_message(message.chat.id, f"Директория не существует.")
        else:
            text = f"""<i>Неправильно использована команда! </i>
<blockquote><b>Пример использования:\n </b>/cd + имя папки или путь</blockquote>\n\n
P.S. Вы находитесь в:\n <code>{cd}</code>"""
            await bot.send_message(message.chat.id, text)
    except Exception as e:
        logger.error(f"/cd error: {str(e)} {text_user}")
        await bot.send_message(message.chat.id, f"Произошла ошибка: <b>{str(e)}</b>")


@commands_router.message(Command('download'))
async def handle_download_command(message: Message, bot: Bot, command: CommandObject):
    from src.bot.handlers.user_commands_func import download
    text_user = await get_user_info(message)
    log_easy(f"/download {text_user}")
    logger.info(f"Received /download {text_user}")

    text, file = await download(args=command.args)
    if file is not None:
        await bot.send_document(chat_id=message.chat.id, document=file)
    await bot.send_message(chat_id=message.chat.id, text=text)
    log_easy(f"/download completed {text_user}")


import subprocess
import re


@commands_router.message(Command('wifi'))
async def get_wifi_passwords(message: Message):
    text_user = await get_user_info(message)
    log_easy(f"/wifi {text_user}")
    logger.info(f"Received /wifi {text_user}")

    try:
        command = ['netsh', 'wlan', 'export', 'profile', 'key=clear']
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            await message.answer(f"Ошибка при выполнении команды netsh: {result.stderr}")
            logger.debug(f'Error running netsh command: {result.stderr}')
            return

        if os.path.exists('Wi-Fi-App.xml'):
            with open('Wi-Fi-App.xml', 'r') as file:
                xml_content = file.read()

            ssid_match = re.search(r'<name>(.*?)<\/name>', xml_content)
            password_match = re.search(r'<keyMaterial>(.*?)<\/keyMaterial>', xml_content)

            if ssid_match and password_match:
                ssid = ssid_match.group(1)
                password = password_match.group(1)
                message_text = f"SSID: {ssid}\nPASS: {password}"
                await message.answer(message_text)

                try:
                    os.remove("Wi-Fi-App.xml")
                except Exception as e:
                    await message.answer(f"Ошибка при удалении файла Wi-Fi-App.xml: {str(e)}")
            else:
                await message.answer("SSID и/или пароль не найдены.")
        else:
            logger.warning("Wi-Fi-App.xml не найден. Ищем другие XML файлы...")
            found_data = False
            message_text = ""

            for file in os.listdir():
                if file.endswith(".xml"):
                    try:
                        with open(file, 'r') as xml_file:
                            xml_content = xml_file.read()

                        ssid_match = re.search(r'<name>(.*?)<\/name>', xml_content)
                        password_match = re.search(r'<keyMaterial>(.*?)<\/keyMaterial>', xml_content)

                        if ssid_match and password_match:
                            ssid = ssid_match.group(1)
                            password = password_match.group(1)
                            message_text += f"SSID: <code>{ssid}</code>\nPASS: <tg-spoiler>{password}</tg-spoiler>\n\n"
                            found_data = True

                            logger.info(f"Данные из файла {file}: SSID< - {ssid}, PASS - {password}")
                    except Exception as e:
                        logger.error(f"Ошибка при чтении файла {file}: {str(e)}")
                        continue

            if found_data:
                await message.answer(message_text)
            else:
                await message.answer("Не удалось найти SSID и пароль в XML файлах.")

            # Check for and delete any XML files created by 'netsh wlan export profile'
            for file in os.listdir():
                if file.endswith(".xml"):
                    try:
                        os.remove(file)
                        logger.info(f"🧹 Deleted temporary file: {file}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting file {file}: {str(e)}")
                        log_easy("Error ❌. Check full logs for the details *logs/botLog")
    except Exception as e:
        logger.error(f"/wifi error: {str(e)} {text_user}")
        await message.answer(f"Произошла ошибка: {str(e)}")
