# subscribers.py
from utils.logger import get_logger
import html
from datetime import datetime
from aiogram import Bot
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from configs.config import Config, HEADERS
from utils.GoogleSheets import GoogleSheetsManager

# === Запускаем логирование ===
logger = get_logger(__name__)


# === ХЭНДЛЕР ПОДПИСКИ===
async def handle_new_member(update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager):
    try:
        if (update.old_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and
            update.new_chat_member.status == ChatMemberStatus.MEMBER):

            user = update.new_chat_member.user
            invite = update.invite_link

            user_data = {
                'id': user.id,
                'full_name': html.escape(user.full_name),
                'username': f"@{html.escape(user.username)}" if user.username else "—",
                'language_code': html.escape(user.language_code) if user.language_code else "—",
                'is_premium': getattr(user, 'is_premium', False),
                'is_bot': user.is_bot,
                'last_online': getattr(user, 'last_online_date', '—'),
                'registration_date': getattr(user, 'registration_date', '—')
            }

            join_method = "Direct Join"
            invite_data = {}

            if invite:
                join_method = "Invite Link"
                invite_data = {
                    'link_name': html.escape(invite.name) if invite.name else "—",
                    'link': invite.invite_link,
                    'creator_id': getattr(invite.creator, 'id', '—'),
                    'is_primary': invite.is_primary,
                    'is_revoked': invite.is_revoked,
                    'expire_date': getattr(invite, 'expire_date', '—'),
                    'member_limit': getattr(invite, 'member_limit', '—'),
                    'pending_join_request_count': getattr(invite, 'pending_join_request_count', '—')
                }
            elif update.via_join_request:
                join_method = "Join Request"
                invite_data = {
                    'via_join_request': True,
                    'join_request_date': getattr(update, 'date', '—')
                }

            message = (
                f"👤 <b>Новый подписчик</b>\n"
                f"├ <b>ID:</b> <code>{user_data['id']}</code>\n"
                f"├ <b>Имя:</b> {user_data['full_name']}\n"
                f"├ <b>Username:</b> {user_data['username']}\n"
                f"├ <b>Язык:</b> {user_data['language_code']}\n"
                f"├ <b>Premium:</b> {'✅' if user_data['is_premium'] else '❌'}\n"
                f"├ <b>Бот:</b> {'✅' if user_data['is_bot'] else '❌'}\n"
                f"└ <b>Способ вступления:</b> {join_method}\n"
            )

            if invite_data:
                message += "\n🔗 <b>Информация о ссылке:</b>\n"
                for key, value in invite_data.items():
                    if value not in ['—', None]:
                        message += f"├ <b>{key.replace('_', ' ').title()}:</b> {value}\n"

            additional_info = [
                f"📅 <b>Last Online:</b> {user_data['last_online']}" if user_data['last_online'] != '—' else None,
                f"📅 <b>Registration Date:</b> {user_data['registration_date']}" if user_data['registration_date'] != '—' else None
            ]
            if any(additional_info):
                message += "\n" + "\n".join(filter(None, additional_info))

            '''
            Временно убрал отправку сообщения при подписке юзера (костыль - лень пересобирать конфиги)
            '''
            # await bot.send_message(chat_id=Config.CHANNEL_ID, text=message, parse_mode="HTML")

            full_data = {
                **user_data,
                **invite_data,
                'join_method': join_method,
                'join_date': datetime.utcnow().isoformat(),
                'status': 'active'
            }

            updated = gsheets.update_status_by_id(user.id, 'active')

            if not updated:
                gsheets.ensure_headers(HEADERS)
                gsheets.add_subscriber(HEADERS, full_data)

            logger.info(f"New member: {user.id} via {join_method}")

    except Exception as e:
        logger.error(f"Error in handle_new_member: {e}", exc_info=True)
        
        
# === ХЭНДЛЕР ОТПИСКИ===
async def handle_unsubscribed_member(update: ChatMemberUpdated, bot: Bot, gsheets: GoogleSheetsManager):
    try:
        if (update.old_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED] and
            update.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]):

            user = update.old_chat_member.user
            full_name = html.escape(user.full_name) if user.full_name else "—"
            username = f"@{html.escape(user.username)}" if user.username else "—"

            message = (
                f"🚪 <b>Пользователь отписался</b>\n"
                f"🙍 <b>Имя:</b> {full_name}\n"
                f"💬 <b>Username:</b> {username}\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>"
            )

            if Config.SPREADSHEET_ID and gsheets:
                success = gsheets.update_status_by_id(user.id, 'inactive')
                if success:
                    logger.info(f"User {user.id} marked inactive in sheet")
                else:
                    logger.warning(f"User {user.id} not found in sheet")

            '''
            Временно убрал отправку сообщения при подписке юзера (костыль - лень пересобирать конфиги)
            '''
            # await bot.send_message(chat_id=Config.CHANNEL_ID, text=message, parse_mode="HTML")
            
            logger.info(f"User {user.id} unsubscribed")

    except Exception as e:
        logger.error(f"Error in handle_unsubscribed_member: {e}", exc_info=True)
