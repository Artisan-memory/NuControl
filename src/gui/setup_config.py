# setup_config.py

import configparser
import os
from src.config import project_root

def create_config_file():
    with open(os.path.join(project_root, 'config.ini'), 'w') as file:
        file.write('[Settings]\n')
        file.write('language = en\n')
        file.write('autostart = 0\n')
        file.write('enabled = 0\n')
        file.write('friends_restrict = 0\n')
        file.write('logs = False\n')
        file.write('debug = False\n')
        file.write('admin_id = \n')
        file.write('bot_token = ENTER_TOKEN\n')


def load_config():
    if not os.path.exists('config.ini'):
        create_config_file()

    config = configparser.ConfigParser()
    config.read('config.ini')
    return config
