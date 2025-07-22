#src/utils/logger.py
"""
Модуль для настройки кастомного логгера с цветным выводом в консоль и записью в файлы.
"""

import logging
import os
from datetime import datetime

from colorama import Fore, Back, Style, init

# Инициализация colorama для Windows/Linux/macOS
init(autoreset=True)

# Путь к папке с логами
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """
    Цветной форматтер для вывода логов в консоль.
    """

    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Back.RED + Fore.WHITE + Style.BRIGHT,
    }

    def format(self, record):
        log_level = record.levelname
        color = self.COLORS.get(log_level, "")
        self._style._fmt = f"{color}{LOG_FORMAT}{Style.RESET_ALL}"
        return super().format(record)


def get_logger(name=None):
    """
    Возвращает настроенный логгер с указанным именем.

    Пример:
        logger = get_logger(__name__)
    """
    # Настройка корневого логгера
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Минимальный уровень логирования

    # Предотвращаем дублирование логов (если уже есть хэндлеры)
    if logger.hasHandlers():
        return logger

    # --- Консольный вывод ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # --- Логирование в файл ---
    log_file = os.path.join(LOGS_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
