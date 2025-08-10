# src/handlers/subscribers.py
import html
from datetime import datetime

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

# Импортируем HEADERS
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)


# === ХЭНДЛЕР ПОДПИСКИ===
async def handle_new_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    try:
        # Проверяем, что пользователь присоединился
        if (
            update.old_chat_member.status
            in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            and update.new_chat_member.status == ChatMemberStatus.MEMBER
        ):
            user = update.new_chat_member.user
            invite = update.invite_link

            # Создаем базовый словарь данных пользователя, соответствующий HEADERS
            # <-- Изменение 2: Инициализация user_data с полями из HEADERS -->
            user_data = {
                "id": user.id,
                "full_name": html.escape(user.full_name) if user.full_name else "",
                "username": f"@{html.escape(user.username)}" if user.username else "",
                "is_bot": user.is_bot,
                # Поля, связанные с ссылкой, инициализируем пустыми или значениями по умолчанию
                "link_name": "",  # Будет заполнено, если есть invite link
                "link": "",  # Будет заполнено, если есть invite link
                "join_method": "Direct Join",  # По умолчанию Direct Join
                "join_date": datetime.now(datetime.timezone.utc).strftime(
                    "%d.%m.%Y %H:%M:%S"
                ),  # Дата присоединения
            }

            # Обрабатываем данные пригласительной ссылки, если она есть
            if invite:
                user_data["join_method"] = "✅"
                user_data["link_name"] = html.escape(invite.name) if invite.name else ""
                user_data["link"] = invite.invite_link if invite.invite_link else ""

            # Добавляем подписчика в таблицу
            # <-- Изменение 4: Передаем только user_data -->
            success = gsheets.add_subscriber(user_data)

            if success:
                logger.info(
                    f"Новый подписчик добавлен в таблицу: {user.id} via {user_data['join_method']}"
                )
            else:
                logger.error(
                    f"Не удалось добавить нового подписчика в таблицу: {user.id}"
                )

    except Exception as e:
        logger.error(f"Ошибка в handle_new_member: {e}", exc_info=True)


# === ХЭНДЛЕР ОТПИСКИ===
async def handle_unsubscribed_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    try:
        # Проверяем, что пользователь отписался или был забанен
        if update.old_chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        ] and update.new_chat_member.status in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        ]:
            user = update.old_chat_member.user

            # Создаем словарь данных для отписавшегося пользователя, соответствующий HEADERS
            # <-- Изменение 5: Инициализация user_data для отписки -->
            user_data = {
                "id": user.id,
                "full_name": html.escape(user.full_name) if user.full_name else "",
                "username": f"@{html.escape(user.username)}" if user.username else "",
                "is_bot": user.is_bot,
                # Поля, связанные с ссылкой, не применимы при отписке
                "link_name": "",
                "link": "",
                "join_method": "❌",  # Метод "отписка"
                "join_date": datetime.utcnow().isoformat(),  # Дата отписки
            }

            # Добавляем запись об отписке в таблицу
            # <-- Изменение 6: Передаем только user_data -->
            success = gsheets.add_subscriber(user_data)

            if success:
                status_str = (
                    "отписался"
                    if update.new_chat_member.status == ChatMemberStatus.LEFT
                    else "забанен"
                )
                logger.info(
                    f"Пользователь {user.id} {status_str}, запись добавлена в таблицу"
                )
            else:
                logger.error(
                    f"Не удалось добавить запись об отписке пользователя {user.id}"
                )

    except Exception as e:
        logger.error(f"Ошибка в handle_unsubscribed_member: {e}", exc_info=True)
