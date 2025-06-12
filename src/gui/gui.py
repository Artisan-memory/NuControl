# gui.py

import os
import json
import shutil
import sys
import webbrowser
import ctypes
import requests
import customtkinter
import winreg
import aioshutil

from tkinter import StringVar
from PIL import Image, ImageTk
from customtkinter import CTkSwitch, CTkLabel, CTkImage, CTkEntry, CTkButton, CTkComboBox, CTkFrame, CTkTextbox
from TkToolTip import ToolTip
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from CTkMessagebox import CTkMessagebox

from src.logging_setup import gui_logger
from src.gui.setup_config import load_config
from src.gui.bot_manager import BotManager
from src.gui.tray import SystemTray

from src.config import LOGS_FILE_PATH, CONFIG_FILE_PATH, AUTOSTART_PATH

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

LOG_FILE_PATH = f"{LOGS_FILE_PATH}/log_easy.log"

if not os.path.exists(LOG_FILE_PATH):
    app_info = (
        "\t\t🖥️NuControl by Artisan-memory🤖\n\n"
        "\t\nThis application is designed to control your PC remotely. 🌐\n"
        "For more information and updates, visit our GitHub repository:\n"
        "(https://github.com/Artisan-memory/NuControl)\n\n"
        "\n\t\t\tVersion: 0.0.1-beta\n\n"
        "==============================================\n\n"
    )
    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as file:
        file.write(app_info)
    gui_logger.info("Log file created and app info written.")

os.makedirs(f"{LOGS_FILE_PATH}/botLog", exist_ok=True)


class BaseAppButtons(CTkFrame):
    """Base buttons in the application."""

    def __init__(self, master, translations):
        gui_logger.info("Initializing BaseAppButtons")
        super().__init__(master)
        self.translations = translations
        self.config = load_config()
        self.create_buttons()
        gui_logger.info("BaseAppButtons initialized")

    def create_buttons(self):
        """Create the buttons"""
        gui_logger.info("Creating buttons in BaseAppButtons")
        buttons = [
            ("Logs", self.master.show_logs_frame),
            ("Friends", self.master.show_friends_frame),
            ("Settings", self.master.show_settings_frame)
        ]
        for i, (text, command) in enumerate(buttons):
            button = CTkButton(
                self, text=self.translations[text], corner_radius=5,
                command=command, width=85, height=33
            )
            if text == "Settings":
                button.grid(row=i + 10, column=0, padx=12, pady=(190, 0),
                            sticky="w")
            else:
                button.grid(row=i, column=0, padx=12, pady=(12, 0), sticky="w")
        gui_logger.info("Buttons have been created")


