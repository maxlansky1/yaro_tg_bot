"""
Хэндлер подписок
"""

import html
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatJoinRequest, ChatMemberUpdated

from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

logger = get_logger(__name__)


def create_user_data_dict(user, invite=None, subscription_type="Direct Join"):
    """Создает стандартный словарь данных пользователя для Google Sheets"""
    return {
        "id": user.id,
        "name": html.escape(user.full_name) if user.full_name else "",
        "username": f"@{html.escape(user.username)}" if user.username else "",
        "Человек": "❌" if user.is_bot else "✅",
        "Имя ссылки": html.escape(invite.name) if invite and invite.name else "",
        "Ссылка": invite.invite_link if invite and invite.invite_link else "",
        "Подписка/отписка": subscription_type,
        "Дата": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .strftime("%d.%m.%Y %H:%M:%S"),
    }


async def handle_new_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    """Обрабатывает события, когда пользователь вступает в канал"""
    try:
        if (
            update.old_chat_member.status
            in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            and update.new_chat_member.status == ChatMemberStatus.MEMBER
        ):
            user = update.new_chat_member.user
            invite = update.invite_link

            # Определяем тип подписки
            subscription_type = "✅" if invite else "Direct Join"

            user_data = create_user_data_dict(user, invite, subscription_type)
            success = gsheets.add_subscriber(user_data)

            if success:
                logger.info(
                    f"Новый подписчик добавлен в таблицу: {user.id} via {subscription_type}"
                )
            else:
                logger.error(
                    f"Не удалось добавить нового подписчика в таблицу: {user.id}"
                )

    except Exception as e:
        logger.error(f"Ошибка в handle_new_member: {e}", exc_info=True)


async def handle_unsubscribed_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    """Обрабатывает события, когда пользователь отписывается от канала"""
    try:
        if update.old_chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        ] and update.new_chat_member.status in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        ]:
            user = update.old_chat_member.user

            # Для отписки invite link не применим
            user_data = create_user_data_dict(user, None, "❌")
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


async def handle_chat_join_request(
    update: ChatJoinRequest, bot: Bot, gsheets: GoogleSheetsManager
):
    """Обрабатывает новые заявки на вступление в канал и сохраняет их в Google Sheets"""
    try:
        user = update.from_user
        chat = update.chat

        # Создаем данные для сохранения в таблицу заявок
        request_data = create_user_data_dict(
            user, update.invite_link, "Заявка на вступление"
        )
        request_data.update(
            {
                "channel_id": str(chat.id),
                "channel_name": html.escape(chat.title) if chat.title else str(chat.id),
            }
        )

        # Сохраняем заявку в лист "Заявки на вступление"
        success = gsheets.add_join_request(request_data)

        if success:
            logger.info(
                f"Новая заявка на вступление сохранена в таблицу: {user.id} в канал {chat.title}"
            )
        else:
            logger.error(
                f"Не удалось сохранить заявку в таблицу: {user.id} в канал {chat.title}"
            )

    except Exception as e:
        logger.error(f"Ошибка в handle_chat_join_request: {e}", exc_info=True)
