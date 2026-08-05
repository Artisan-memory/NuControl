import configparser
import os

from src.config import CONFIG_FILE_PATH, write_default_config


def load_config() -> configparser.ConfigParser:
    """Read config.ini from the project root, creating it with defaults if missing."""
    if not os.path.exists(CONFIG_FILE_PATH):
        write_default_config()

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_PATH, encoding='utf-8')
    return config
