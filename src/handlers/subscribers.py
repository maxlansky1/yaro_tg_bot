# subscribers.py
import html
from datetime import datetime

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.types import ChatMemberUpdated

from configs.config import HEADERS
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)


# === ХЭНДЛЕР ПОДПИСКИ===
async def handle_new_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    try:
        if (
            update.old_chat_member.status
            in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]
            and update.new_chat_member.status == ChatMemberStatus.MEMBER
        ):
            user = update.new_chat_member.user
            invite = update.invite_link

            user_data = {
                "id": user.id,
                "full_name": html.escape(user.full_name),
                "username": f"@{html.escape(user.username)}" if user.username else "—",
                "language_code": html.escape(user.language_code)
                if user.language_code
                else "—",
                "is_premium": getattr(user, "is_premium", False),
                "is_bot": user.is_bot,
                "last_online": getattr(user, "last_online_date", "—"),
                "registration_date": getattr(user, "registration_date", "—"),
            }

            join_method = "Direct Join"
            invite_data = {}

            if invite:
                join_method = "Invite Link"
                invite_data = {
                    "link_name": html.escape(invite.name) if invite.name else "—",
                    "link": invite.invite_link,
                    "creator_id": getattr(invite.creator, "id", "—"),
                    "is_primary": invite.is_primary,
                    "is_revoked": invite.is_revoked,
                    "expire_date": getattr(invite, "expire_date", "—"),
                    "member_limit": getattr(invite, "member_limit", "—"),
                    "pending_join_request_count": getattr(
                        invite, "pending_join_request_count", "—"
                    ),
                }
            elif update.via_join_request:
                join_method = "Join Request"
                invite_data = {
                    "via_join_request": True,
                    "join_request_date": getattr(update, "date", "—"),
                }

            full_data = {
                **user_data,
                **invite_data,
                "join_method": join_method,
                "join_date": datetime.utcnow().isoformat(),
                "status": "active",
            }

            # Вместо обновления статуса, просто добавляем строку в таблицу
            gsheets.add_subscriber(HEADERS, full_data)

            logger.info(f"New member: {user.id} via {join_method}")

    except Exception as e:
        logger.error(f"Error in handle_new_member: {e}", exc_info=True)


# === ХЭНДЛЕР ОТПИСКИ===
async def handle_unsubscribed_member(
    update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager
):
    try:
        if update.old_chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.RESTRICTED,
        ] and update.new_chat_member.status in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        ]:
            user = update.old_chat_member.user
            full_name = html.escape(user.full_name) if user.full_name else "—"
            username = f"@{html.escape(user.username)}" if user.username else "—"

            # Добавляем запись о том, что пользователь отписался
            full_data = {
                "id": user.id,
                "full_name": full_name,
                "username": username,
                "join_method": "Unsubscribe",
                "join_date": datetime.utcnow().isoformat(),
                "status": "inactive",
            }

            gsheets.add_subscriber(HEADERS, full_data)

            logger.info(f"User {user.id} unsubscribed")

    except Exception as e:
        logger.error(f"Error in handle_unsubscribed_member: {e}", exc_info=True)
