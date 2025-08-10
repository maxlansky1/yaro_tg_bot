"""
Модуль backup.py

Фоновая задача для бота.
Каждый час скачивает Google Таблицу и отправляет её в Telegram администраторам как документ.
Файлы не сохраняются на диск — только во временной памяти.
"""

import asyncio
from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd
from aiogram import Bot
from aiogram.types import BufferedInputFile

from configs.config import Config
from utils.GoogleSheets import GoogleSheetsManager
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)


class GoogleTableBackup:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.backup_interval_seconds = 60 * 60 * 8  # каждые 8 часов 
        self.gsheets = GoogleSheetsManager()
        self.gc = self.gsheets.client  # Уже подключён через GoogleSheetsManager

    async def _download_sheet_to_buffer(self) -> Optional[BytesIO]:
        """
        Скачивает все листы Google Таблицы и сохраняет их в буфер (в память)
        """
        try:
            output = BytesIO()

            spreadsheet = self.gc.open_by_key(Config.SPREADSHEET_ID)

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for sheet in spreadsheet.worksheets():
                    data = sheet.get_all_records()
                    df = pd.DataFrame(data)
                    df.to_excel(
                        writer, index=False, sheet_name=sheet.title[:31]
                    )  # Ограничение длины имени листа

            output.seek(0)  # Перемещаем курсор в начало файла
            logger.info("✅ Таблица успешно загружена в буфер")
            return output

        except Exception as e:
            logger.error(f"❌ Ошибка при подготовке таблицы: {e}", exc_info=True)
            return None

    async def _send_backup_to_admins(self, file_buffer: BytesIO, filename: str):
        """Отправляет Excel-файл всем админам как документ"""
        try:
            input_file = BufferedInputFile(file_buffer.getvalue(), filename=filename)

            for admin_id in Config.TELEGRAM_ADMIN_IDS:
                await self.bot.send_document(chat_id=admin_id, document=input_file)
                logger.info(f"📩 Резервная копия отправлена админу {admin_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка при отправке файла: {e}", exc_info=True)

    async def run_backup_loop(self):
        """Цикл резервного копирования таблицы"""
        logger.info("🔄 Запуск фоновой задачи резервного копирования Google Таблицы")

        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"backup_{timestamp}.xlsx"

            try:
                file_buffer = await self._download_sheet_to_buffer()
                if file_buffer:
                    await self._send_backup_to_admins(file_buffer, filename)
                    logger.info("🧹 Буфер очищен после отправки")
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле бэкапа: {e}", exc_info=True)

            # Ждём перед следующим запуском
            logger.info(
                f"💤 Ожидание {self.backup_interval_seconds // 60} минут до следующего бэкапа..."
            )
            await asyncio.sleep(self.backup_interval_seconds)
