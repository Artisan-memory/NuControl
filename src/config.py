import configparser
import os

# Central place for paths and the parsed config. Everything that needs a path
# or a setting reads it from here so behaviour no longer depends on the CWD

APP_VERSION = "0.0.1-beta"

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LOGS_FILE_PATH = os.path.join(project_root, 'logs')
CONFIG_FILE_PATH = os.path.join(project_root, 'config.ini')
TMP_DIR = os.path.join(project_root, 'tmp')
AUTOSTART_PATH = os.path.join(project_root, 'NuControl.bat')

DEFAULT_CONFIG = {
    'language': 'en',
    'autostart': '0',
    'enabled': '0',
    'admin_id': '',
    'bot_token': 'ENTER_TOKEN',
    'control_port': '9999',
}


def write_default_config(path: str = CONFIG_FILE_PATH) -> None:
    """Create config.ini with default settings if it does not exist yet."""
    config = configparser.ConfigParser()
    config['Settings'] = DEFAULT_CONFIG
    with open(path, 'w', encoding='utf-8') as file:
        config.write(file)


if not os.path.exists(CONFIG_FILE_PATH):
    write_default_config()

config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH, encoding='utf-8')

admin_id_raw = config.get('Settings', 'admin_id', fallback='').strip()
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else None
TOKEN = config.get('Settings', 'bot_token', fallback='')

# Loopback port the GUI uses to tell the bot process to stop. Configurable so a
# second NuControl (or an unrelated process on 9999) does not deadlock the pair
CONTROL_HOST = '127.0.0.1'
CONTROL_PORT = config.getint('Settings', 'control_port', fallback=9999)
