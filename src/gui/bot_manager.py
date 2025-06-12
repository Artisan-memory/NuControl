import subprocess
import configparser
import socket
from src.config import CONFIG_FILE_PATH, project_root


class BotManager:
    CONFIG_FILE = CONFIG_FILE_PATH

    def __init__(self, config: configparser.ConfigParser):
        self.config: configparser.ConfigParser = config
        self.bot_process: subprocess.Popen | None = None

    def start_process(self) -> None:
        try:
            self.bot_process = subprocess.Popen(['python', 'bot.py'],
                                               creationflags=subprocess.CREATE_NO_WINDOW)
            self._update_config('1')
        except Exception as e:
            print('Error starting the bot process: {e}')

    def stop_process(self) -> None: 
        try:
            if self.bot_process:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(("127.0.0.1", 9999))
                    s.sendall(b"stop")
                    print(f"Sent stop")
            self._update_config('0')
        except Exception as e:
            print(f'Error stopping the bot process: {e}')

    def _update_config(self, enabled_value: str) -> None:
        self.config.set('Settings', 'enabled', enabled_value)
        with open(self.CONFIG_FILE, 'w') as config_file:
            self.config.write(config_file)

