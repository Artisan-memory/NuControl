import asyncio
import os
import ctypes
import platform
import subprocess
import pyperclip

import cv2
import langid
import pygame
import pyscreenshot
import pyttsx3

from aiogram.types import FSInputFile
from datetime import datetime
from src.logging_setup import log_easy
from src.bot.utils.system_info import SystemInfo
from bot import timer
from loguru import logger

pygame.init()
pygame.mixer.init()


async def get_system_info():
    """Fetches and returns system information"""
    system_info = SystemInfo()

    try:

        # Call methods from the SystemInfo class
        memory_info = await system_info.get_memory_info()
        disk_info = await system_info.get_disk_info()
        # cpu_info = await system_info.get_cpu_info()

        # Get bot uptime
        uptime = await timer.get_elapsed_time()
        logger.debug("Successfully fetched system inf")

        result = (
            "<b>💾 Memory</b>\n"
            f"<b>Available:</b> {memory_info['Available']} of {memory_info['Total']}\n"
            f"<b>Used:</b> {memory_info['Used']} ({memory_info['Used Percentage']})\n\n"

            "<b>🖴 Disk</b>\n"
            f"<b>Free Space:</b> {disk_info['Free Space']} of {disk_info['Total Space']}\n"
            f"<b>Used Space:</b> {disk_info['Used Space']} ({disk_info['Used Percentage']})\n\n"

            "<b>⏳ Uptime</b>\n"
            f"<b>Uptime:</b> {uptime}\n"
        )

        # f"<b>🖥️ CPU Usage:</b> {cpu_info['CPU Usage']} (fake)"
        return result

    except Exception as e:
        logger.error(f"Error: {e}")
        return f"<b>Error occurred:</b> {e}"


async def lock_screen():
    """Locks the computer - /lock"""
    try:
        logger.info("Attempting to lock the computer.")
        ctypes.windll.user32.LockWorkStation()
        logger.info("Computer locked successfully.")
        return "PC has been successfully locked"
    except Exception as e:
        logger.error(f"Error locking the computer: {e}")
        return f"Error locking the computer: {e}"


async def screenshot():
    """Takes a screenshot - /screenshot"""
    try:
        current_directory = os.getcwd()
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d__%Hh-%Mmin-%Ssec")
        path = os.path.join(current_directory, "tmp", f"{formatted_datetime}.jpg")

        img = pyscreenshot.grab()
        img.save(path)
        image = FSInputFile(path)

        logger.info(f"Screenshot taken and saved to {path}")
        return image, path
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return None, None


async def webcam():
    """Captures an image using the webcam - /webcam"""
    try:
        logger.info("Attempting to capture image from webcam.")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            image = None
            path = None
            logger.error("Unable to open webcam.")
            return "Error: <b>Unable to open webcam</b>", image, path
        else:
            ret, frame = await asyncio.get_event_loop().run_in_executor(None, cap.read)

            if ret:
                current_directory = os.getcwd()
                tmp_directory = os.path.join(current_directory, "tmp")
                current_datetime = datetime.now()
                formatted_datetime = current_datetime.strftime("%Y-%m-%d__%Hh-%Mmin-%Ssec")
                path = os.path.join(tmp_directory, f"{formatted_datetime}.jpg")

                await asyncio.get_event_loop().run_in_executor(None, cv2.imwrite, path, frame)
                image = FSInputFile(path)
                cap.release()

                logger.info(f"Webcam image captured and saved to {path}")
                return None, image, path
            else:
                image = None
                path = None
                cap.release()
                logger.error("Error capturing image from webcam.")
                return "Error while capturing from webcam.", image, path
    except Exception as e:
        response_text = f"Error: <b>{str(e)}</b>"
        logger.error(f"Webcam capture error: {e}")
        return response_text, None, None


async def download(args):
    """Sends the specified file to the user"""
    try:
        if args:
            file_path = args
            logger.info(f"Downloading file from path: {file_path}")

            if os.path.exists(file_path):
                file = FSInputFile(file_path)
                text = "File sent successfully!"
                logger.info(f"File {file_path} sent successfully.")
                return text, file  # file = document
            else:
                logger.error(f"File {file_path} does not exist.")
                return "Specified file does not exist.", None
        else:
            logger.error("No file path provided for download.")
            return """<i>No file path provided</i>
                      <blockquote><b>Example usage:\n</b> /download + file path</blockquote>""", None
    except Exception as e:
        logger.error(f"Error in download: {e}")
        return f"Error: <b>{str(e)}</b>", None


