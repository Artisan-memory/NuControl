# NuControl

<div style="display: flex; justify-content: center; align-items: center;">
<img src="README_IMAGES/landscape_nobg.png" alt="landscape" width="512" height="200" style="zoom:70%;" />
</div>


**NuControl** is an application designed to remotely control your PC using a telegram bot, based on the idea of [Tostapunk's project](https://github.com/Tostapunk/PC-Control-telegram-bot) MIT. 

The project currently: **BETA** there are a lot of problems. I will fix them when I will have a time. [CLICK HERE FOR THE GUI](README_IMAGES/gui_image1.png)

___

## Features

- **Remote PC Control**

- **App minimizes in system tray on close/on startup**

- **Logs path in logs dir**

- - easy_log.log it is easy logs for bot
  - gui.log log of gui
  - botLog/telegram_bot.log detailed logs of telegram bot

- **Friend Management**: NOT WORKING. MAYBE IN A FUTURE

  

  ___

  

- ### **Available Commands:**
  
 | Command                      | Description                                          | Example (only if needed)               |
|-----------------------------|------------------------------------------------------|--------------------------------------|
| **/shutdown** / **/s**       | Shut down the computer                               |                                      |
| **/reboot** / **/r**         | Restart the computer                                 |                                      |
| **/hibernate** / **/h**      | Put the computer to sleep                            |                                      |
| **/lock** / **/l**           | Lock the computer                                    |                                      |
| **/logout**                 | Log out of the current user session                  |                                      |
| **/cancel**                 | Cancel any scheduled actions                         |                                      |
| **/check**                 | Check the computer's status, as a chart plus details |                                      |
| **/cpu**                   | Same as /check but more concise                      |                                      |
| **/launch {program_name}**  | Launch the specified program or file                 | /launch notepad                      |
| **/link {url}**             | Open the specified URL in a browser                   | /link google.com                    |
| **/task {process_name}**    | Check if a process is running or stop it              | /task chrome                       |
| **/screen**                | Take a screenshot of the current screen               |                                      |
| **/keyboard** / **/kb**    | Show a keyboard                                       |                                      |
| **/webcam** / **/web** / **/photo** | Capture an image using the webcam             |                                      |
| **/download {file_path}**   | Send a specified file to the user                      | /download C:/Users/Name/Documents/file.txt |
| **/say {text}**            | Play the provided text aloud through speakers          | /say Hello World!                   |
| **/wifi**                  | Display SSID and password of saved Wi-Fi networks      |                                      |
| **/ls**                    | Show contents of the current directory                  |                                      |
| **/cd {directory_path}**    | Change current directory                                | /cd C:/Users/Name/Documents         |
| **/clipboard** or **/clipboard {text}** | Show or update clipboard content            | /clipboard or /clipboard Hello      |

  
  ---
  
  ### **Note:**
  
  You can set a delay for the first four commands (shutdown, reboot, hibernate, lock) by adding a time argument in minutes.
  
  - **Example:**  
    - **/shutdown 2** (Shutdown after 2 minutes)  
    - **/s 2** (Shutdown after 2 minutes)  



---


> ❗ **This project is designed for Windows OS. I won't do it for another OS**




## 	Start

- Python 3.10+

### Installation

1. **Clone the repository**:

    ```sh
    git clone https://github.com/Artisan-memory/NuControl.git
    cd NuControl
    ```

2. **Run it**:

    Double-click **`NuControl.bat`**. On the first run it installs the
    dependencies from `requirements.txt`, then starts the app. Every later run
    (including autostart) skips the install and just launches.

    Prefer to do it by hand?

    ```sh
    pip install -r requirements.txt
    python main.py
    ```

Requires Python 3.10+ on Windows.

---

## Usage

The idea behind this app is simple: it runs quietly in the background and stays out of your way. You’ll probably never notice it’s there. Sure, some of the features might not be used often, but that's okay. The point is that once you launch it, it's always ready when you need it most.

In those rare moments when you need to access your computer remotely, that’s when this app shines. It’s not a replacement for tools like AnyDesk, but it’s a lightweight, easy option when you just need something simple and quick. Launch it once, forget about it, and it’ll be there when you need it. 

Optimization.. uhhh. BETA VERSION!



## Configuration

Configuration settings are stored in `config.ini`. You can manually edit this file.

### Example `config.ini`

```ini
[Settings]
language = en          ; str: en / ru / de
autostart = 0          ; 0 or 1
enabled = 0            ; 0 or 1
admin_id = 123456789   ; int, your Telegram user id
bot_token = YOUR_BOT_TOKEN
control_port = 9999    ; loopback port the GUI uses to stop the bot
```

## Instruction how to add new language

1. Update `initializer_locales.json`:
    - Open `gui/locales/initializer_locales.json`.
    - Add a new entry for your language in the following format:
```json
      {
    "English": "en",
    "Русский": "ru",
    "Deutsch": "de",
    "Your Language Name": "your_language_file_name"
}

```
2. **Create a New Locale File:**
    - Navigate to the `locales` directory.
    - Create a new JSON file named with `your_language_file_name.json`.
    - And that's all!! Just translate the file by your needs, (example you can see in `en.json`/`ru.json`/`de.json`)

### Bot translations (gettext)

The GUI uses the JSON locales above. The Telegram bot's own replies use gettext
catalogs under `src/bot/locales/<lang>/LC_MESSAGES/messages.po`, compiled to
`.mo`. The bot picks its language from the same `language` setting in
`config.ini`. The compiled `.mo` files are committed, so running the bot does not
require Babel.

To change or add bot translations you need Babel (`pip install Babel`):

```sh
# 1. Update the template with any newly wrapped _( ) strings
pybabel extract -F babel.cfg -k _ -k gettext -k lazy_gettext -o src/bot/locales/messages.pot .
# 2. Merge into existing catalogs (or `init -l <lang>` for a new one)
pybabel update -i src/bot/locales/messages.pot -d src/bot/locales -D messages
# 3. Edit the msgstr entries in the .po files, then compile
pybabel compile -d src/bot/locales -D messages
```

---

## TODO (Beta)

- [x] Fix the fatal bot startup crash and the CWD-dependent paths
- [x] Fix autostart, the log viewer, and the tray "Exit" crash
- [x] Bot translations (`en`/`ru`/`de`) via aiogram gettext `.po`/`.mo`
- [x] Clean up `requirements.txt` and remove dead code
- [x] Automatic version checking
- [x] Rework `/check` into a chart plus details
- [x] One screenshot file per monitor, lossless and DPI aware
- [x] Wait for the network at autostart instead of giving up right after boot
- [ ] Implement or remove the Friends / Bot Access feature

**Made with ❤️ by Artisan-memory.** And thanks to **[@tyuniha](https://t.me/tyuniha)** for the arts

---

### Contact and Support:

If you have any questions or suggestions, feel free to reach out:

<div align="center">
    <a href="https://t.me/tegye23"><img src="https://img.shields.io/badge/Telegram-d5d5d5?style=for-the-badge&logo=telegram&logoColor=0A0209" /></a>
   <br>
  <a href="https://discord.com/users/1139606020935667712"><img src="https://img.shields.io/badge/Discord-d5d5d5?style=for-the-badge&logo=discord&logoColor=0A0209" ></a>
  <a href="mailto:dataroofer@gmail.com"><img src="https://img.shields.io/badge/Gmail-d5d5d5?style=for-the-badge&logo=gmail&logoColor=0A0209" /></a> 
</div>
<br>

<img src="https://www.animatedimages.org/data/media/562/animated-line-image-0184.gif" width="1920" />

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

