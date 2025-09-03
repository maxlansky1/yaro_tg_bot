# states/state.py

from aiogram.fsm.state import State, StatesGroup


class CreateLinkStates(StatesGroup):
    """Состояния создания ссылки"""

    waiting_for_channel = State()  # Ожидаем выбор канала
    waiting_for_link_name = State()  # Ожидаем название ссылки
    waiting_for_approval_type = State()  # Ожидаем выбор типа пригласительной ссылки


class RequestManagementStates(StatesGroup):
    """Состояния управления заявками на подписку"""

    waiting_for_channel_selection = (
        State()
    )  # Ожидаем выбор канала для управления заявками
    managing_requests = State()  # Состояние обработки заявок


class StatisticsStates(StatesGroup):
    """Состояния просмотра статистики по подпискам"""

    waiting_for_channel_selection = State()  # Ожидаем выбор канала для статистики
    waiting_for_link_selection = (
        State()
    )  # Ожидаем выбор ссылки для просмотра подписчиков
