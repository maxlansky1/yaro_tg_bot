"""
Точка входа в приложение

Содержит инициализацию бота, подключение обработчиков,
настройку FSM состояний, запуск бота.
"""

import asyncio
from functools import partial

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from configs.config import Config
from handlers.buttons import buttons_router
from handlers.links import cmd_create_link, process_link_name
from handlers.requests import requests_router
from handlers.subscribers import handle_new_member, handle_unsubscribed_member
from keyboards.keyboards import get_main_menu_keyboard
from states.state import CreateLinkStates
from utils.backup import GoogleTableBackup
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)


# === Инициализация бота ===
def init_bot(gsheets: GoogleSheetsManager) -> Bot:
    """Создаёт и возвращает экземпляр бота с настроенными свойствами"""
    bot = Bot(
        token=Config.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bot.gsheets = gsheets  # Добавляем gsheets как атрибут бота
    return bot


# === Инициализация хранилища данных ===
def init_storage():
    """Инициализирует FSM хранилище"""
    return MemoryStorage()


# === Инициализация Google Sheets ===
def init_gsheets() -> GoogleSheetsManager:
    """Создаёт и возвращает менеджер для работы с Google Таблицами"""
    try:
        gsheets = GoogleSheetsManager()
        logger.info("✅ GoogleSheetsManager успешно инициализирован")
        return gsheets
    except Exception as e:
        logger.critical(f"❌ Ошибка при инициализации GoogleSheetsManager: {e}")
        raise


# === Регистрация обработчиков подписки/отписки ===
def register_chat_member_handlers(
    dp: Dispatcher, bot: Bot, gsheets: GoogleSheetsManager
):
    """Регистрирует обработчики событий изменения состава чата"""
    dp.chat_member.register(
        partial(handle_new_member, bot=bot, gsheets=gsheets),
        F.old_chat_member.status.in_([ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]),
        F.new_chat_member.status == ChatMemberStatus.MEMBER,
    )

    dp.chat_member.register(
        partial(handle_unsubscribed_member, bot=bot, gsheets=gsheets),
        F.old_chat_member.status.in_(
            [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED]
        ),
        F.new_chat_member.status.in_([ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]),
    )
    logger.info("✅ Обработчики участников чата зарегистрированы")


# === Регистрация команд ===
def register_command_handlers(dp: Dispatcher):
    """Регистрирует обработчики текстовых команд"""

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        """Обработка команды /start"""
        try:
            if message.from_user.id in Config.TELEGRAM_ADMIN_IDS:
                await message.answer(
                    "👋 Приветствую, администратор! Выберите действие:",
                    reply_markup=get_main_menu_keyboard(),
                )
            else:
                await message.answer("⛔ У вас нет доступа к этому боту")
        except Exception as e:
            logger.error(f"Ошибка в cmd_start: {e}", exc_info=True)
            await message.answer("⚠️ Произошла ошибка при обработке команды")

    @dp.message(Command("create_link"))
    async def handle_create_link_command(message: Message, state: FSMContext):
        await cmd_create_link(message, message.bot, state)

    @dp.message(CreateLinkStates.waiting_for_link_name)
    async def handle_link_name_input(message: Message, state: FSMContext):
        await process_link_name(message, state, message.bot, message.bot.gsheets)

    logger.info("✅ Команды зарегистрированы")


# === Запуск бота ===
async def run_bot(bot: Bot, dp: Dispatcher):
    """Запускает бота с текущими настройками"""
    try:
        logger.info("🚀 Бот запускается...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при работе бота: {e}", exc_info=True)
    finally:
        logger.info("🔌 Закрываем соединение с Telegram API...")
        await bot.session.close()


# === Точка входа ===
if __name__ == "__main__":
    # Инициализация компонентов
    gsheets = init_gsheets()
    storage = init_storage()
    bot = init_bot(gsheets)  # Передаем gsheets в бота
    dp = Dispatcher(storage=storage)

    # Подключаем роутеры
    dp.include_router(buttons_router)
    dp.include_router(requests_router)

    # Регистрация обработчиков
    register_chat_member_handlers(dp, bot, gsheets)
    register_command_handlers(dp)

    # === Запуск бота и фоновой задачи ===
    async def main():
        # Создаем и запускаем фоновую задачу
        backup_handler = GoogleTableBackup(bot=bot)
        backup_task = asyncio.create_task(backup_handler.run_backup_loop())

        try:
            logger.info("🤖 Бот готов к работе!")
            await run_bot(bot, dp)
        finally:
            backup_task.cancel()
            await backup_task  # Ждём завершения задачи
            await bot.session.close()

    asyncio.run(main())
