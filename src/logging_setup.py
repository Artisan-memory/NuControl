# logger_setup.py
import datetime

import logging
import os
import aiofiles
from src.config import LOGS_FILE_PATH

# Create a logs directory if it doesn't exist
os.makedirs(LOGS_FILE_PATH, exist_ok=True)


# Just easy log with format [SSMMHH] text
def log_easy(message):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{current_time}] {message}"

    with open(os.path.join(LOGS_FILE_PATH, 'log_easy.log'), 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry + '\n')


# Creating formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        date_time = self.formatTime(record, "%H:%M:%S - %d/%m/%Y")
        # {record.levelname}s
        log_msg = f"{date_time} - {record.filename} - {record.funcName} - {record.getMessage()}"
        return log_msg


main_formatter = CustomFormatter()

# GUI logger
gui_logger = logging.getLogger("gui_logger")
gui_logger.setLevel(logging.INFO)
gui_file_handler = logging.FileHandler(os.path.join(LOGS_FILE_PATH, 'gui.log'), mode='a', encoding='utf-8')
gui_file_handler.setFormatter(main_formatter)
gui_logger.addHandler(gui_file_handler)
logger = gui_logger

# Example Usage (you may remove this or keep for testing)
if __name__ == "__main__":
    log_easy("This is an easy log message.")
    gui_logger.info("This is a GUI log message.")
