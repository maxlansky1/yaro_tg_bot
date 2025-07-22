"""Модуль для настройки кастомного логгера.

Обеспечивает цветной вывод в консоль и запись логов в файлы.

Attributes:
    LOGS_DIR (str): Путь к директории, где будут сохраняться лог-файлы.
    LOG_FORMAT (str): Формат строки лога.
    DATE_FORMAT (str): Формат даты и времени в логах.
"""

import logging
import os
import sys
from datetime import datetime

from colorama import Back, Fore, Style, init

from configs.config import Config

# Инициализация colorama для Windows/Linux/macOS
init(autoreset=True)

# Путь к папке с логами
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Цветной форматтер для вывода логов в консоль.

    Класс расширяет стандартный `logging.Formatter`, добавляя цветовое оформление
    в зависимости от уровня логирования. Поддерживаются уровни DEBUG, INFO,
    WARNING, ERROR и CRITICAL.

    Attributes:
        COLORS (dict): Сопоставление уровней логирования с цветами из библиотеки colorama.
    """

    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Back.RED + Fore.WHITE + Style.BRIGHT,
    }

    def format(self, record):
        """Форматирует запись лога, применяя цвет в зависимости от уровня.

        Цвет устанавливается перед вызовом базового метода `format()` родительского класса.

        Args:
            record (logging.LogRecord): Объект записи лога.

        Returns:
            str: Отформатированная строка лога с цветовым выделением.
        """

        log_level = record.levelname
        color = self.COLORS.get(log_level, "")
        self._style._fmt = f"{color}{LOG_FORMAT}{Style.RESET_ALL}"
        return super().format(record)


def get_logger(name=None):
    """Возвращает настроенный логгер с указанным именем.

    Создаёт и настраивает логгер, который выводит сообщения в консоль с цветовой
    индикацией уровня логирования и записывает информационные и более серьёзные
    сообщения в файл.

    Args:
        name (str, optional): Имя логгера. Если не указано, возвращается корневой логгер.

    Returns:
        logging.Logger: Настроенный экземпляр логгера.
    """

    # Настройка корневого логгера при помощи configs/config.py
    logger = logging.getLogger(name)
    logger.setLevel(Config.LOG_LEVEL)

    # Предотвращаем дублирование логов (если уже есть хэндлеры)
    if logger.hasHandlers():
        return logger

    # --- Консольный вывод ---
    console_handler = logging.StreamHandler(sys.stdout)

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
