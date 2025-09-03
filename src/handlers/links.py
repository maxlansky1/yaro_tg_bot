"""
Модуль управления пригласительными ссылками

Содержит команды:
- /create_link - создать новую пригласительную ссылку
- /revoke_link - отозвать ранее созданную ссылку
"""

from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from configs.config import Config
from keyboards.keyboards import get_approval_type_keyboard
from states.state import CreateLinkStates
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)


# === ХЭНДЛЕРЫ КОМАНД ===
async def cmd_create_link(message: Message, bot: Bot, state: FSMContext):
    """
    Команда `/create_link` — запускает процесс создания новой пригласительной ссылки.

    Только администраторы могут использовать эту команду.
    Пользователю предлагается выбрать канал, затем ввести имя ссылки.
    """

    if message.from_user.id not in Config.TELEGRAM_ADMIN_IDS:
        await message.answer(
            "⛔ У вас нет прав для выполнения этой команды. Обратитесь к администратору"
        )
        return

    try:
        # Формируем клавиатуру с доступными каналами
        kb = InlineKeyboardBuilder()
        for channel_id in Config.TELEGRAM_CHANNEL_IDS:
            try:
                chat = await bot.get_chat(channel_id)
                title = chat.title or str(channel_id)
            except Exception as e:
                logger.warning(
                    f"Не удалось получить информацию о канале {channel_id}: {e}"
                )
                title = str(channel_id)
            kb.add(
                InlineKeyboardButton(
                    text=title, callback_data=f"select_channel:{channel_id}"
                )
            )

        await state.set_state(CreateLinkStates.waiting_for_channel)
        await message.answer(
            "📢 Выберите канал, для которого создать ссылку:",
            reply_markup=kb.as_markup(),
        )

    except Exception as e:
        logger.error(f"Ошибка при выборе канала: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при выборе канала.")


async def handle_channel_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора канала через inline-кнопку.
    Сохраняет выбранный канал в состоянии и запрашивает тип одобрения.
    """
    try:
        channel_id = callback.data.split("select_channel:")[1]
        await state.update_data(selected_channel=channel_id)
        await state.set_state(CreateLinkStates.waiting_for_approval_type)

        await callback.message.edit_text(
            "⚙️ Выберите тип пригласительной ссылки:",
            reply_markup=get_approval_type_keyboard(),
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при обработке выбора канала: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при выборе канала", show_alert=True)


async def handle_approval_type_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора типа одобрения.
    Сохраняет выбор и запрашивает имя ссылки.
    """
    try:
        if callback.data == "back_to_channel_selection":
            # Возвращаем к выбору канала
            from keyboards.keyboards import get_channel_selection_keyboard

            kb = await get_channel_selection_keyboard(callback.bot)
            await state.set_state(CreateLinkStates.waiting_for_channel)
            await callback.message.edit_text(
                "📢 Выберите канал, для которого создать ссылку:", reply_markup=kb
            )
            await callback.answer()
            return

        # Сохраняем тип одобрения
        approval_required = callback.data == "approval_required"
        await state.update_data(approval_required=approval_required)
        await state.set_state(CreateLinkStates.waiting_for_link_name)

        approval_text = (
            "с одобрением администратора" if approval_required else "без одобрения"
        )
        await callback.message.edit_text(
            f"📝 Введите имя для новой пригласительной ссылки ({approval_text}):"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при обработке типа одобрения: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при выборе типа одобрения", show_alert=True)


async def process_link_name(
    message: Message, state: FSMContext, bot: Bot, gsheets: GoogleSheetsManager
):
    """
    Обрабатывает введённое пользователем имя ссылки.

    Создаёт пригласительную ссылку через Telegram API,
    сохраняет данные в Google Таблицу и отправляет ответ пользователю.
    """
    try:
        campaign_name = message.text.strip()
        if not campaign_name:
            await message.answer("ℹ️ Имя ссылки не может быть пустым.")
            return

        data = await state.get_data()
        channel_id = data.get("selected_channel")
        approval_required = data.get("approval_required", True)

        if not channel_id:
            await message.answer("⚠️ Канал не выбран. Пожалуйста, начните заново.")
            return

        await state.clear()

        # Получаем информацию о канале
        chat = await bot.get_chat(channel_id)
        channel_name = chat.title or str(channel_id)

        # Создаём пригласительную ссылку с заданным периодом действия
        expire_date = datetime.now() + timedelta(days=14)
        invite_link = await bot.create_chat_invite_link(
            chat_id=channel_id,  # id канала
            name=campaign_name,  # имя ссылки
            expire_date=expire_date,  # срок действия
            creates_join_request=approval_required,  # нужно ли одобрение админа для вступления
        )

        # Подготавливаем данные для таблицы
        link_data = {
            "Имя ссылки": campaign_name,
            "Ссылка": invite_link.invite_link,
            "Имя канала": channel_name,
            "Дата создания ссылки": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .strftime("%d.%m.%Y %H:%M:%S"),
        }

        # Сохраняем в таблицу
        gsheets.add_invite_link(link_data)

        # Формируем и отправляем ответ
        approval_text = "с одобрением" if approval_required else "без одобрения"
        response = (
            f"🔗 <b>Новая ссылка:</b>\n\n"
            f"📛 <b>Название:</b> <code>{escape(campaign_name)}</code>\n"
            f"📣 <b>Канал:</b> <code>{escape(channel_name)}</code>\n"
            f"🔗 <b>Ссылка:</b> <a href='{invite_link.invite_link}'>{escape(invite_link.invite_link)}</a>"
        )
        await message.answer(response)
        logger.info(
            f"Создана ссылка для канала {channel_id} ({channel_name}): {campaign_name} ({approval_text})"
        )

    except Exception as e:
        logger.error(f"Ошибка при создании ссылки: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при создании ссылки.")
