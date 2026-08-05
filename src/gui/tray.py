import pystray
import os

from PIL import Image
from pystray import MenuItem as Item

from src.config import APP_VERSION
from src.gui.setup_config import load_config
from src.gui.bot_manager import BotManager
from src.logging_setup import gui_logger

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

class SystemTray:
    """Class representing the system tray icon and its menu."""

    def __init__(self, app):
        self.app = app
        self.menu = (Item('Show', self.on_show), Item('Exit', self.on_quit))
        self.icon = self.create_image()
        self.tray = pystray.Icon("name", self.icon, f"NuControl v{APP_VERSION}", self.menu)

        self.config = load_config()
        self.language = self.config.get('Settings', 'language')
        self.bot_manager = BotManager(self.config)

        gui_logger.info("SystemTray initialized")

    def run(self):
        """Run the system tray icon."""
        gui_logger.info("Tray icon running")
        self.tray.run()

    def create_image(self):
        """Create and return the system tray icon image."""
        icon_path = f"{project_root}/CTk_images/icon.ico"
        image = Image.open(icon_path)
        image.thumbnail((16, 16))
        return image

    def on_show(self):
        """Show the application window with a fade-in effect."""
        gui_logger.info("Showing the application window")
        self.app.deiconify()
        gui_logger.info("App window shown")

    def on_quit(self):
        """Quit the application and stop the tray icon."""
        gui_logger.info("Quitting the application and stopping the tray icon")
        self.bot_manager.stop_process()
        self.tray.stop()
        self.app.quit()
        gui_logger.info("App quitting and tray icon stopped")
