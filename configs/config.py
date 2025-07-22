import sys
from environs import Env
from pathlib import Path

# Добавляем src в путь импорта
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Импортируем кастомный логгер
from src.utils.logger import get_logger

# Инициализация и чтение переменных окружения
env = Env()
env.read_env()  # Читает из .env и системных переменных

# Настройка логирования
logger = get_logger(__name__)  # Используем кастомный логгер

# === Заголовки таблицы в Google Sheets ===
HEADERS = [
    "id", "full_name", "username", "language_code",
    "is_premium", "is_bot", "link_name", "link", "creator_id",
    "is_primary", "is_revoked", "expire_date", "member_limit",
    "pending_join_request_count", "via_join_request", "join_request_date",
    "join_method", "join_date", "status", "last_online", "registration_date"
]
"""
Заголовки столбцов в Google Таблице для хранения информации о пользователях.

Полное описание каждого поля приведено выше в комментариях к исходному файлу.
"""

class Config:

    # --- Пути и директории ---
    BASE_DIR = Path(__file__).parent.parent
    """
    Корневая директория проекта.
    """

    # --- Telegram Bot ---
    TELEGRAM_BOT_TOKEN: str = env.str("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        raise ValueError("Отсутствует TELEGRAM_BOT_TOKEN.")
    
    TELEGRAM_CHANNEL_IDS: list[int] = [int(x) for x in env.list("TELEGRAM_CHANNEL_IDS", [])]
    if not TELEGRAM_CHANNEL_IDS:
        logger.error("TELEGRAM_CHANNEL_IDS не указаны!")
        raise ValueError("Отсутствуют TELEGRAM_CHANNEL_IDS.")
    
    TELEGRAM_ADMIN_IDS: list[int] = [int(x) for x in env.list("TELEGRAM_ADMIN_IDS", [])]
    if not TELEGRAM_ADMIN_IDS:
        logger.error("TELEGRAM_ADMIN_IDS не указаны!")
        raise ValueError("Отсутствуют TELEGRAM_ADMIN_IDS.")
    
    # --- Google Sheets ---
    GOOGLE_CREDS_JSON = BASE_DIR / env.str("GOOGLE_CREDS_JSON")
    if not GOOGLE_CREDS_JSON:
        logger.error("GOOGLE_CREDS_JSON не указан!")
        raise ValueError("Отсутствует GOOGLE_CREDS_JSON.")
    
    SPREADSHEET_ID: str = env.str("SPREADSHEET_ID")
    if not SPREADSHEET_ID:
        logger.error("Не указан SPREADSHEET_ID!")
        raise ValueError("Отсутствует SPREADSHEET_ID.")
    
    GOOGLE_DRIVE_PATH: str = env.str("GOOGLE_DRIVE_PATH", "/content/drive/MyDrive/YARO")
    
    # --- Логирование ---
    LOG_LEVEL: str = env.str("LOG_LEVEL", "INFO").upper()

    @classmethod
    def check_credentials(cls):
        """
        Проверка наличия обязательных переменных окружения.
        """
        required_vars = {
            "BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "SPREADSHEET_ID": cls.SPREADSHEET_ID,
            "CHANNEL_IDS": cls.TELEGRAM_CHANNEL_IDS or None,
        }

        missing = [var_name for var_name, value in required_vars.items() if not value]
        if missing:
            error_msg = f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✅ Все обязательные переменные окружения успешно загружены.")

# Инициализация конфигурации
Config.check_credentials()

# Переменные могут быть использованы в приложении:
config = Config()
