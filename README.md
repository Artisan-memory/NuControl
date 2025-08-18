# NuControl

<div style="display: flex; justify-content: center; align-items: center;">
<img src="README_IMAGES\landscape_nobg.png" alt="landscape" width="512" height="200" style="zoom:70%;" />
</div>


**NuControl** is an application designed to remotely control your PC using a telegram bot, based on the idea of [Tostapunk's project](https://github.com/Tostapunk/PC-Control-telegram-bot)MIT. 

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
| **/check**                 | Check the computer's status                          |                                      |
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

2. **Install the required packages**:
    ```sh
    pip install -r requirements.txt
    ```
    or open `STARTUP_OPEN_ME.bat`

3. **Run the application**:

    ```sh
    python main.py
    ```

    or

    

    Run **NuControl.bat**
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
language = en (str)
autostart = False (bool) 
enabled = False (bool)
admin_id = 123456789 (int)
bot_token = YOUR_BOT_TOKEN (str)
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

---

## TODO (Beta)
- [ ] Refactor the code
- [x] Modify the startup logic between `main.py` and `bot.py`
- [ ] Remove workarounds where they exist
- [ ] Correct logging
- [ ] Complete the commands that are implemented but not working
- [ ] Implement automatic version checking
- [ ] Visualize & rework `/check` 
- [x] Fix autostart functionality
- [ ] Implement proper translations for `En`, `Ru`, etc., using `po`/`mo` files <!-- - [ ] Implement AI voice for the command `/say {argument}` -->
- [ ] Fix question mark tooltip
- [ ] Recall what I should do else

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

## License

This project is distributed under the `GPL-3.0` [LICENSE](./LICENSE) 
