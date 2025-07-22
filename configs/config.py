"""Модуль для конфигурации"""

import sys
from pathlib import Path

from environs import Env

# Добавляем src в путь импорта
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Инициализация и чтение переменных окружения
env = Env()
env.read_env()  # Читает из .env и системных переменных


class Config:
    # --- Пути и директории ---
    BASE_DIR = Path(__file__).parent.parent

    # --- Telegram Bot ---
    TELEGRAM_BOT_TOKEN: str = env.str("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Отсутствует TELEGRAM_BOT_TOKEN.")

    TELEGRAM_CHANNEL_IDS: list[int] = [
        int(x) for x in env.list("TELEGRAM_CHANNEL_IDS", [])
    ]
    if not TELEGRAM_CHANNEL_IDS:
        raise ValueError("Отсутствуют TELEGRAM_CHANNEL_IDS.")

    TELEGRAM_ADMIN_IDS: list[int] = [int(x) for x in env.list("TELEGRAM_ADMIN_IDS", [])]
    if not TELEGRAM_ADMIN_IDS:
        raise ValueError("Отсутствуют TELEGRAM_ADMIN_IDS.")

    # --- Google Sheets ---
    GOOGLE_CREDS_JSON = BASE_DIR / env.str("GOOGLE_CREDS_JSON")
    if not GOOGLE_CREDS_JSON:
        raise ValueError("Отсутствует GOOGLE_CREDS_JSON.")

    SPREADSHEET_ID: str = env.str("SPREADSHEET_ID")
    if not SPREADSHEET_ID:
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
            raise ValueError(error_msg)


# Инициализация конфигурации
Config.check_credentials()

# Переменные могут быть использованы в приложении:
config = Config()

# === Заголовки таблицы в Google Sheets ===
HEADERS = [
    "id",
    "full_name",
    "username",
    "language_code",
    "is_premium",
    "is_bot",
    "link_name",
    "link",
    "creator_id",
    "is_primary",
    "is_revoked",
    "expire_date",
    "member_limit",
    "pending_join_request_count",
    "via_join_request",
    "join_request_date",
    "join_method",
    "join_date",
    "status",
    "last_online",
    "registration_date",
]
