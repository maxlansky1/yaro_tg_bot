"""
Модуль управления заявками на вступление в канал
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from configs.config import Config
from keyboards.keyboards import (
    get_back_to_channels_keyboard,
    get_channel_selection_keyboard,
    get_request_management_keyboard,
)
from states.state import RequestManagementStates
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)

# === Роутер ===
requests_router = Router()


@requests_router.message(F.text == "Управление заявками")
async def handle_manage_requests_button(message: Message, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "Управление заявками".
    Только администраторы могут управлять заявками.
    """
    try:
        # Проверка прав доступа
        if message.from_user.id not in Config.TELEGRAM_ADMIN_IDS:
            await message.answer("⛔ У вас нет доступа")
            return

        # Отображаем выбор канала
        keyboard = await get_channel_selection_keyboard(
            message.bot, callback_prefix="manage_requests_channel"
        )

        await state.set_state(RequestManagementStates.waiting_for_channel_selection)
        await message.answer(
            "📢 Выберите канал для управления заявками:", reply_markup=keyboard
        )

    except Exception as e:
        logger.error(
            f"Ошибка при выборе канала для управления заявками: {e}", exc_info=True
        )
        await message.answer("⚠️ Произошла ошибка при выборе канала")


@requests_router.callback_query(F.data.startswith("manage_requests_channel:"))
async def handle_channel_selection_callback(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор канала для управления заявками через inline-кнопку.
    """
    try:
        # Извлекаем ID канала из callback данных
        channel_id = callback.data.split("manage_requests_channel:")[1]

        # Сохраняем выбранный канал в состоянии
        await state.update_data(selected_channel=channel_id)

        # Получаем список заявок из Google Sheets
        try:
            pending_requests = callback.bot.gsheets.get_pending_requests(channel_id)
        except Exception as e:
            logger.error(f"Ошибка при получении заявок для канала {channel_id}: {e}")
            await callback.answer(
                "⚠️ Ошибка при получении списка заявок", show_alert=True
            )
            return

        # Проверяем наличие заявок
        if not pending_requests:
            keyboard = get_back_to_channels_keyboard()
            await callback.message.edit_text(
                "📭 Нет заявок на вступление в этот канал", reply_markup=keyboard
            )
            return

        # Сохраняем список заявок в состоянии
        await state.update_data(requests_data=pending_requests)

        # Формируем сообщение со списком заявок
        channel_name = (
            pending_requests[0].get("channel_name", channel_id)
            if pending_requests
            else channel_id
        )
        text = f"📋 Заявки на вступление в канал {channel_name}:\n\n"

        for i, req in enumerate(pending_requests, 1):
            username = req.get("username", "")
            name = req.get("name", f"ID: {req.get('id', 'N/A')}")
            text += f"{i}. {name} {username}\n"

        # Отображаем список заявок с кнопками управления
        keyboard = get_request_management_keyboard()

        await state.set_state(RequestManagementStates.managing_requests)
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()

    except Exception as e:
        logger.error(
            f"Ошибка при обработке выбора канала для заявок: {e}", exc_info=True
        )
        await callback.answer("⚠️ Ошибка при обработке заявок", show_alert=True)


@requests_router.callback_query(F.data == "accept_all_requests")
async def handle_accept_all_requests(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает принятие всех заявок.
    """
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data.get("selected_channel")
        requests_data = data.get("requests_data", [])

        # Проверка наличия необходимых данных
        if not channel_id or not requests_data:
            await callback.answer("⚠️ Ошибка: данные не найдены", show_alert=True)
            return

        # Массовое одобрение заявок и перенос в основную таблицу
        success_count = 0
        approved_user_ids = []

        for req in requests_data:
            user_id = int(req.get("id"))
            try:
                # Одобряем заявку через Telegram API
                result = await callback.bot.approve_chat_join_request(
                    chat_id=channel_id, user_id=user_id
                )

                if result:
                    success_count += 1
                    approved_user_ids.append(str(user_id))
                else:
                    logger.error(f"Не удалось одобрить заявку пользователя {user_id}")

            except Exception as e:
                logger.error(f"Ошибка при одобрении заявки пользователя {user_id}: {e}")

        # Переносим одобренные заявки в основную таблицу
        if approved_user_ids:
            try:
                callback.bot.gsheets.move_requests_to_main_sheet(approved_user_ids)
            except Exception as e:
                logger.error(f"Ошибка при переносе заявок в основную таблицу: {e}")

        # Отправляем результат
        keyboard = get_back_to_channels_keyboard()
        await callback.message.edit_text(
            f"✅ Обработано заявок: {success_count} из {len(requests_data)}\n"
            f"{'🔄 Заявки перенесены в основную таблицу' if approved_user_ids else ''}",
            reply_markup=keyboard,
        )

        await state.clear()
        await callback.answer("Заявки обработаны")

    except Exception as e:
        logger.error(f"Ошибка при принятии всех заявок: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при обработке заявок", show_alert=True)


@requests_router.callback_query(F.data == "decline_all_requests")
async def handle_decline_all_requests(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает отклонение всех заявок.
    """
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data.get("selected_channel")
        requests_data = data.get("requests_data", [])

        # Проверка наличия необходимых данных
        if not channel_id or not requests_data:
            await callback.answer("⚠️ Ошибка: данные не найдены", show_alert=True)
            return

        # Массовое отклонение заявок
        success_count = 0
        declined_user_ids = []

        for req in requests_data:
            user_id = int(req.get("id"))
            try:
                # Отклоняем заявку через Telegram API
                result = await callback.bot.decline_chat_join_request(
                    chat_id=channel_id, user_id=user_id
                )

                if result:
                    success_count += 1
                    declined_user_ids.append(str(user_id))
                else:
                    logger.error(f"Не удалось отклонить заявку пользователя {user_id}")

            except Exception as e:
                logger.error(
                    f"Ошибка при отклонении заявки пользователя {user_id}: {e}"
                )

        # Удаляем отклоненные заявки из таблицы заявок
        if declined_user_ids:
            try:
                callback.bot.gsheets.move_requests_to_main_sheet(declined_user_ids)
            except Exception as e:
                logger.error(f"Ошибка при удалении отклоненных заявок: {e}")

        # Отправляем результат
        keyboard = get_back_to_channels_keyboard()
        await callback.message.edit_text(
            f"❌ Отклонено заявок: {success_count} из {len(requests_data)}\n"
            f"{'🔄 Заявки удалены из таблицы' if declined_user_ids else ''}",
            reply_markup=keyboard,
        )

        await state.clear()
        await callback.answer("Заявки отклонены")

    except Exception as e:
        logger.error(f"Ошибка при отклонении всех заявок: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при обработке заявок", show_alert=True)


@requests_router.callback_query(F.data == "back_to_channel_selection")
async def handle_back_to_channel_selection(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает к выбору канала.
    """
    try:
        # Отображаем выбор канала
        keyboard = await get_channel_selection_keyboard(
            callback.bot, callback_prefix="manage_requests_channel"
        )

        await state.set_state(RequestManagementStates.waiting_for_channel_selection)
        await callback.message.edit_text(
            "📢 Выберите канал для управления заявками:", reply_markup=keyboard
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при возврате к выбору канала: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка", show_alert=True)
