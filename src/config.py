import configparser
import os

# This file exists only for paths


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

LOGS_FILE_PATH = os.path.join(project_root, 'logs')
CONFIG_FILE_PATH = os.path.join(project_root, 'config.ini')
AUTOSTART_PATH = f"{project_root}/NuControl.bat"

if not os.path.exists(CONFIG_FILE_PATH):
    print('not exists')
    with open(os.path.join(CONFIG_FILE_PATH), 'w') as file:
        file.write('[Settings]\n')
        file.write('language = en\n')
        file.write('autostart = 0\n')
        file.write('enabled = 0\n')
        file.write('friends_restrict = 0\n')
        file.write('logs = False\n')
        file.write('debug = False\n')
        file.write('admin_id = \n')
        file.write('bot_token = ENTER_TOKEN\n')

config = configparser.ConfigParser()
config.read(CONFIG_FILE_PATH)


admin_id_raw = config.get('Settings', 'admin_id', fallback='').strip()
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else None
TOKEN = config.get('Settings', 'bot_token', fallback='')