from typing import Dict, List

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from configs.config import Config


class CallbackData:
    SELECT_CHANNEL = "select_channel"
    ACCEPT_ALL = "accept_all_requests"
    DECLINE_ALL = "decline_all_requests"
    BACK_TO_CHANNELS = "back_to_channel_selection"
    STATS_CHANNEL = "stats_channel"
    STATS_LINK = "stats_link"
    BACK_TO_MAIN_STATS = "back_to_main_stats"
    BACK_TO_CHANNEL_STATS = "back_to_channel_stats"


# Универсальная функция для кнопки "назад"
def get_back_button(callback_data: str, text: str = "↩️ Назад") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=text, callback_data=callback_data)
    return builder.as_markup()


# === Основные текстовые кнопки ===
def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает основную клавиатуру с кнопками"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Создать ссылку")
    builder.button(text="Открыть Google Таблицу")
    builder.button(text="Управление заявками")
    builder.button(text="Управление заявками")
    builder.adjust(2, 2)  # 2 кнопки в первом ряду, 1 во втором
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


# === Inline клавиатуры ===
async def get_channel_selection_keyboard(
    bot: Bot, callback_prefix: str = "select_channel"
) -> InlineKeyboardMarkup:
    """
    Возвращает inline-клавиатуру с выбором каналов.

    Args:
        bot: Экземпляр бота
        callback_prefix: Префикс для callback данных (для разных контекстов)
    """
    builder = InlineKeyboardBuilder()

    for channel_id in Config.TELEGRAM_CHANNEL_IDS:
        try:
            chat = await bot.get_chat(channel_id)
            channel_title = chat.title or f"Канал {channel_id}"
        except Exception:
            channel_title = f"Канал {channel_id}"

        builder.button(
            text=channel_title, callback_data=f"{callback_prefix}:{channel_id}"
        )

    return builder.as_markup()


async def get_channel_statistics_keyboard(
    bot: Bot, callback_prefix: str = "stats_channel"
) -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с выбором каналов для статистики"""
    builder = InlineKeyboardBuilder()

    for channel_id in Config.TELEGRAM_CHANNEL_IDS:
        try:
            chat = await bot.get_chat(channel_id)
            channel_title = chat.title or f"Канал {channel_id}"
        except Exception:
            channel_title = f"Канал {channel_id}"

        builder.button(
            text=channel_title, callback_data=f"{callback_prefix}:{channel_id}"
        )

    builder.button(text="↩️ Назад", callback_data="back_to_main_stats")
    builder.adjust(1)
    return builder.as_markup()


def get_request_management_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для управления заявками"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принять все", callback_data="accept_all_requests")
    builder.button(text="❌ Отклонить все", callback_data="decline_all_requests")
    builder.button(text="↩️ Назад", callback_data="back_to_channel_selection")
    builder.adjust(2, 1)  # 2 кнопки в первом ряду, 1 во втором
    return builder.as_markup()


def get_links_statistics_keyboard(
    links: List[Dict], callback_prefix: str = "stats_link"
) -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру с выбором ссылок для статистики"""
    builder = InlineKeyboardBuilder()

    for i, link in enumerate(links[:15], 1):  # Ограничиваем 15 ссылками
        link_name = link.get("Имя ссылки", f"Ссылка {i}")
        # Используем имя ссылки как идентификатор (можно также использовать саму ссылку)
        callback_data = f"{callback_prefix}:{link_name}"
        builder.button(text=link_name, callback_data=callback_data)

    builder.button(text="↩️ Назад", callback_data="back_to_channel_stats")
    builder.adjust(1)
    return builder.as_markup()


def get_back_to_channels_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру с кнопкой возврата к выбору каналов"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="↩️ Выбрать другой канал", callback_data="back_to_channel_selection"
    )
    return builder.as_markup()


def get_approval_type_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для выбора типа одобрения"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ С одобрением", callback_data="approval_required")
    builder.button(text="❌ Без одобрения", callback_data="approval_not_required")
    builder.button(text="↩️ Назад", callback_data="back_to_channel_selection")
    builder.adjust(2, 1)
    return builder.as_markup()
