from .socket import ConnectionManager
from .state import AppState

state = AppState()
manager = ConnectionManager()


def get_state() -> AppState:
    return state


def get_manager() -> ConnectionManager:
    return manager
