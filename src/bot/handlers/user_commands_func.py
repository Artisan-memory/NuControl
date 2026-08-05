import asyncio
import csv
import io
import os
import ctypes
import platform
import re
import subprocess
import threading
import winsound

import pyperclip
import cv2
import langid
import pyttsx3

from aiogram.types import FSInputFile
from aiogram.utils.i18n import gettext as _
from datetime import datetime
from src.config import TMP_DIR, APP_VERSION
from src.logging_setup import log_result
from src.bot.utils import process, system_info
from src.bot.utils.report_image import render_report
from src.bot.utils.screen import grab_monitors
from src.bot.utils.timer import Timer
from loguru import logger

# Timer is a singleton; this returns the same instance bot.py starts on launch
timer = Timer()

BAR_WIDTH = 14


def gigabytes(value: float) -> str:
    return f"{value / 1024 ** 3:.1f} GB"


def human_size(value: float) -> str:
    for unit in ("B", "KB", "MB"):
        if value < 1024:
            return f"{value:.0f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def usage_bar(percent: float) -> str:
    """Render a percentage as a fixed-width bar, e.g. [████░░░░░░░░░░] 29%."""
    filled = min(BAR_WIDTH, max(0, round(percent / 100 * BAR_WIDTH)))
    return f"<code>[{'█' * filled}{'░' * (BAR_WIDTH - filled)}]</code> {percent:.0f}%"


def _usage_block(title: str, stats: dict) -> list[str]:
    return [
        title,
        usage_bar(stats["percent"]),
        _("{used} used of {total} · {free} free").format(
            used=gigabytes(stats["used"]),
            total=gigabytes(stats["total"]),
            free=gigabytes(stats["free"]),
        ),
    ]


async def get_system_info():
    """Short status report - /cpu"""
    try:
        memory = await system_info.get_memory_info()
        disks = await system_info.get_disk_totals()
        cpu_usage = await system_info.get_cpu_usage()
        uptime = await timer.get_elapsed_time()

        lines = [
            _("<b>⚙️ CPU</b>"),
            usage_bar(cpu_usage),
            "",
            *_usage_block(_("<b>🧠 Memory</b>"), memory),
            "",
            *_usage_block(_("<b>🖴 Disks (total)</b>"), disks),
            "",
            _("<b>⏳ Uptime</b>"),
            uptime,
        ]
        logger.debug("Successfully fetched system info")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error: {e}")
        return _("<b>Error occurred:</b> {error}").format(error=e)


async def show_on_screen(text: str):
    """Окно поверх всех на самом ПК - /msg"""
    MB_OK_TOPMOST = 0x00040040
    # MessageBoxW висит, пока его не закроют, поэтому только отдельным потоком
    threading.Thread(
        target=ctypes.windll.user32.MessageBoxW,
        args=(0, text, "NuControl", MB_OK_TOPMOST),
        daemon=True,
    ).start()


async def lock_screen():
    """Locks the computer - /lock"""
    try:
        logger.info("Attempting to lock the computer.")
        ctypes.windll.user32.LockWorkStation()
        logger.info("Computer locked successfully.")
        return _("PC has been successfully locked")
    except Exception as e:
        logger.error(f"Error locking the computer: {e}")
        return _("Error locking the computer: {error}").format(error=e)


async def logout():
    """Logs out of the current Windows user session - /logout"""
    try:
        logger.info("Attempting to log out the current session.")
        process.run(['shutdown', '/l'], check=True)
        return _("Logging out of the current session...")
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return _("Error logging out: {error}").format(error=e)


async def screenshot():
    """Takes a screenshot - /screenshot
    One (FSInputFile, path) pair per monitor, so two screens arrive as two files.
    Empty on failure."""
    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d__%Hh-%Mmin-%Ssec")
        images = await asyncio.to_thread(grab_monitors)

        shots = []
        for index, image in enumerate(images, start=1):
            suffix = f"_monitor{index}" if len(images) > 1 else ""
            path = os.path.join(TMP_DIR, f"{stamp}{suffix}.png")
            await asyncio.to_thread(image.save, path, "PNG")
            shots.append((FSInputFile(path), path))
            logger.info(f"Screenshot {index}/{len(images)} ({image.width}x{image.height}) -> {path}")

        return shots
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        return []


