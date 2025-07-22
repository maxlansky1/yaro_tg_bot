"""
Точка входа — главный запуск приложения.

Этот модуль содержит точку входа в приложение и вызывает основную функцию main().
"""

import time
from datetime import datetime

from src.utils.logger import get_logger

# Настраиваем логирование
logger = get_logger(__name__)


def log_messages():
    """Функция, которая логирует сообщения разных уровней и выводит текст через print.

    Задает 5 уровней логирования
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.debug(f"ДЕБАГ: А — {now}")
    logger.info(f"ИНФО: Б — {now}")
    logger.warning(f"ВНИМАНИЕ: В — {now}")
    logger.error(f"ERROR: Г — {now}")
    logger.critical(f"CRITICAL: Д — {now}")

    print(f"[{now}] This is usual print function")
    print(f"[{now}] Это необычный принт")


def main():
    """Основная функция, запускающая бесконечный цикл с логами."""
    logger.info("Приложение запущено. Начинаем вывод каждые 10 секунд...")

    try:
        while True:
            log_messages()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Приложение остановлено вручную")


if __name__ == "__main__":
    main()
