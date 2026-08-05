# gui.py

import os
import json
import threading
import time
import webbrowser
import ctypes
import requests
import customtkinter

import tkinter
from tkinter import BooleanVar
from PIL import Image, ImageTk
from customtkinter import CTkSwitch, CTkLabel, CTkImage, CTkEntry, CTkButton, CTkComboBox, CTkFrame, CTkTextbox
from CTkMessagebox import CTkMessagebox

from src.logging_setup import gui_logger
from src.gui.setup_config import load_config
from src.gui.bot_manager import BotManager
from src.gui.tray import SystemTray

from src.config import LOGS_FILE_PATH, CONFIG_FILE_PATH, AUTOSTART_PATH, APP_VERSION

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

LOG_FILE_PATH = f"{LOGS_FILE_PATH}/log_easy.log"

if not os.path.exists(LOG_FILE_PATH):
    app_info = (
        "\t\t🖥️NuControl by Artisan-memory🤖\n\n"
        "\t\nThis application is designed to control your PC remotely. 🌐\n"
        "For more information and updates, visit our GitHub repository:\n"
        "(https://github.com/Artisan-memory/NuControl)\n\n"
        f"\n\t\t\tVersion: {APP_VERSION}\n\n"
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


NETWORK_CHECK_URL = "http://www.google.com"
NETWORK_CHECK_TIMEOUT = 3
# После загрузки винды вайфай поднимается не сразу, так что на автозапуске ждём
STARTUP_NETWORK_WAIT = 30
NETWORK_RETRY_DELAY = 2


# Tk сопоставляет Ctrl+C/V/X/A по символу клавиши, а на русской раскладке там
# кириллица, поэтому штатные сочетания молчат. Коды клавиш от раскладки не зависят
CLIPBOARD_KEYCODES = {67: "<<Copy>>", 86: "<<Paste>>", 88: "<<Cut>>"}
SELECT_ALL_KEYCODE = 65


def _on_control_key(event):
    if event.keycode == SELECT_ALL_KEYCODE:
        event.widget.select_range(0, 'end')
        event.widget.icursor('end')
        return "break"

    virtual_event = CLIPBOARD_KEYCODES.get(event.keycode)
    if virtual_event is None:
        return None
    event.widget.event_generate(virtual_event)
    return "break"


def enable_clipboard_shortcuts(widget) -> None:
    """Вешаем на весь класс Entry, а не на конкретное поле: до полей внутри
    CTkInputDialog иначе не дотянуться, там виджеты создаются позже и наружу
    не отдаются. На латинице Tk выберет более точную штатную привязку
    <Control-v>, так что второй вставки не будет
    """
    widget.bind_class("Entry", "<Control-KeyPress>", _on_control_key, add="+")


def check_token(token: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url)
        response_data = response.json()
        return response_data.get("ok", False)
    except requests.exceptions.RequestException:
        return False


def has_internet() -> bool:
    try:
        requests.get(NETWORK_CHECK_URL, timeout=NETWORK_CHECK_TIMEOUT)
        return True
    except requests.exceptions.RequestException:
        return False


def wait_for_internet(seconds: int) -> bool:
    """Retry until the connection is up or the wait runs out."""
    deadline = time.monotonic() + seconds
    while not has_internet():
        if time.monotonic() >= deadline:
            return False
        time.sleep(NETWORK_RETRY_DELAY)
    return True


class LogTail:
    """Дописывает в окно только новые строки и держит прокрутку внизу.

    Раньше файл перечитывался целиком на каждое изменение, из-за чего лог дёргался
    и терял позицию прокрутки. Опрос вместо watchdog - тот на дозапись в конец
    файла срабатывает не всегда.
    """

    INTERVAL_MS = 400

    def __init__(self, textbox):
        self.textbox = textbox
        self.offset = 0
        self.job = None

    def start(self):
        self.offset = 0
        self._append(self._read_new())
        self._schedule()

    def stop(self):
        if self.job is not None:
            self.textbox.after_cancel(self.job)
            self.job = None

    def _schedule(self):
        self.job = self.textbox.after(self.INTERVAL_MS, self._poll)

    def _poll(self):
        chunk = self._read_new()
        if chunk:
            self._append(chunk)
        self._schedule()

    def _read_new(self) -> str:
        try:
            size = os.path.getsize(LOG_FILE_PATH)
            if size < self.offset:  # лог обнулили или пересоздали
                self.offset = 0
            if size == self.offset:
                return ""
            with open(LOG_FILE_PATH, 'r', encoding='utf-8', errors='replace') as file:
                file.seek(self.offset)
                chunk = file.read()
            self.offset = size
            return chunk
        except OSError as e:
            gui_logger.error(f"Error reading log file: {e}")
            return ""

    def _append(self, text: str):
        if not text:
            return
        try:
            self.textbox.configure(state='normal')
            self.textbox.insert("end", text)
            self.textbox.configure(state='disabled')
            self.textbox.see("end")
        except Exception as e:
            gui_logger.error(f"Error updating textbox content: {e}")


class Tooltip:
    """Свой тултип: TkToolTip вешается на CTkLabel, а события мыши получают
    вложенные виджеты, поэтому подсказка не показывалась"""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.window = None
        for target in (widget, *widget.winfo_children()):
            target.bind("<Enter>", self.show, add="+")
            target.bind("<Leave>", self.hide, add="+")

    def show(self, event=None):
        if self.window is not None:
            return
        x = self.widget.winfo_rootx() + 30
        y = self.widget.winfo_rooty() + 30
        self.window = tkinter.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        tkinter.Label(
            self.window, text=self.text, justify="left",
            background="#34495E", foreground="white", relief="flat",
            font=("Arial", 10), padx=10, pady=8,
        ).pack()

    def hide(self, event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None


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
        # The bot is a child process that dies with the previous session, so at
        # GUI launch it is never running yet regardless of the stored flag
        self.bot_running = False
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
        self.title(f"NuControl || {APP_VERSION}")
        self.geometry("660x400")
        self.iconbitmap(self.Ctk_images_path + 'icon.ico')
        self.resizable(False, False)

        # Change icon in taskbar
        myappid = 'mycompany.myproduct.subproduct.version'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        customtkinter.set_default_color_theme('blue')
        customtkinter.set_appearance_mode("dark")
        enable_clipboard_shortcuts(self)
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
        """Start or stop the bot subprocess, toggling the button label."""
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

    def start_bot_when_online(self, wait_seconds: int = STARTUP_NETWORK_WAIT):
        """Autostart entry point: wait for the network, then start the bot. The wait runs
        in a worker thread so the window and the tray icon still come up meanwhile."""
        gui_logger.info("Waiting up to %ss for a connection before starting the bot", wait_seconds)

        def worker():
            online = wait_for_internet(wait_seconds)
            self.after(0, self.finish_autostart, online)

        threading.Thread(target=worker, daemon=True).start()

    def finish_autostart(self, online: bool):
        """Start the bot, or offer another attempt if there is still no network."""
        if online:
            self.run_bot()
            return

        gui_logger.warning("No internet connection after the startup wait")
        if self.ask_retry():
            self.start_bot_when_online()

    def ask_retry(self) -> bool:
        """Show the offline warning. True if the user wants another attempt."""
        retry = self.translations["Try again"]
        answer = CTkMessagebox(
            title="No internet connection", message=self.translations["no_internet_connection"],
            icon=self.Ctk_images_path + "no-internet.png", option_1=retry
        ).get()
        return answer == retry

    def valid_bot_config(self):
        """Validate bot configuration."""
        user_id_check = self.config.get('Settings', 'admin_id')
        bot_token_check = self.config.get('Settings', 'bot_token')

        while not has_internet():
            gui_logger.warning("No internet connection")
            if not self.ask_retry():
                return False

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
        webbrowser.open("https://github.com/Artisan-memory/NuControl")

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

        self.stop_log_tail()
        self.log_tail = LogTail(self.textbox)
        self.log_tail.start()
        gui_logger.info("Logs frame displayed")

    def stop_log_tail(self):
        """Опрос надо снимать при уходе со вкладки, иначе он останется на убитом виджете"""
        tail = getattr(self, "log_tail", None)
        if tail is not None:
            tail.stop()
            self.log_tail = None

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

        self.switch_var_autostart = BooleanVar(value=self.get_toggle_state(name='autostart'))
        toggle_settings_autostart = CTkSwitch(
            settings_frame, text=self.translations["Autostart"], command=self.switch_event,
            variable=self.switch_var_autostart, onvalue=True, offvalue=False
        )
        toggle_settings_autostart.grid(row=1, column=0, padx=12, pady=(12, 0), sticky="w")
        gui_logger.info(f"Autostart toggle set to {self.switch_var_autostart.get()}")

        toggle_bot_access = CTkSwitch(settings_frame, text=self.translations["Bot Access"])
        toggle_bot_access.grid(row=2, column=0, padx=12, pady=(12, 0), sticky="w")

        question_mark = Image.open(self.Ctk_images_path + "question-mark.png")
        question_mark = CTkImage(light_image=question_mark, dark_image=question_mark, size=(25, 25))
        image_widget = CTkLabel(settings_frame, text='', image=question_mark)
        image_widget.grid(row=2, column=1, padx=1, pady=(12, 0), sticky="w")
        Tooltip(image_widget, self.translations["Bot_access_tooltip"])

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

        entry_userid.bind("<Return>", lambda event: self.commit_admin_id(entry_userid))
        entry_userid.bind("<FocusOut>", lambda event: self.save_admin_id(entry_userid))

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

    def commit_admin_id(self, entry: CTkEntry):
        """По Enter ещё и снимаем фокус - чтобы было видно, что поле принято"""
        self.save_admin_id(entry)
        self.right_frame.focus_set()

    def save_admin_id(self, entry: CTkEntry):
        """Сохраняет ID и по Enter, и когда поле теряет фокус.

        Читаем через CTkEntry, а не через event.widget: когда поле пустеет,
        customtkinter кладёт во внутренний Entry текст плейсхолдера, и он уехал бы
        в конфиг вместо id. Обёртка в этом случае возвращает пустую строку
        """
        value = entry.get().strip()
        if value and not value.isdigit():
            gui_logger.warning("Admin ID must be a number, got %r", value)
            return
        if value == self.config.get('Settings', 'admin_id'):
            return

        self.config.set('Settings', 'admin_id', value)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as config_file:
            self.config.write(config_file)
        gui_logger.info("Admin ID saved")


    def add_to_startup(self, file_path: str) -> bool:
        """
        Copy the given file to the user's Startup folder.
        :param file_path: Full path to the executable/script
        :return: True if added successfully, False otherwise
        """
        gui_logger.info("Adding file to startup: %s", file_path)
        try:
            shortcut_name = os.path.splitext(os.path.basename(file_path))[0] + ".lnk"
            destination = os.path.join(self.startup_dir, shortcut_name)
            gui_logger.info("Creating shortcut %s -> %s", destination, file_path)

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
            shortcut_name = os.path.splitext(file_name)[0] + ".lnk"
            target_path = os.path.join(self.startup_dir, shortcut_name)

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
        shortcut.WindowStyle = 7  # Minimized, so the .bat console does not flash at boot
        shortcut.Save()

    def switch_event(self):
        """
        Handle the event when the autostart switch is toggled.
        """
        enabled = bool(self.switch_var_autostart.get())
        gui_logger.info("Autostart switch toggled to %s", enabled)
        self.config.set('Settings', 'autostart', '1' if enabled else '0')
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as config_file:
            self.config.write(config_file)

        if enabled:
            if not self.add_to_startup(AUTOSTART_PATH):
                gui_logger.error("Failed to add file to startup folder")
        else:
            file_name = os.path.basename(AUTOSTART_PATH)
            if not self.remove_from_startup(file_name):
                gui_logger.error("Failed to remove file from startup folder")

    def clear_right_frame_widgets(self):
        """Clear all widgets in the right frame."""
        gui_logger.info("Clearing right frame widgets")
        self.stop_log_tail()
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
