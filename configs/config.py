"""
Модуль конфигурации приложения.

Загружает переменные окружения из файла .env и системных переменных,
используя библиотеку `environs`, и предоставляет централизованный доступ
к настройкам через класс `Config`.
"""

from pathlib import Path

from environs import Env

env = Env()
env.read_env()  # читает из .env и системных переменных


class Config:
    """
    Глобальная конфигурация приложения.

    Все параметры считываются из переменных окружения и используются
    для настройки различных аспектов проекта: базы данных, кэша, API,
    телеграм-бота, email, логирования, безопасности и т.д.
    """

    # --- Общие настройки --- (имя приложения, уровень логирования, путь к корню проекта, часовой пояс, кол-во воркеров)
    APP_NAME: str = env.str("APP_NAME", "MyApp")
    LOG_LEVEL: str = env.str("LOG_LEVEL", "INFO")
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    TIMEZONE: str = env.str("TIMEZONE", "UTC")
    MAX_WORKERS: int = env.int("MAX_WORKERS", 5)

    # --- Базовые директории проекта ---
    GITHUB_WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
    CONFIGS_DIR: Path = PROJECT_ROOT / "configs"
    DIAGRAMS_DIR: Path = PROJECT_ROOT / "diagrams"
    DOCS_DIR: Path = PROJECT_ROOT / "docs"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    NOTES_DIR: Path = PROJECT_ROOT / "notes"
    SRC_DIR: Path = PROJECT_ROOT / "src"
    TESTS_DIR: Path = PROJECT_ROOT / "tests"
    TOOLS_DIR: Path = PROJECT_ROOT / "tools"

    # --- Docker ---
    DOCKER_ENV: str = env.str("DOCKER_ENV", "development")
    DOCKER_IMAGE_NAME: str = env.str("DOCKER_IMAGE_NAME", "myapp-image")
    DOCKER_CONTAINER_NAME: str = env.str("DOCKER_CONTAINER_NAME", "myapp-container")

    # --- Telegram Bot ---
    TELEGRAM_BOT_TOKEN: str = env.str("TELEGRAM_BOT_TOKEN", None)
    TELEGRAM_CHAT_ID: str = env.str("TELEGRAM_CHAT_ID", None)
    TELEGRAM_ADMIN_IDS: list[int] = [int(x) for x in env.list("TELEGRAM_ADMIN_IDS", [])]

    # --- Google API ---
    GOOGLE_API_KEY: str = env.str("GOOGLE_API_KEY", None)
    GOOGLE_CLIENT_ID: str = env.str("GOOGLE_CLIENT_ID", None)
    GOOGLE_CLIENT_SECRET: str = env.str("GOOGLE_CLIENT_SECRET", None)
    GOOGLE_REDIRECT_URI: str = env.str("GOOGLE_REDIRECT_URI", None)


config = Config()
