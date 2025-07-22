"""
Модуль управления пригласительными ссылками

Содержит команды:
- /create_link - создать новую пригласительную ссылку
- /revoke_link - отозвать ранее созданную ссылку
"""

from utils.logger import get_logger
from datetime import datetime, timedelta
from html import escape

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from configs.config import Config
from states.state import CreateLinkStates
from utils.GoogleSheets import GoogleSheetsManager

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
        await message.answer("⛔ У вас нет прав для выполнения этой команды. Обратитесь к администратору")
        return

    try:
        # Формируем клавиатуру с доступными каналами
        kb = InlineKeyboardBuilder()
        for channel_id in Config.TELEGRAM_CHANNEL_IDS:
            try:
                chat = await bot.get_chat(channel_id)
                title = chat.title or str(channel_id)
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о канале {channel_id}: {e}")
                title = str(channel_id)
            kb.add(InlineKeyboardButton(text=title, callback_data=f"select_channel:{channel_id}"))

        await state.set_state(CreateLinkStates.waiting_for_channel)
        await message.answer("📢 Выберите канал, для которого создать ссылку:", reply_markup=kb.as_markup())

    except Exception as e:
        logger.error(f"Ошибка при выборе канала: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при выборе канала.")


async def handle_channel_selected(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора канала через inline-кнопку.

    Сохраняет выбранный канал в состоянии и запрашивает имя ссылки.
    """
    try:
        channel_id = callback.data.split("select_channel:")[1]
        await state.update_data(selected_channel=channel_id)
        await state.set_state(CreateLinkStates.waiting_for_link_name)

        await callback.message.edit_text("📝 Введите имя для новой пригласительной ссылки:")
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка при обработке выбора канала: {e}", exc_info=True)
        await callback.answer("⚠️ Ошибка при выборе канала", show_alert=True)


async def process_link_name(message: Message, state: FSMContext, bot: Bot, gsheets: GoogleSheetsManager):
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
            chat_id=channel_id,
            name=campaign_name,
            expire_date=expire_date
        )

        # Подготавливаем данные для таблицы
        link_data = {
            "name": campaign_name,
            "invite_link": invite_link.invite_link,
            "creator_id": message.from_user.id,
            "channel_name": channel_name,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_revoked": "FALSE"
        }

        # Сохраняем в таблицу
        gsheets.add_invite_link(link_data)

        # Формируем и отправляем ответ
        response = (
            f"🔗 <b>Новая ссылка:</b>\n\n"
            f"📛 <b>Название:</b> <code>{escape(campaign_name)}</code>\n"
            f"📣 <b>Канал:</b> <code>{escape(channel_name)}</code>\n"
            f"🔗 <b>Ссылка:</b> <code>{escape(invite_link.invite_link)}</code>"
        )
        await message.answer(response)
        logger.info(f"Создана ссылка для канала {channel_id} ({channel_name}): {campaign_name}")

    except Exception as e:
        logger.error(f"Ошибка при создании ссылки: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при создании ссылки.")