async def webcam():
    """Captures an image using the webcam - /webcam"""
    try:
        logger.info("Attempting to capture image from webcam.")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            image = None
            path = None
            logger.error("Unable to open webcam.")
            return _("Error: <b>unable to open the webcam</b>"), image, path
        else:
            ret, frame = await asyncio.get_event_loop().run_in_executor(None, cap.read)

            if ret:
                os.makedirs(TMP_DIR, exist_ok=True)
                formatted_datetime = datetime.now().strftime("%Y-%m-%d__%Hh-%Mmin-%Ssec")
                path = os.path.join(TMP_DIR, f"{formatted_datetime}.jpg")

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
                return _("Error while capturing from the webcam."), image, path
    except Exception as e:
        logger.error(f"Webcam capture error: {e}")
        return _("Error: <b>{error}</b>").format(error=e), None, None


async def download(args):
    """Sends the specified file to the user"""
    try:
        if args:
            file_path = args
            logger.info(f"Downloading file from path: {file_path}")

            if os.path.exists(file_path):
                file = FSInputFile(file_path)
                logger.info(f"File {file_path} sent successfully.")
                return _("File sent successfully!"), file  # file = document
            else:
                logger.error(f"File {file_path} does not exist.")
                return _("Specified file does not exist."), None
        else:
            logger.error("No file path provided for download.")
            return _("<i>No file path provided</i>\n"
                     "<blockquote><b>Example:</b> /download + file path</blockquote>"), None
    except Exception as e:
        logger.error(f"Error in download: {e}")
        return _("Error: <b>{error}</b>").format(error=e), None


