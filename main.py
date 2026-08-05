import configparser
import threading
import ctypes
import os

from src.config import CONFIG_FILE_PATH
from src.gui.gui import App
from src.gui.tray import SystemTray
from src.logging_setup import gui_logger

MUTEX_NAME = "Local\\NuControl"
ERROR_ALREADY_EXISTS = 183

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
    """Claim a named mutex and return its handle; the caller must keep it referenced
    for the whole process lifetime. Unlike a lock file it cannot go stale after a crash.
    Exits if another instance already holds it.
    """
    # Раньше тут был tendo, который на винде нормально не работает
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel32.CreateMutexW.restype = ctypes.c_void_p

    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        ctypes.windll.user32.MessageBoxW(0, "NuControl is already running", "Error", 0x10)
        gui_logger.info("NuControl is already running")
        exit(1)
    if not handle:
        gui_logger.warning("Could not create the single-instance mutex (error %s)",
                           ctypes.get_last_error())
    return handle


def main():
    instance_lock = ensure_single_instance()  # noqa: F841 - kept alive to hold the mutex

    config = load_config(CONFIG_FILE_PATH)
    minimized = config.getint("Settings", "autostart", fallback=0)  # Default to 0

    try:
        app_instance = App()
        gui_logger.info("Initializing the Tkinter application and system tray")
        tray_instance = SystemTray(app_instance)

        # Minimize the application at the start if minimized is set to True
        if minimized:
            app_instance.on_close()  # Minimizing on startup to tray
            # Not run_bot(): right after a boot there is no network yet, and the
            # check has to happen off the mainloop so the window still comes up
            app_instance.start_bot_when_online()

        tray_thread = threading.Thread(target=run_tray, args=(tray_instance,))
        tray_thread.start()

        gui_logger.info("Starting the Tkinter application")
        start_app(app_instance)
    except KeyboardInterrupt:
        gui_logger.info("App interrupted by user")
        exit(0)


if __name__ == "__main__":
    main()
