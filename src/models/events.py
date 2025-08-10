# src/events.py
"""
Модуль для описания событий пользователей в Telegram.

Содержит модель UserEvent, которая представляет собой одну строку
в Google Таблице с информацией о вступлении или выходе пользователя.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer


class UserEvent(BaseModel):
    """
    Модель одного события пользователя (подписка/отписка).

    Соответствует структуре таблицы Google Sheets (см. HEADERS).
    Все поля сериализуются в строковый формат, подходящий для записи в ячейку.
    """

    # === Основная информация о пользователе ===
    id: int = Field(..., description="Telegram ID пользователя")
    full_name: str = Field(..., description="Полное имя (first + last)")
    username: Optional[str] = Field(None, description="Username без @")
    language_code: Optional[str] = Field(
        None, description="Язык интерфейса (ru, en и т.д.)"
    )
    is_premium: bool = Field(False, description="Есть ли Telegram Premium")
    is_bot: bool = Field(False, description="Является ли пользователь ботом")

    # === Информация о ссылке-приглашении ===
    link_name: Optional[str] = Field(None, description="Название ссылки (если есть)")
    link: Optional[str] = Field(None, description="Полная пригласительная ссылка")
    creator_id: Optional[int] = Field(None, description="ID создателя ссылки")
    is_primary: Optional[bool] = Field(
        None, description="Является ли основной ссылкой канала"
    )
    is_revoked: Optional[bool] = Field(None, description="Аннулирована ли ссылка")
    expire_date: Optional[datetime] = Field(
        None, description="Дата истечения срока действия"
    )
    member_limit: Optional[int] = Field(
        None, description="Ограничение по количеству участников"
    )
    pending_join_request_count: Optional[int] = Field(
        None, description="Количество ожидающих запросов на вступление"
    )

    # === Данные о способе вступления ===
    via_join_request: Optional[bool] = Field(
        None, description="Вступил через запрос на вступление"
    )
    join_request_date: Optional[datetime] = Field(
        None, description="Дата отправки запроса на вступление"
    )

    # === Метаданные события ===
    join_method: str = Field(
        "Unknown",
        description="Способ вступления: Invite Link, Join Request, Direct Join",
    )
    join_date: datetime = Field(
        default_factory=datetime.utcnow, description="Дата и время события"
    )
    status: str = Field(..., description="Текущий статус: active, inactive")
    last_online: Optional[datetime] = Field(
        None, description="Последний онлайн (если доступно)"
    )
    registration_date: Optional[datetime] = Field(
        None, description="Дата регистрации в Telegram"
    )

    # --- Сериализация для Google Sheets ---
    @field_serializer("*")
    def serialize_values(self, value):
        """
        Преобразует любое значение в строку для записи в Google Таблицу.
        - None → "—"
        - bool → "✅" / "❌"
        - datetime → ISO-строка (2025-05-08T12:34:56)
        - остальное → str(value)
        """
        if value is None:
            return "—"
        if isinstance(value, bool):
            return "✅" if value else "❌"
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    @classmethod
    def get_headers(cls) -> list[str]:
        """
        Возвращает список заголовков в том же порядке, что и поля модели.
        Совпадает с глобальной константой HEADERS.
        """
        return [
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

    def to_row(self) -> list[str]:
        """
        Преобразует объект события в список значений, готовый к записи в Google Таблицу.
        Порядок значений соответствует `get_headers()`.
        """
        return [getattr(self, field) for field in self.get_headers()]