async def say(args):
    """Plays the specified text through the speaker - /say {argument}"""
    try:
        if args:
            text = args
            logger.info(f"Playing text: {text}")
            log_easy(f"Argument /say - {text}")

            current_directory = os.getcwd()
            output_file = os.path.join(current_directory, "tmp", "output.wav")

            engine = pyttsx3.init()
            language = await asyncio.to_thread(langid.classify, text)

            if language[0] == 'ru':
                russian_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0"
                engine.setProperty('voice', russian_voice_id)
            else:
                english_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
                engine.setProperty('voice', english_voice_id)

            engine.save_to_file(text, output_file)
            engine.runAndWait()

            pygame.mixer.Sound(output_file).play()
            await asyncio.sleep(2)
            os.remove(output_file)

            logger.info("Text played successfully.")
            return "Text played successfully"
        else:
            logger.error("No text provided for /say command.")
            return """<i>No text provided for playback</i>
                      <blockquote><b>Example usage:\n</b> /say + text</blockquote>"""
    except Exception as e:
        logger.error(f"Error in say: {e}")
        return f"Error: <b>{str(e)}</b>"


async def launch(args):
    """Launches the specified program - /launch {argument}"""
    try:
        if args:
            logger.info(f"Launching program with argument: {args}")
            if args.startswith(("http://", "https://")):
                logger.error("URL provided for /launch command.")
                return "Use the /link command to open URLs."

            ret = await asyncio.create_subprocess_shell(f"start {args}")
            returned_code = await ret.wait()
            logger.info(f"Program launch returned code: {returned_code}")
            text = f"Launching <b>{args}</b>..." if returned_code == 0 else f"Failed to launch {args}"
            return text
        else:
            logger.error("No program name provided for /launch command.")
            return """<i>No program name provided</i>
                      <blockquote><b>Example usage:\n</b> /launch + program name</blockquote>"""
    except Exception as e:
        logger.error(f"Error in launch: {e}")
        return f"Error: <b>{str(e)}</b>"


async def link(args):
    """Opens the specified link - /link {argument}"""
    try:
        if args:
            log_easy(f"Argument /link - {args}")
            logger.info(f"Opening link: {args}")

            if not args.startswith(("http://", "https://")):
                args = "https://" + args

            if platform.system() == "Windows":
                ret = await asyncio.create_subprocess_shell(f"start {args}")
            else:
                logger.error("Unsupported operating system")
                return "Error: Unsupported operating system"

            returned_code = await ret.wait()
            logger.info(f"Link open returned code: {returned_code}")
            text = f"Opening <b>{args}</b>..." if returned_code == 0 else f"Cannot open {args}"
            return text
        else:
            logger.error("No link provided for /link command.")
            return """<i>No link provided</i>
                      <blockquote><b>Example usage:\n</b> /link + web link</blockquote>"""
    except Exception as e:
        logger.error(f"Error in link: {e}")
        return f"Error: <b>{str(e)}</b>"


async def clipboard(args):
    """Show clipboard text and user can modify clipboard text /clipboard or /clipboard {argument}"""
    try:
        if args:
            pyperclip.copy(args)  # Вставляем аргумент в буфер обмена
            log_easy(f"Буфер обмена обновлен: {args}")
            return f"*Буфер обмена обновлен:* `{args}`"
        else:
            clipboard_text = pyperclip.paste()  # Получаем текст из буфера обмена
            if clipboard_text:
                log_easy(f"Буфер обмена содержит:\n➖➖➖➖➖➖➖➖➖\n\n{clipboard_text}")
                return (f"*Буфер обмена содержит:*\n➖➖➖➖➖➖➖➖➖"
                        f"\n```\n{clipboard_text}```")
            else:
                return "*Буфер обмена пуст.*"
    except Exception as e:
        logger.error(f"/clipboard error: {str(e)}")
        return f"Error: *{str(e)}*"


async def replace_tags(text, symbol, open_tag, close_tag):
    return text.replace(symbol * 3, open_tag, 1)[::-1].replace(symbol * 3, close_tag[::-1], 1)[::-1]


