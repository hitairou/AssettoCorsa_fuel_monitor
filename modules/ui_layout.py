# modules/ui_layout.py
# Compatibility facade for the multi-window UI implementation.

from modules.window_manager import create_windows, update_windows


def create_ui(_app_id=None, state=None):
    if state is None:
        from modules.app_state import state as _state
        state = _state
    return create_windows(state)


def update_all(_labels=None, state=None):
    if state is None:
        from modules.app_state import state as _state
        state = _state
    update_windows(state)


def get_render_callback(_state):
    return None
