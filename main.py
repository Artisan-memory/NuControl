import configparser
import threading
import ctypes
import os

from src.config import CONFIG_FILE_PATH
from tendo import singleton
from src.gui.gui import App
from src.gui.tray import SystemTray
from src.logging_setup import gui_logger

def load_config(config_path):
    """Load configuration settings from the config file."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        gui_logger.info("Config file not found")
        exit()
    config.read(config_path)
    return config


def run_tray(system_tray):
    """Run the application in the system tray."""
    system_tray.run()


def start_app(application):
    """Run the application."""
    gui_logger.info("Run application")
    try:
        application.mainloop()
    finally:
        gui_logger.info("Stopping the Tkinter application")


def ensure_single_instance():
    """Ensure that only one instance of the application is running."""

    # Эта хуйня не работает

    try:
        singleton.SingleInstance(flavor_id="NuControl")
    except singleton.SingleInstanceException:
        ctypes.windll.user32.MessageBoxW(0, "The NuControl is already running", "Error", 0x10)
        gui_logger.info("The NuControl is already running")
        exit(1)


def main():
    ensure_single_instance()

    # Load the configuration

    config = load_config(CONFIG_FILE_PATH)
    minimized = config.getint("Settings", "autostart", fallback=0)  # Default to 0

    try:
        app_instance = App()
        gui_logger.info("Initializing the Tkinter application and system tray")
        tray_instance = SystemTray(app_instance)

        # Minimize the application at the start if minimized is set to True
        if minimized:
            app_instance.on_close()  # Minimizing on startup to tray
            app_instance.run_bot()

        tray_thread = threading.Thread(target=run_tray, args=(tray_instance,))
        tray_thread.start()

        gui_logger.info("Starting the Tkinter application")
        start_app(app_instance)
    except KeyboardInterrupt:
        gui_logger.info("App interrupted by user")
        exit(0)


if __name__ == "__main__":
    main()
