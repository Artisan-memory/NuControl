import configparser
import os
import socket
import subprocess
import sys

from src.config import CONFIG_FILE_PATH, CONTROL_HOST, CONTROL_PORT, project_root
from src.logging_setup import gui_logger

BOT_ENTRYPOINT = os.path.join(project_root, "bot.py")


class BotManager:
    def __init__(self, config: configparser.ConfigParser):
        self.config: configparser.ConfigParser = config
        self.bot_process: subprocess.Popen | None = None

    def start_process(self) -> None:
        try:
            self.bot_process = subprocess.Popen(
                [sys.executable, BOT_ENTRYPOINT],
                cwd=project_root,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            self._update_config('1')
            gui_logger.info("Bot process started (pid=%s)", self.bot_process.pid)
        except Exception as e:
            gui_logger.error("Error starting the bot process: %s", e)

    def stop_process(self) -> None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((CONTROL_HOST, CONTROL_PORT))
                s.sendall(b"stop")
            gui_logger.info("Sent stop command to bot process")
        except OSError as e:
            gui_logger.warning("Could not reach the bot process to stop it: %s", e)
        finally:
            self._update_config('0')

    def _update_config(self, enabled_value: str) -> None:
        self.config.set('Settings', 'enabled', enabled_value)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as config_file:
            self.config.write(config_file)