def check_token(token: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        response_data = response.json()
        return response_data.get("ok", False)
    except requests.exceptions.RequestException:
        return False


class LogFileEventHandler(FileSystemEventHandler):
    def __init__(self, textbox):
        super().__init__()
        self.textbox = textbox
        gui_logger.info(f"Initialized LogFileEventHandler with textbox: {self.textbox}")

    def on_modified(self, event):
        # gui_logger.info(f"Detected file modification event: {event}")
        # gui_logger.info(f"Event source path: {event.src_path}")

        if event.src_path.endswith(os.path.basename(LOG_FILE_PATH)):
            gui_logger.info(f"File modified matches LOG_FILE_PATH: {LOG_FILE_PATH}")
            try:
                with open(f"{LOG_FILE_PATH}/log_easy.log", 'r', encoding='utf-8') as file:
                    log_text = file.read()
                    gui_logger.info("Read log file content successfully.")
                    self.update_textbox(log_text)
            except Exception as e:
                gui_logger.error(f"Error reading log file: {e}")
        else:
            # gui_logger.info("Modified file does not match LOG_FILE_PATH.")
            pass

    def update_textbox(self, text):
        gui_logger.info("Scheduling update of textbox content.")
        self.textbox.after(0, self._update_textbox_content, text)

    def _update_textbox_content(self, text):
        gui_logger.info("Updating textbox content.")
        try:
            self.textbox.configure(state='normal')
            self.textbox.delete("0.0", "end")
            self.textbox.insert("0.0", text)
            self.textbox.configure(state='disabled')
            gui_logger.info("Textbox content updated successfully.")
        except Exception as e:
            gui_logger.error(f"Error updating textbox content: {e}")


class App(customtkinter.CTk):
    """Main application class."""

    def __init__(self):
        gui_logger.info("Initializing App")
        super().__init__()
        self.Ctk_images_path = f"{project_root}/CTk_images/"
        self.config = load_config()
        self.language = self.config.get('Settings', 'language')
        self.language_map = self.load_language_map()
        self.translations = self.load_translations(self.language)
        self.setup_ui()
        self.bot_manager = BotManager(self.config)
        self.bot_running = self.config.getboolean('Settings', 'enabled')
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.system_tray = SystemTray(self)
        self.user_path = os.path.expanduser("~")
        self.startup_dir = os.path.join(
            self.user_path,
            "AppData", "Roaming", "Microsoft", "Windows",
            "Start Menu", "Programs", "Startup"
        )
        gui_logger.info("App initialized")

    def load_translations(self, language: str) -> dict:
        """Load translations based on the selected language."""
        gui_logger.info(f"Loading translations for language: {language}")
        try:
            with open(f'{project_root}/locales/{language}.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            gui_logger.warning(
                f"Translation file for language '{language}' not found. Loading default 'en' translations.")
            with open(f'{project_root}/locales/en.json', 'r', encoding='utf-8') as file:
                return json.load(file)

    def on_close(self):
        """Handle the window close event by hiding the window and creating a tray icon."""
        gui_logger.info("App window hidden")
        self.withdraw()

    def load_language_map(self) -> dict:
        """Load language names and their codes from a JSON file."""
        with open(f'{project_root}/locales/initializer_locales.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def setup_ui(self):
        """Set up the user interface."""
        gui_logger.info("Setting up UI")
        self.title("NuControl || 0.0.1-beta")
        self.geometry("660x400")
        self.iconbitmap(self.Ctk_images_path + 'icon.ico')
        self.resizable(False, False)

        # Change icon in taskbar
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        customtkinter.set_default_color_theme('blue')
        customtkinter.set_appearance_mode("dark")
        self.configure_columns_and_rows()
        self.button_frame = BaseAppButtons(self, self.translations)
        self.button_frame.grid(row=0, column=0, padx=12, pady=(12, 0), sticky="nsw")
        self.right_frame = CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=12, pady=(12, 0), sticky="nsew")

        self.add_start_polling_button()
        self.show_settings_frame()
        gui_logger.info("UI setup complete")

    def add_start_polling_button(self):
        """Add start polling button and GitHub image."""
        container_frame = CTkLabel(self, text='', height=60)
        container_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        container_frame.grid_columnconfigure(0, weight=1)
        container_frame.grid_columnconfigure(1, weight=0)


        self.img_github = Image.open(self.Ctk_images_path + "github-mark-white.png")
        self.img_github_tk = ImageTk.PhotoImage(self.img_github)
        self.github_icon = CTkImage(light_image=self.img_github, dark_image=self.img_github, size=(40, 40))

        github_label = CTkLabel(container_frame, text='', image=self.github_icon)
        github_label.grid(row=0, column=0, padx=(25, 100), pady=(0, 0), sticky="w")
        github_label.bind("<Button-1>", self.open_github)
        github_label.bind("<Enter>", lambda e: github_label.configure(cursor="hand2"))

        self.start_polling = CTkButton(
            container_frame, text=self.translations["Start"], corner_radius=5,
            command=self.run_bot, width=85, height=35
        )
        self.start_polling.grid(row=0, column=1, padx=13, pady=(10, 6), sticky="e")

    def run_bot(self):
        """LET'S JSUT FORGET ABOUT THIS"""
        gui_logger.info("Attempting to run bot")
        if not self.bot_running:
            gui_logger.info("Bot is not running, starting bot")
            if not self.valid_bot_config():
                return

            self.bot_manager.start_process()
            self.start_polling.configure(text=self.translations["Stop"])
            gui_logger.info("Bot started")
        else:
            self.bot_manager.stop_process()
            self.start_polling.configure(text=self.translations["Start"])
            gui_logger.info("Bot stopped")
        self.bot_running = not self.bot_running

    def valid_bot_config(self):
        """Validate bot configuration."""
        user_id_check = self.config.get('Settings', 'admin_id')
        bot_token_check = self.config.get('Settings', 'bot_token')

        try:
            requests.get("http://www.google.com", timeout=2)
        except requests.exceptions.RequestException:
            CTkMessagebox(
                title="No internet connection", message=self.translations["no_internet_connection"],
                icon=self.Ctk_images_path + "no-internet.png"
            )
            gui_logger.warn("No internet connection")
            return

        if not user_id_check.isdigit():
            CTkMessagebox(
                title="Admin id", message=self.translations["admin_id_error"],
                icon=self.Ctk_images_path + "warning.png"
            )
            gui_logger.warning("Invalid admin id")
            return False

        if not check_token(token=bot_token_check):
            CTkMessagebox(
                title="BOT_TOKEN", message=self.translations["bot_token_error"],
                icon=self.Ctk_images_path + "warning.png"
            )
            gui_logger.warning("Invalid bot token")
            return False
        return True

    def open_github(self, event):
        """Open the GitHub repository in the default web browser."""
        gui_logger.info("Opening GitHub repository")
        webbrowser.open("https://github.com/Artisan-memory/Nucontrol")

    def configure_columns_and_rows(self):
        """Configure the grid columns and rows."""
        gui_logger.info("Configuring grid columns and rows")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def show_logs_frame(self):
        """Display the logs frame."""
        gui_logger.info("Showing logs frame")
        self.clear_right_frame_widgets()
        self.textbox = CTkTextbox(
            master=self.right_frame, width=503, height=327, corner_radius=0,
            fg_color="transparent", wrap='none'
        )
        self.textbox.grid(row=0, column=0, sticky="nsew")
        gui_logger.info(f"Textbox created: {self.textbox}")

        event_handler = LogFileEventHandler(self.textbox)
        observer = Observer()
        observer.schedule(event_handler, path=LOG_FILE_PATH, recursive=False)
        observer.start()
        gui_logger.info(f"Observer started for path: {os.path.dirname(LOG_FILE_PATH)}")

        self.update_log_text()
        gui_logger.info("Logs frame displayed")

    def update_log_text(self):
        """Update the content of the log text box."""
        gui_logger.info("Updating log text")
        try:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as file:
                log_text = file.read()
                gui_logger.info("Read log file content successfully.")
            self.textbox.after(0, self._update_textbox_content, log_text)
        except Exception as e:
            gui_logger.error(f"Error reading log file: {e}")

    def _update_textbox_content(self, text: str):
        """Internal method to update the content of the text box."""
        self.textbox.configure(state='normal')
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", text)
        self.textbox.configure(state='disabled')
        gui_logger.info("Textbox content updated successfully.")

    def show_friends_frame(self):
        """Display the friends frame."""
        gui_logger.info("Showing friends frame")
        self.clear_right_frame_widgets()
        friends_main_label = CTkLabel(
            self.right_frame, text=self.translations["Friends"], font=("Arial", 20, "bold"), anchor="center"
        )
        friends_main_label.grid(row=0, column=1, padx=12, pady=(12, 0), sticky="ew")
        under_line_label = CTkLabel(self.right_frame, text='', anchor="center")
        under_line_label.grid(row=1, column=1, padx=12, pady=(12, 0), sticky="ew")

        entries = []
        for i in range(4):
            entry_nickname = CTkEntry(self.right_frame, placeholder_text=f"Nickname {i + 1}")
            entry_nickname.grid(row=2 + i, column=0, padx=10, pady=(12, 0), sticky="w")
            entries.append(entry_nickname)
            entry_userid = CTkEntry(self.right_frame, placeholder_text=f"user_id {i + 1}")
            entry_userid.grid(row=2 + i, column=1, padx=25, pady=(12, 0), sticky="w")
            entries.append(entry_userid)
        gui_logger.info("Friends frame displayed")

    def get_toggle_state(self, name: str) -> bool:
        """Get the current toggle state from the config."""
        return self.config.getboolean('Settings', name)

    def show_settings_frame(self):
        """Display the settings frame."""
        gui_logger.info("Showing settings frame")
        self.clear_right_frame_widgets()
        self.create_settings_widgets(self.right_frame)
        gui_logger.info("Settings frame displayed")

    def create_settings_widgets(self, settings_frame: CTkFrame):
        """Create the settings widgets."""
        gui_logger.info("Creating settings widgets")
        settings_label = CTkLabel(
            settings_frame, text=self.translations["Settings"], font=("Arial", 20, "bold"), anchor="center"
        )
        settings_label.grid(row=0, column=1, padx=12, pady=(12, 0), sticky="ew")

        self.switch_var_autostart = StringVar(value=self.get_toggle_state(name='autostart'))
        toggle_settings_autostart = CTkSwitch(
            settings_frame, text=self.translations["Autostart"], command=self.switch_event,
            variable=self.switch_var_autostart, onvalue=True, offvalue=False
        )
        toggle_settings_autostart.grid(row=1, column=0, padx=12, pady=(12, 0), sticky="w")
        gui_logger.info(f"Autostart toggle set to {self.switch_var_autostart.get()}")

        if self.get_toggle_state(name='autostart') == 1:
            toggle_settings_autostart.select()

        toggle_bot_access = CTkSwitch(settings_frame, text=self.translations["Bot Access"])
        toggle_bot_access.grid(row=2, column=0, padx=12, pady=(12, 0), sticky="w")

        question_mark = Image.open(self.Ctk_images_path + "question-mark.png")
        question_mark = CTkImage(light_image=question_mark, dark_image=question_mark, size=(25, 25))
        image_widget = CTkLabel(settings_frame, text='', image=question_mark)
        image_widget.grid(row=2, column=1, padx=1, pady=(12, 0), sticky="w")
        ToolTip(
            image_widget,
            msg=self.translations["Bot_access_tooltip"],
            delay=0.2, follow=True,
            parent_kwargs={
                "bg": "#2C3E50", "padx": 14, "pady": 14, "borderwidth": 0, "relief": "flat",
            },
            fg="white", bg="#34495E", font=("Arial", 12, "bold"), padx=7, pady=7
        )

        language_names = list(self.language_map.keys())
        self.combobox_language = CTkComboBox(
            settings_frame, values=language_names, state='readonly', command=self.change_language
        )
        self.combobox_language.grid(row=1, column=2, pady=10, padx=15)
        current_language_name = self.get_language_name(self.language)
        self.combobox_language.set(current_language_name)
        gui_logger.info(f"Language set to {self.combobox_language.get()}")

        entry_userid_value = self.config.get('Settings', 'admin_id')
        gui_logger.info(f"User ID set to {entry_userid_value}")
        entry_userid = CTkEntry(settings_frame, placeholder_text=self.translations["Admin ID (yours)"])
        entry_userid.grid(row=2, column=2, padx=12, pady=(10, 0), sticky="w")
        if entry_userid_value:
            entry_userid.insert(0, entry_userid_value)

        self.add_settings_buttons(settings_frame, entry_userid)
        gui_logger.info("Settings widgets created")

    def add_settings_buttons(self, settings_frame: CTkFrame, entry_userid: CTkEntry):
        """Add additional settings buttons."""
        under_line_labels = [CTkLabel(self.right_frame, text='', anchor="center") for _ in range(3)]
        for i, label in enumerate(under_line_labels, start=3):
            label.grid(row=i, column=1, padx=12, pady=(12, 0), sticky="ew")

        btn_bot_token = CTkButton(
            self.right_frame, text=self.translations["BOT_TOKEN"], corner_radius=32,
            fg_color="transparent", hover_color="#C850C0", border_color="#FFCC70", border_width=2,
            command=self.open_bot_token_dialog
        )
        btn_bot_token.grid(row=6, column=1, padx=0, pady=(0, 0), sticky="ew")

        entry_userid.bind("<Return>", self.handle_userid_enter)

    def open_bot_token_dialog(self):
        """Open the bot token input dialog."""
        gui_logger.info("Opening bot token input dialog")
        dialog = customtkinter.CTkInputDialog(
            text=self.translations[
                "Write your bot token here or close the window if you have already entered the token"],
            title="SECRET | BOT_TOKEN"
        )
        token_value = dialog.get_input()
        if token_value:
            self.config.set('Settings', 'bot_token', token_value)
            with open(CONFIG_FILE_PATH, 'w') as config_file:
                self.config.write(config_file)
            gui_logger.info("Bot token saved")

    def handle_userid_enter(self, event):
        """Handle the event when the user ID is entered."""
        user_admin_value = event.widget.get()
        event.widget.master.focus_set()
        self.config.set('Settings', 'admin_id', user_admin_value)
        with open(CONFIG_FILE_PATH, 'w') as config_file:
            self.config.write(config_file)
        self.right_frame.focus_set()
        gui_logger.info("Admin ID entered")


    def add_to_startup(self, file_path: str) -> bool:
        """
        Copy the given file to the user's Startup folder.
        :param file_path: Full path to the executable/script
        :return: True if added successfully, False otherwise
        """
        gui_logger.info("Adding file to startup: %s", file_path)
        try:
            file_name = os.path.basename(file_path)
            destination = os.path.join(self.startup_dir, file_name + ".lnk")
            gui_logger.info("Copying from %s to %s", file_path, destination)

            if not os.path.exists(file_path):
                gui_logger.error("File not found: %s", file_path)
                return False
            if not os.path.exists(destination):
                self._create_windows_shortcut(file_path, destination)
                gui_logger.info("Successfully copied to startup.")
                return True
            else:
                gui_logger.warning("File already exists in startup.")
                return True
        except Exception as e:
            gui_logger.error("Copy failed: %s", str(e))
            return False

    def remove_from_startup(self, file_name: str) -> bool:
        """
        Remove the specified file from the user's Startup folder.
        :param file_name: Only the name of the file (e.g., script.exe)
        :return: True if removed successfully, False otherwise
        """
        try:
            target_path = os.path.join(self.startup_dir, file_name + ".lnk")

            if os.path.exists(target_path):
                os.remove(target_path)
                return True
            else:
                gui_logger.warning("File not found in startup: %s", file_name)
                return True
        except Exception as e:
            gui_logger.error("Failed to remove from startup: %s", str(e))
            return False

    def _create_windows_shortcut(self, file_path: str, shortcut_path: str):
        """Creates a Windows shortcut (.lnk file)."""
        from win32com.client import Dispatch
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = file_path
        shortcut.WorkingDirectory = os.path.dirname(file_path)  # Set working directory
        shortcut.Save()

    def switch_event(self):
        """
        Handle the event when the autostart switch is toggled.
        """
        gui_logger.info("Autostart switch toggled to %s", str(self.switch_var_autostart.get()))
        self.config.set('Settings', 'autostart', str(self.switch_var_autostart.get()))
        with open(CONFIG_FILE_PATH, 'w') as config_file:
            self.config.write(config_file)

        # Check whether autostart is toggled on or off
        if bool(int(self.switch_var_autostart.get())):
            # Enabling autostart
            success = self.add_to_startup(AUTOSTART_PATH)
            if not success:
                gui_logger.error("Failed to add file to startup folder")
        else:
            # Disabling autostart
            file_name = os.path.basename(AUTOSTART_PATH)
            success = self.remove_from_startup(file_name)
            if not success:
                gui_logger.error("Failed to remove file from startup folder")

    def clear_right_frame_widgets(self):
        """Clear all widgets in the right frame."""
        gui_logger.info("Clearing right frame widgets")
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def change_language(self, choice: str):
        """Change the language of the application."""
        gui_logger.info(f"Changing language to {choice}")
        self.language = self.language_map.get(choice, 'en')  # Default to English if not found
        self.translations = self.load_translations(self.language)
        self.config.set('Settings', 'language', self.language)
        with open(CONFIG_FILE_PATH, 'w') as config_file:
            self.config.write(config_file)
        self.refresh_ui()
        self.show_settings_frame()

    def get_language_name(self, language_code: str) -> str:
        """Get the full language name from the code."""
        return next((name for name, code in self.language_map.items() if code == language_code), "English")

    def refresh_ui(self):
        """Refresh the user interface."""
        gui_logger.info("Refreshing UI")
        self.button_frame.destroy()
        self.button_frame = BaseAppButtons(self, self.translations)
        self.button_frame.grid(row=0, column=0, padx=12, pady=(12, 0), sticky="nsw")
        self.start_polling.configure(
            text=self.translations["Start"] if not self.bot_running else self.translations["Stop"]
        )
        current_language_name = self.get_language_name(self.language)
        self.combobox_language.set(current_language_name)


if __name__ == "__main__":
    try:
        gui_logger.info("Starting App")
        app = App()
        app.deiconify()
        app.mainloop()
    except KeyboardInterrupt:
        gui_logger.critical("App interrupted by user")