async def shutdown(args):
    """Shuts down the computer - /shutdown {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            log_easy(f"Argument /shutdown - {args}")
            logger.info(f"Shutting down with delay: {args} minutes")
            time = float(args) * 60  # Convert to seconds
            subprocess.run(['shutdown', '/s', '/t', str(int(time))])

            if time < 60:
                return f"Computer will shut down in {int(time)} seconds"
            else:
                return f"Computer will shut down in {int(time) // 60} minutes"
        else:
            logger.info("Immediate shutdown")
            subprocess.run(['shutdown', '/s', '/t', '20'])
            return "Computer will shut down immediately"
    except Exception as e:
        logger.error(f"Error in shutdown: {e}")
        return f"Error: <b>{str(e)}</b>"


async def reboot(args):
    """Reboots the computer - /reboot {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            log_easy(f"Argument /reboot - {args}")
            logger.info(f"Rebooting with delay: {args} minutes")
            time = float(args) * 60  # Convert to seconds
            subprocess.run(['shutdown', '/r', '/t', str(int(time))])

            if time < 60:
                return f"Computer will reboot in {int(time)} seconds"
            else:
                return f"Computer will reboot in {int(time) // 60} minutes"
        else:
            logger.info("Immediate reboot")
            subprocess.run(['shutdown', '/r', '/t', '20'])
            return "Computer will reboot in 20 seconds"
    except Exception as e:
        logger.error(f"Error in reboot: {e}")
        return f"Error: <b>{str(e)}</b>"


async def hibernate(args):
    """Hibernates the computer - /hibernate {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            log_easy(f"Argument /hibernate - {args}")
            logger.info(f"Hibernating with delay: {args} minutes")
            time = float(args) * 60  # Convert to seconds
            subprocess.run(['shutdown', '/h', '/t', str(int(time))])

            if time < 60:
                return f"Computer will hibernate in {int(time)} seconds"
            else:
                return f"Computer will hibernate in {int(time) // 60} minutes"
        else:
            logger.info("Immediate hibernation")
            subprocess.run(['shutdown', '/h', '/t', '2'])
            return "Computer will hibernate in 2 seconds"
    except Exception as e:
        logger.error(f"Error in hibernate: {e}")
        return f"Error: <b>{str(e)}</b>"


async def cancel():
    """Cancels scheduled shutdown/reboot - /cancel"""
    try:
        subprocess.run(['shutdown', '/a'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Scheduled shutdown/reboot canceled.")
        return "Scheduled actions have been canceled"
    except subprocess.CalledProcessError as e:
        if e.returncode == 1116:
            logger.warning("No scheduled actions to cancel.")
            return "No scheduled actions to cancel"
        else:
            logger.error(f"Error canceling scheduled actions: {e}")
            return f"Error canceling scheduled actions: {e}"


async def task(args):
    """Stops the specified process - /task {argument}"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    if args:
        log_easy(f"Argument /task - {args}")
        logger.info(f"Stopping process: {args}")
        task_kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"Kill {args}", callback_data=f'task_kill_{args}')
            ]])

        try:
            out = os.popen(f"tasklist | findstr {args}").read()
            if not out.strip():
                logger.info(f"Process {args} not found.")
                return f"<i>Process <b>{args}</b> not found</i>", None

            return out, task_kb
        except Exception as e:
            logger.error(f"Error stopping process {args}: {e}")
            return f"Error stopping process {args}", task_kb
    else:
        logger.error("No process name provided for /task command.")
        return """<i>No process name provided</i>
                  <blockquote><b>Example usage:\n</b> /task + process name</blockquote>""", None


async def check_hardware():
    """Displays PC hardware information - /check"""
    try:
        import src.bot.handlers.user_commands_get_hardware as hardware
        system_info = await hardware.get_system_info()
        memory_info = await hardware.get_memory_info()
        disk_info = await hardware.get_disk_info()
        gpu_info = await hardware.get_gpu_info()

        text_check_hardware = "<b>Computer Information:</b>\n"
        for key, value in system_info.items():
            text_check_hardware += f"{key}: {value}\n"

        text_check_hardware += "<b>Memory Information:</b>\n"
        for key, value in memory_info.items():
            text_check_hardware += f"    - {key}: {value}\n"

        text_check_hardware += "<b>Disk Information:</b>\n"
        for idx, info in enumerate(disk_info, start=1):
            text_check_hardware += f"<b>Disk {idx}:</b>\n"
            for key, value in info.items():
                text_check_hardware += f"    - {key}: {value}\n"

        text_check_hardware += "<b>GPU Information:</b>\n"
        for idx, info in enumerate(gpu_info.values(), start=1):
            text_check_hardware += f"<b>GPU {idx}:</b>\n"
            for key, value in info.items():
                text_check_hardware += f"    - {key}: {value}\n"

        logger.info("Hardware information retrieved successfully.")
        return text_check_hardware
    except Exception as e:
        logger.error(f"Error retrieving hardware information: {e}")
        return f"Error: <b>{str(e)}</b>"
