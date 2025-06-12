from aiogram.types import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    KeyboardButtonPollType
)

keyboard_clear = ReplyKeyboardRemove()


main = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📸 Скриншот"),
            KeyboardButton(text="🤳 Снимок вебки"),
        ],
        [
            KeyboardButton(text="❌ Отмена")
        ],
        [
            KeyboardButton(text="🔒 Заблокировать комп"),
            KeyboardButton(text="🔊 Воспроизвести звук")
        ]
    ],
    resize_keyboard=True,
    selective=True
)
