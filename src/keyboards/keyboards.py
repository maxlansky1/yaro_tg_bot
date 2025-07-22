# keyboards.py
from aiogram import Bot
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

from configs.config import Config

# Кнопки
btn_create_link = KeyboardButton(text="Создать ссылку")
btn_open_sheet = KeyboardButton(text="Открыть Google Таблицу")

# Основная клавиатура
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[[btn_create_link], [btn_open_sheet]],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# --- Асинхронная inline-клавиатура для выбора канала ---
async def get_channel_selection_keyboard(bot: Bot) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel_id in Config.TELEGRAM_CHANNEL_IDS:
        try:
            chat = await bot.get_chat(channel_id)
            channel_title = chat.title or f"Канал {channel_id}"
        except Exception:
            channel_title = f"Канал {channel_id}"

        keyboard.add(
            InlineKeyboardButton(
                text=channel_title, callback_data=f"select_channel:{channel_id}"
            )
        )

    return keyboard
