"""
Модуль статистики по подпискам

Содержит функционал для получения статистики подписчиков по пригласительным ссылкам
"""

from html import escape
from typing import Dict, List

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from configs.config import Config
from keyboards.keyboards import (
    get_channel_statistics_keyboard,
    get_links_statistics_keyboard,
    get_main_menu_keyboard,
)
from states.state import StatisticsStates
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

logger = get_logger(__name__)


async def cmd_statistics(message: Message, bot: Bot, state: FSMContext):
    """
    Команда статистики по подпискам.
    Отправляет меню выбора канала для просмотра статистики.
    """
    if message.from_user.id not in Config.TELEGRAM_ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для выполнения этой команды")
        return

    try:
        await state.set_state(StatisticsStates.waiting_for_channel_selection)
        kb = await get_channel_statistics_keyboard(bot)

        await message.answer(
            "📊 <b>Статистика по подпискам</b>\n\n"
            "Выберите канал для просмотра статистики:",
            reply_markup=kb,
        )
    except Exception as e:
        logger.error(f"Ошибка при запуске статистики: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при загрузке статистики")


async def handle_channel_selected_for_stats(
    callback: CallbackQuery, state: FSMContext, bot: Bot, gsheets: GoogleSheetsManager
):
    """
    Обработчик выбора канала для статистики.
    Получает список ссылок для выбранного канала и отправляет их для выбора.
    """
    try:
        if callback.data == "back_to_main_stats":
            await state.clear()
            await callback.message.edit_text(
                "👋 Приветствую, администратор! Выберите действие:",
                reply_markup=get_main_menu_keyboard(),
            )
            await callback.answer()
            return

        channel_id = callback.data.split("stats_channel:")[1]

        # Сохраняем выбранный канал
        await state.update_data(selected_channel=channel_id)

        # Получаем информацию о канале
        try:
            chat = await bot.get_chat(channel_id)
            channel_name = chat.title or str(channel_id)
        except Exception:
            channel_name = str(channel_id)

        await state.update_data(channel_name=channel_name)

        # Получаем ссылки для этого канала из Google Sheets
        links = gsheets.get_invite_links_for_channel(channel_name)

        if not links:
            await callback.message.edit_text(
                f"❌ Для канала <b>{escape(channel_name)}</b> пока нет пригласительных ссылок.",
                reply_markup=await get_channel_statistics_keyboard(bot),
            )
            await callback.answer()
            return

        # Сохраняем ссылки
        await state.update_data(channel_links=links)
        await state.set_state(StatisticsStates.waiting_for_link_selection)

        # Отправляем клавиатуру с выбором ссылок
        kb = get_links_statistics_keyboard(links)

        await callback.message.edit_text(
            f"📊 <b>Ссылки для канала:</b> <code>{escape(channel_name)}</code>\n\n"
            "Выберите ссылку для просмотра подписчиков:",
            reply_markup=kb,
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при выборе канала для статистики: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при выборе канала", show_alert=True)


async def handle_link_selected_for_stats(
    callback: CallbackQuery, state: FSMContext, gsheets: GoogleSheetsManager
):
    """
    Обработчик выбора ссылки для получения подписчиков.
    Получает список подписчиков по выбранной ссылке и отправляет их пользователю.
    """
    try:
        if callback.data == "back_to_channel_stats":
            # Возвращаем к выбору каналов
            kb = await get_channel_statistics_keyboard(callback.bot)

            await state.set_state(StatisticsStates.waiting_for_channel_selection)
            await callback.message.edit_text(
                "📊 <b>Статистика по подпискам</b>\n\n"
                "Выберите канал для просмотра статистики:",
                reply_markup=kb,
            )
            await callback.answer()
            return

        # Получаем имя ссылки из callback_data
        selected_link_name = callback.data.split("stats_link:")[1]

        # Получаем подписчиков для этой ссылки
        subscribers = gsheets.get_subscribers_for_link(selected_link_name)

        if not subscribers:
            await callback.message.edit_text(
                f"❌ Для ссылки <b>{escape(selected_link_name)}</b> пока нет подписчиков.",
                reply_markup=get_links_statistics_keyboard(
                    (await state.get_data()).get("channel_links", [])
                ),
            )
            await callback.answer()
            return

        # Формируем сообщение со списком подписчиков
        subscribers_list = format_subscribers_list(subscribers)

        # Отправляем сообщение с подписчиками
        await callback.message.edit_text(
            f"👥 <b>Подписчики по ссылке:</b> <code>{escape(selected_link_name)}</code>\n\n"
            f"{subscribers_list}",
            reply_markup=get_links_statistics_keyboard(
                (await state.get_data()).get("channel_links", [])
            ),
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении подписчиков: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при получении подписчиков", show_alert=True)


def format_subscribers_list(subscribers: List[Dict]) -> str:
    """
    Форматирует список подписчиков для отправки.
    Делает username кликабельными и добавляет пустые строки для удобства чтения.
    """
    if not subscribers:
        return "❌ Нет подписчиков"

    formatted_list = []
    for i, subscriber in enumerate(subscribers, 1):
        username = subscriber.get("username", "").strip()
        user_id = subscriber.get("id", "").strip()

        if username and username != "None":
            # Делаем username кликабельным
            formatted_list.append(f"{i}. @{escape(username)}")
        elif user_id and user_id != "None":
            formatted_list.append(f"{i}. ID: {escape(str(user_id))}")
        else:
            formatted_list.append(f"{i}. Неизвестный пользователь")

        # Добавляем пустую строку для удобства чтения
        formatted_list.append("")

    # Убираем последнюю пустую строку
    if formatted_list and formatted_list[-1] == "":
        formatted_list.pop()

    return "\n".join(formatted_list) if formatted_list else "❌ Нет подписчиков"