async def say(args):
    """Plays the specified text through the speaker - /say {argument}"""
    try:
        if args:
            text = args
            logger.info(f"Playing text: {text}")

            os.makedirs(TMP_DIR, exist_ok=True)
            output_file = os.path.join(TMP_DIR, "output.wav")

            engine = pyttsx3.init()
            language = await asyncio.to_thread(langid.classify, text)

            if language[0] == 'ru':
                russian_voice_id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0"
                engine.setProperty('voice', russian_voice_id)
            else:
                english_voice_id = r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
                engine.setProperty('voice', english_voice_id)

            engine.save_to_file(text, output_file)
            engine.runAndWait()

            await asyncio.to_thread(winsound.PlaySound, output_file, winsound.SND_FILENAME)
            os.remove(output_file)

            logger.info("Text played successfully.")
            return _("Text played successfully")
        else:
            logger.error("No text provided for /say command.")
            return _("<i>No text provided</i>\n"
                     "<blockquote><b>Example:</b> /say + text</blockquote>")
    except Exception as e:
        logger.error(f"Error in say: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def launch(args):
    """Launches the specified program - /launch {argument}"""
    try:
        if args:
            logger.info(f"Launching program with argument: {args}")
            if args.startswith(("http://", "https://")):
                logger.error("URL provided for /launch command.")
                return _("Use the /link command to open URLs.")

            ret = await asyncio.create_subprocess_shell(f"start {args}")
            returned_code = await ret.wait()
            logger.info(f"Program launch returned code: {returned_code}")
            if returned_code == 0:
                return _("Launching <b>{program}</b>...").format(program=args)
            return _("Failed to launch {program}").format(program=args)
        else:
            logger.error("No program name provided for /launch command.")
            return _("<i>No program name provided</i>\n"
                     "<blockquote><b>Example:</b> /launch + program name</blockquote>")
    except Exception as e:
        logger.error(f"Error in launch: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def link(args):
    """Opens the specified link - /link {argument}"""
    try:
        if args:
            logger.info(f"Opening link: {args}")

            if not args.startswith(("http://", "https://")):
                args = "https://" + args

            if platform.system() == "Windows":
                ret = await asyncio.create_subprocess_shell(f"start {args}")
            else:
                logger.error("Unsupported operating system")
                return _("Error: unsupported operating system")

            returned_code = await ret.wait()
            logger.info(f"Link open returned code: {returned_code}")
            if returned_code == 0:
                return _("Opening <b>{url}</b>...").format(url=args)
            return _("Cannot open {url}").format(url=args)
        else:
            logger.error("No link provided for /link command.")
            return _("<i>No link provided</i>\n"
                     "<blockquote><b>Example:</b> /link + web link</blockquote>")
    except Exception as e:
        logger.error(f"Error in link: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def clipboard(args):
    """Show clipboard text and user can modify clipboard text /clipboard or /clipboard {argument}"""
    try:
        if args:
            pyperclip.copy(args)
            log_result(_("Clipboard updated"))
            return _("*Clipboard updated:* `{value}`").format(value=args)
        else:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                return _("*Clipboard contains:*\n➖➖➖➖➖➖➖➖➖\n```\n{content}```").format(content=clipboard_text)
            else:
                return _("*Clipboard is empty.*")
    except Exception as e:
        logger.error(f"/clipboard error: {str(e)}")
        return _("Error: *{error}*").format(error=e)


async def replace_tags(text, symbol, open_tag, close_tag):
    return text.replace(symbol * 3, open_tag, 1)[::-1].replace(symbol * 3, close_tag[::-1], 1)[::-1]


async def shutdown(args):
    """Shuts down the computer - /shutdown {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            logger.info(f"Shutting down with delay: {args} minutes")
            time = float(args) * 60  # Convert to seconds
            process.run(['shutdown', '/s', '/t', str(int(time))])

            if time < 60:
                return _("Computer will shut down in {seconds} seconds").format(seconds=int(time))
            else:
                return _("Computer will shut down in {minutes} minutes").format(minutes=int(time) // 60)
        else:
            logger.info("Immediate shutdown")
            process.run(['shutdown', '/s', '/t', '20'])
            return _("Computer will shut down immediately")
    except Exception as e:
        logger.error(f"Error in shutdown: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def reboot(args):
    """Reboots the computer - /reboot {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            logger.info(f"Rebooting with delay: {args} minutes")
            time = float(args) * 60  # Convert to seconds
            process.run(['shutdown', '/r', '/t', str(int(time))])

            if time < 60:
                return _("Computer will reboot in {seconds} seconds").format(seconds=int(time))
            else:
                return _("Computer will reboot in {minutes} minutes").format(minutes=int(time) // 60)
        else:
            logger.info("Immediate reboot")
            process.run(['shutdown', '/r', '/t', '20'])
            return _("Computer will reboot in {seconds} seconds").format(seconds=20)
    except Exception as e:
        logger.error(f"Error in reboot: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def _hibernate_after(delay_seconds: int) -> None:
    """Hibernate once the delay passes. `shutdown /h` cannot take `/t`, so a
    delayed hibernate has to be scheduled by us rather than by shutdown.exe."""
    await asyncio.sleep(delay_seconds)
    await process.run_async(['shutdown', '/h'])


async def hibernate(args):
    """Hibernates the computer - /hibernate {argument}"""
    try:
        if args:
            args = args.replace(',', '.')
            seconds = int(float(args) * 60)
            logger.info(f"Hibernating with delay: {seconds} seconds")
            asyncio.create_task(_hibernate_after(seconds))

            if seconds < 60:
                return _("Computer will hibernate in {seconds} seconds").format(seconds=seconds)
            else:
                return _("Computer will hibernate in {minutes} minutes").format(minutes=seconds // 60)
        else:
            logger.info("Immediate hibernation")
            await asyncio.to_thread(subprocess.run, ['shutdown', '/h'])
            return _("Computer will hibernate now")
    except Exception as e:
        logger.error(f"Error in hibernate: {e}")
        return _("Error: <b>{error}</b>").format(error=e)


async def cancel():
    """Cancels scheduled shutdown/reboot - /cancel"""
    try:
        process.run(['shutdown', '/a'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Scheduled shutdown/reboot canceled.")
        return _("Scheduled actions have been canceled")
    except subprocess.CalledProcessError as e:
        if e.returncode == 1116:
            logger.warning("No scheduled actions to cancel.")
            return _("No scheduled actions to cancel")
        else:
            logger.error(f"Error canceling scheduled actions: {e}")
            return _("Error canceling scheduled actions: {error}").format(error=e)


MAX_KILL_BUTTONS = 5


async def _matching_processes(pattern: str) -> dict[str, dict[str, float]]:
    """Processes whose image name contains `pattern`, grouped by image name.
    tasklist prints one row per process - a browser alone floods the reply with
    a hundred of them, so they are grouped into one line and one button each."""
    result = await process.run_async(
        ["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "tasklist failed")

    pattern = pattern.lower()
    grouped: dict[str, dict[str, float]] = {}
    for row in csv.reader(io.StringIO(result.stdout)):
        if len(row) < 5:
            continue
        name, memory = row[0], row[4]
        if pattern not in name.lower():
            continue
        # Memory reads like "12,345 K"; anything unexpected counts as zero
        kilobytes = int(re.sub(r"\D", "", memory) or 0)
        entry = grouped.setdefault(name, {"count": 0, "memory": 0})
        entry["count"] += 1
        entry["memory"] += kilobytes * 1024
    return grouped


async def task(args):
    """Lists processes matching a name and offers to kill them - /task {argument}"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    if not args:
        logger.error("No process name provided for /task command.")
        return _("<i>No process name provided</i>\n"
                 "<blockquote><b>Example:</b> /task + process name</blockquote>"), None

    logger.info(f"Looking up process: {args}")

    try:
        grouped = await _matching_processes(args)
    except Exception as e:
        logger.error(f"Error listing process {args}: {e}")
        return _("Error looking up process {program}").format(program=args), None

    if not grouped:
        logger.info(f"Process {args} not found.")
        return _("<i>Process <b>{program}</b> not found</i>").format(program=args), None

    # Самые жирные сверху, кнопок даём только на первые несколько
    ranked = sorted(grouped.items(), key=lambda item: item[1]["memory"], reverse=True)
    total = sum(entry["count"] for _name, entry in ranked)

    lines = [_("🔍 Found {count} process(es) matching <b>{program}</b>").format(
        count=total, program=args)]
    lines += [
        _("<b>{name}</b> — {count} × {memory}").format(
            name=name, count=int(entry["count"]), memory=human_size(entry["memory"]),
        )
        for name, entry in ranked
    ]

    task_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("Kill {program}").format(program=name),
                              callback_data=f'task_kill_{name}')]
        for name, _entry in ranked[:MAX_KILL_BUTTONS]
    ])
    return "\n".join(lines), task_kb


def _detail_line(stats: dict) -> str:
    return _("{used} used of {total} · {free} free").format(
        used=gigabytes(stats["used"]),
        total=gigabytes(stats["total"]),
        free=gigabytes(stats["free"]),
    )


async def check_hardware():
    """Displays PC hardware information - /check
    Returns (text, image_path or None). The bars live in the card, so the text keeps
    plain percentages and stays a complete report when the card cannot be drawn."""
    try:
        machine = await system_info.get_platform_info()
        memory = await system_info.get_memory_info()
        disks = await system_info.get_disks_info()
        gpus = await system_info.get_gpu_info()

        lines = [
            _("<b>💻 System</b>"),
            _("OS: <b>{value}</b>").format(value=machine["os"]),
            _("Computer: <b>{value}</b>").format(value=machine["host"]),
            _("User: <b>{value}</b>").format(value=machine["user"]),
            _("CPU: <code>{value}</code>").format(value=machine["cpu"]),
            _("Python: <code>{value}</code>").format(value=machine["python"]),
            "",
            _("<b>🧠 Memory</b> — {percent:.0f}%").format(percent=memory["percent"]),
            _detail_line(memory),
        ]
        meters = [{
            "label": _("Memory"),
            "detail": _detail_line(memory),
            "percent": memory["percent"],
        }]

        for disk in disks:
            label = _("{name} ({fstype})").format(name=disk["name"], fstype=disk["fstype"] or "?")
            lines += [
                "",
                _("<b>🖴 {label}</b> — {percent:.0f}%").format(label=label, percent=disk["percent"]),
                _detail_line(disk),
            ]
            meters.append({"label": label, "detail": _detail_line(disk), "percent": disk["percent"]})

        for index, gpu in enumerate(gpus, start=1):
            detail = _("VRAM: {vram} MB · Temp: {temp} °C").format(vram=gpu["vram"], temp=gpu["temp"])
            lines += [
                "",
                _("<b>🎮 GPU {index}</b> — {load}%").format(index=index, load=gpu["load"]),
                f"<b>{gpu['name']}</b>",
                detail,
            ]
            meters.append({
                "label": gpu["name"],
                "detail": detail,
                "percent": float(gpu["load"]) if gpu["load"].isdigit() else 0.0,
            })

        image_path = await asyncio.to_thread(
            render_report,
            f"NuControl {APP_VERSION}",
            f"{machine['host']} · {machine['os']}",
            meters,
        )

        logger.info("Hardware information retrieved successfully.")
        return "\n".join(lines), image_path
    except Exception as e:
        logger.error(f"Error retrieving hardware information: {e}")
        return _("Error: <b>{error}</b>").format(error=e), None
