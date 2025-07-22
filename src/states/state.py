# states/state.py

from aiogram.fsm.state import StatesGroup, State

class CreateLinkStates(StatesGroup):
    """Состояния создания ссылки"""
    waiting_for_channel = State()       # Ожидаем выбор канала
    waiting_for_link_name = State()     # Ожидаем название ссылки

class OtherStates(StatesGroup):
    """Дополнительные состояния, если появятся"""
    pass
