"""
Модуль обработки кнопок
Содержит хэндлеры для работы с текстовыми командами и inline-кнопками.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from configs.config import Config
from handlers.links import cmd_create_link, handle_channel_selected
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)

# === Роутер ===
buttons_router = Router()


# === ХЭНДЛЕРЫ КНОПОК ===
@buttons_router.message(F.text == "Создать ссылку")
async def handle_create_link_button(message: Message, state: FSMContext):
    """
    Обрабатывает нажатие на текстовую кнопку "Создать ссылку".
    Только администраторы могут создавать ссылки.
    Передаёт управление в `cmd_create_link`.
    """
    try:
        if message.from_user.id in Config.TELEGRAM_ADMIN_IDS:
            await cmd_create_link(message, message.bot, state)
        else:
            await message.answer("⛔ У вас нет доступа")
    except Exception as e:
        logger.error(f"Ошибка при создании ссылки через кнопку: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при создании ссылки")


@buttons_router.message(F.text == "Открыть Google Таблицу")
async def handle_open_sheet_button(message: Message):
    """
    Обрабатывает нажатие на кнопку "Открыть Google Таблицу".
    Отправляет ссылку на таблицу только администраторам.
    """
    try:
        if message.from_user.id not in Config.TELEGRAM_ADMIN_IDS:
            await message.answer("⛔ У вас нет доступа")
            return

        sheet_url = (
            f"https://docs.google.com/spreadsheets/d/{Config.SPREADSHEET_ID}/edit"
        )
        await message.answer(
            f"📎 [Открыть Google Таблицу]({sheet_url})", parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Ошибка при открытии таблицы: {e}", exc_info=True)
        await message.answer("⚠️ Не удалось открыть Google Таблицу")


# === CALLBACK HANDLERS ===
@buttons_router.callback_query(F.data.startswith("select_channel:"))
async def handle_select_channel_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор канала через inline-кнопку.
    Передаёт управление в `handle_channel_selected`.
    """
    try:
        await handle_channel_selected(callback, state)
    except Exception as e:
        logger.error(f"Ошибка при выборе канала: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при выборе канала", show_alert=True)
