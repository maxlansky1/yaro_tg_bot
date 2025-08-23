# utils/GoogleSheets.py
"""
Модуль для работы с Google Sheets

Содержит класс GoogleSheetsManager — основной интерфейс взаимодействия с Google Таблицей.
Поддерживает работу с несколькими листами, автоматическое создание заголовков,
добавление пользователей и пригласительных ссылок, обновление данных и пр.
"""

# [x] TODO: сделать новые creds для гугл таблицы (Предполагаю, что это уже сделано)

import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

# Импортируем HEADERS
from configs.config import HEADERS, Config  # <-- Изменение 1: Импорт HEADERS
from utils.logger import get_logger

# === Запускаем логирование ===
logger = get_logger(__name__)

# Константы
MAX_RETRIES = 5
API_DELAY = 1.5


class GoogleSheetsManager:
    """
    Класс для работы с Google Таблицей через gspread
    """

    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        self.creds_path = Config.GOOGLE_CREDS_JSON
        self.client = None
        self.sheet = None  # Главный лист (например, "Users")
        self.last_api_call = datetime.min
        self._connect()

    def _wait_for_api_limit(self):
        """Ограничивает частоту вызова API для избежания рейт-лимитов"""
        elapsed = (datetime.now() - self.last_api_call).total_seconds()
        if elapsed < API_DELAY:
            time.sleep(API_DELAY - elapsed)
        self.last_api_call = datetime.now()

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, Exception)),
        before_sleep=lambda _: logger.warning("Повторная попытка после ошибки API"),
    )
    def _connect(self):
        """Подключение к Google Таблице"""
        try:
            self._wait_for_api_limit()
            logger.info("Подключение к Google Sheets API...")

            if not self.creds_path.exists():
                raise FileNotFoundError(
                    f"Файл учетных данных не найден: {self.creds_path}"
                )

            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                str(self.creds_path), self.scope
            )
            self.client = gspread.authorize(credentials)
            spreadsheet = self.client.open_by_key(Config.SPREADSHEET_ID)
            self.sheet = spreadsheet.sheet1  # По умолчанию первый лист

            logger.info("Успешное подключение к Google Таблице")

        except Exception as e:
            logger.error(f"Ошибка подключения: {e}\n{traceback.format_exc()}")
            raise

    def _safe_append_row(self, sheet, row: List[str]) -> bool:
        """Добавляет строку с защитой от ошибок и ограничений API"""
        try:
            self._wait_for_api_limit()
            sheet.append_row(row)
            logger.debug(f"Добавлена строка: {row}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении строки: {str(e)}")
            return False

    def ensure_headers(self, headers: List[str], sheet_title: str = None) -> None:
        """
        Проверяет наличие заголовков в указанном листе.
        Если их нет или они не совпадают — создаёт/обновляет.
        """
        try:
            sheet = self._get_sheet(sheet_title) if sheet_title else self.sheet
            all_values = sheet.get_all_values()
            if not all_values or not all_values[0]:
                sheet.insert_row(headers, index=1)
                logger.info(f"Заголовки созданы на листе '{sheet.title}'")
            elif all_values[0] != headers:
                sheet.delete_row(1)
                sheet.insert_row(headers, index=1)
                logger.warning(f"Заголовки обновлены на листе '{sheet.title}'")
            else:
                logger.debug(f"Заголовки актуальны на листе '{sheet.title}'")
        except Exception as e:
            logger.error(
                f"Ошибка при проверке заголовков: {e}\n{traceback.format_exc()}"
            )

    # Добавляем новый метод в класс GoogleSheetsManager:

    def add_join_request(self, request_data: Dict) -> bool:
        """
        Добавляет новую заявку на вступление в отдельный лист "Заявки на вступление"
        """
        try:
            # Получаем или создаем лист для заявок
            sheet = self._get_sheet("Заявки на вступление")

            # Заголовки для листа заявок (расширяем стандартные заголовки)
            request_headers = HEADERS + ["channel_id", "channel_name"]
            self.ensure_headers(request_headers, "Заявки на вступление")

            # Формируем строку данных
            row = [str(request_data.get(h, "")) for h in request_headers]

            if not self._safe_append_row(sheet, row):
                raise ValueError("Не удалось добавить строку заявки")

            logger.info(f"Заявка добавлена в таблицу: {request_data.get('id')}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при добавлении заявки: {e}\n{traceback.format_exc()}")
            return False

    def get_pending_requests(self, channel_id: str) -> List[Dict]:
        """
        Получает список всех заявок на вступление для указанного канала
        """
        try:
            sheet = self._get_sheet("Заявки на вступление")
            all_values = sheet.get_all_values()

            if not all_values:
                return []

            headers = all_values[0]
            requests_list = []

            # Ищем индекс колонки channel_id
            try:
                channel_id_index = headers.index("channel_id")
            except ValueError:
                logger.error("Колонка channel_id не найдена в листе заявок")
                return []

            # Проходим по всем строкам и фильтруем по channel_id
            for row in all_values[1:]:  # Пропускаем заголовки
                if len(row) > channel_id_index and row[channel_id_index] == channel_id:
                    requests_list.append(dict(zip(headers, row)))

            return requests_list

        except Exception as e:
            logger.error(f"Ошибка при получении заявок: {e}\n{traceback.format_exc()}")
            return []

    def move_requests_to_main_sheet(self, request_ids: List[str]) -> bool:
        """
        Переносит обработанные заявки из листа "Заявки на вступление" в основной лист
        и удаляет их из листа заявок
        """
        try:
            # Получаем листы
            requests_sheet = self._get_sheet("Заявки на вступление")
            main_sheet = self.sheet  # Основной лист

            all_requests_values = requests_sheet.get_all_values()
            if not all_requests_values:
                return True

            headers = all_requests_values[0]
            id_index = headers.index("id") if "id" in headers else -1

            if id_index == -1:
                logger.error("Колонка id не найдена в листе заявок")
                return False

            # Находим строки для удаления
            rows_to_delete = []
            rows_to_move = []

            for i, row in enumerate(all_requests_values[1:], 1):  # Пропускаем заголовки
                if len(row) > id_index and row[id_index] in request_ids:
                    rows_to_delete.append(
                        i + 1
                    )  # +1 потому что get_all_values не включает заголовки, но delete_row использует 1-based индекс
                    # Подготавливаем данные для переноса (без channel_id и channel_name)
                    main_row = [
                        row[headers.index(h)] if h in headers else "" for h in HEADERS
                    ]
                    rows_to_move.append(main_row)

            # Переносим данные в основной лист
            for row in rows_to_move:
                self._safe_append_row(main_sheet, row)

            # Удаляем строки из листа заявок (удаляем с конца, чтобы не сбить индексы)
            for row_index in sorted(rows_to_delete, reverse=True):
                try:
                    requests_sheet.delete_row(row_index)
                except Exception as e:
                    logger.error(f"Ошибка при удалении строки {row_index}: {e}")

            logger.info(f"Перенесено {len(rows_to_move)} заявок в основной лист")
            return True

        except Exception as e:
            logger.error(f"Ошибка при переносе заявок: {e}\n{traceback.format_exc()}")
            return False

    # <-- Изменение 3: Используем HEADERS из config напрямую -->
    def add_subscriber(self, user_data: Dict) -> bool:
        """
        Добавляет нового пользователя в таблицу.
        Проверяет и создает заголовки при необходимости.
        :param user_data: данные пользователя, соответствующие HEADERS
        """
        try:
            if not self.sheet:
                logger.error("Таблица не подключена!")
                return False

            # Проверяем и создаем заголовки, если нужно
            self.ensure_headers(HEADERS)

            # Формируем строку данных в соответствии с HEADERS
            row = [
                str(user_data.get(h, "")) for h in HEADERS
            ]  # <-- Изменение 5: Формирование строки по HEADERS
            logger.info(f"Готовим к добавлению строку: {row}")

            if not self._safe_append_row(self.sheet, row):
                raise ValueError("Не удалось добавить строку")

            return True
        except Exception as e:
            logger.error(
                f"Ошибка при добавлении пользователя: {e}\n{traceback.format_exc()}"
            )
            return False

    def add_invite_link(self, link_data: Dict) -> bool:
        """Добавляет информацию о пригласительной ссылке в отдельный лист "InviteLinks" """
        try:
            sheet = self._get_sheet("InviteLinks")
            headers = [
                "Имя ссылки",
                "Ссылка",
                "Имя канала",
                "Дата создания ссылки",
            ]
            self.ensure_headers(headers, "InviteLinks")
            row = [str(link_data.get(h, "")) for h in headers]
            sheet.append_row(row)
            logger.info(f"Ссылка добавлена в InviteLinks: {row}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении ссылки: {e}\n{traceback.format_exc()}")
            return False

    def get_active_invite_links(self) -> List[Dict]:
        try:
            sheet = self._get_sheet("InviteLinks")
            rows = sheet.get_all_records()
            active_links = []
            for row in rows:
                if str(row.get("is_revoked", "")).lower() not in ["true", "1"]:
                    link = str(row.get("invite_link", "")).strip()
                    name = str(row.get("name", "")).strip()

                    if link and link.startswith("https://t.me/+"):
                        active_links.append(
                            {
                                "name": name,
                                "full_link": link,
                                "clean_link": link.split("/")[-1],
                            }
                        )
            return active_links
        except Exception as e:
            logger.error(f"Ошибка при получении ссылок: {e}")
            return []

    def find_link_row(self, link: str) -> Optional[Dict]:
        """Находит строку в таблице по ссылке"""
        try:
            sheet = self._get_sheet("InviteLinks")
            all_values = sheet.get_all_values()
            headers = all_values[0]
            link_index = headers.index("invite_link")

            # Нормализуем входящую ссылку
            if not link.startswith("https://t.me/+"):
                link = f"https://t.me/{link}"

            for row in all_values[1:]:
                stored_link = str(row[link_index]).strip()
                if stored_link == link:
                    return dict(zip(headers, row))
            return None
        except Exception as e:
            logger.error(f"Ошибка при поиске строки: {e}")
            return None

    def _get_sheet(self, title: str):
        """Возвращает лист по названию или создаёт новый, если его нет"""
        try:
            spreadsheet = self.client.open_by_key(Config.SPREADSHEET_ID)
            return spreadsheet.worksheet(title)
        except WorksheetNotFound:
            logger.warning(f"Лист '{title}' не найден, создаём новый...")
            spreadsheet = self.client.open_by_key(Config.SPREADSHEET_ID)
            worksheet = spreadsheet.add_worksheet(title=title, rows="100", cols="20")
            return worksheet

    def health_check(self) -> bool:
        """Проверяет доступность таблицы"""
        try:
            self._wait_for_api_limit()
            return bool(self.sheet.row_count)
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
