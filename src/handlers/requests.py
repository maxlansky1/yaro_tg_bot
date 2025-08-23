"""
Модуль управления заявками на вступление в канал
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from configs.config import Config
from keyboards.keyboards import (get_back_to_channels_keyboard,
                                 get_channel_selection_keyboard,
                                 get_request_management_keyboard)
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

        # Получаем список заявок на вступление
        try:
            join_requests = await callback.bot.get_chat_join_requests(
                chat_id=channel_id,
                limit=10,  # Ограничиваем для предотвращения переполнения сообщения
            )
        except Exception as e:
            logger.error(f"Ошибка при получении заявок для канала {channel_id}: {e}")
            await callback.answer(
                "⚠️ Ошибка при получении списка заявок", show_alert=True
            )
            return

        # Проверяем наличие заявок
        if not join_requests.requests:
            keyboard = get_back_to_channels_keyboard()
            await callback.message.edit_text(
                "📭 Нет заявок на вступление в этот канал", reply_markup=keyboard
            )
            return

        # Сохраняем список заявок в состоянии
        requests_data = []
        for req in join_requests.requests:
            user = req.user
            requests_data.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                }
            )

        await state.update_data(requests_data=requests_data)

        # Формируем сообщение со списком заявок
        text = "📋 Заявки на вступление в канал:\n\n"
        for i, req in enumerate(requests_data, 1):
            username = f"@{req['username']}" if req["username"] else ""
            text += f"{i}. {req['full_name']} {username}\n"

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

        # Массовое одобрение заявок
        success_count = 0
        for req in requests_data:
            try:
                await callback.bot.approve_chat_join_request(
                    chat_id=channel_id, user_id=req["user_id"]
                )
                success_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при одобрении заявки пользователя {req['user_id']}: {e}"
                )

        # Отправляем результат
        keyboard = get_back_to_channels_keyboard()
        await callback.message.edit_text(
            f"✅ Обработано заявок: {success_count} из {len(requests_data)}",
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
        for req in requests_data:
            try:
                await callback.bot.decline_chat_join_request(
                    chat_id=channel_id, user_id=req["user_id"]
                )
                success_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при отклонении заявки пользователя {req['user_id']}: {e}"
                )

        # Отправляем результат
        keyboard = get_back_to_channels_keyboard()
        await callback.message.edit_text(
            f"❌ Отклонено заявок: {success_count} из {len(requests_data)}",
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
