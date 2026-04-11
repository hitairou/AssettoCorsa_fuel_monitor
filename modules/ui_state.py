# modules/ui_state.py
# Window metadata and persistence helpers for the dashboard UI.

import json
import os


WINDOW_ORDER = ["main", "power", "lap", "bsfc", "debug"]

WINDOW_SPECS = {
    "main": {
        "app_name": "ecoran_fuel_monitor",
        "title": " ",
        "size": (560, 118),
        "position": (640, 780),
        "render": "main",
    },
    "power": {
        "app_name": "ecoran_power_window",
        "title": "Ecoran Power",
        "size": (520, 360),
        "position": (60, 80),
        "render": "power",
    },
    "lap": {
        "app_name": "ecoran_lap_window",
        "title": "Ecoran Lap",
        "size": (760, 238),
        "position": (60, 460),
        "render": "lap",
    },
    "bsfc": {
        "app_name": "ecoran_bsfc_window",
        "title": "Ecoran BSFC",
        "size": (420, 340),
        "position": (610, 80),
        "render": "bsfc",
    },
    "debug": {
        "app_name": "ecoran_debug_window",
        "title": "Ecoran Debug",
        "size": (360, 720),
        "position": (1060, 80),
        "render": None,
    },
}


_SAVE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")),
    "ecoran_fuel_monitor"
)
_SAVE_PATH = os.path.join(_SAVE_DIR, "ui_state.json")


def ensure_defaults(state):
    if not getattr(state, "ui_window_positions", None):
        state.ui_window_positions = {}
    if not getattr(state, "ui_window_sizes", None):
        state.ui_window_sizes = {}

    for key in WINDOW_ORDER:
        if key not in state.ui_window_positions:
            state.ui_window_positions[key] = tuple(WINDOW_SPECS[key]["position"])
        if key not in state.ui_window_sizes:
            state.ui_window_sizes[key] = tuple(WINDOW_SPECS[key]["size"])


def load_saved_state(state):
    ensure_defaults(state)

    if not os.path.isfile(_SAVE_PATH):
        return False

    try:
        with open(_SAVE_PATH, "r") as handle:
            payload = json.load(handle)
    except Exception:
        return False

    positions = payload.get("positions", {})
    sizes = payload.get("sizes", {})

    for key in WINDOW_ORDER:
        pos = positions.get(key)
        size = sizes.get(key)
        if _valid_pair(pos):
            state.ui_window_positions[key] = (int(pos[0]), int(pos[1]))
        if _valid_pair(size):
            state.ui_window_sizes[key] = (int(size[0]), int(size[1]))

    restore_state = True
    try:
        restore_state = bool(int(state.strategy.get("ui.restore_state", 1)))
    except Exception:
        restore_state = True

    if restore_state:
        from modules.ui_presets import WINDOW_ATTRS, sync_preset_name

        visibility = payload.get("visibility", {})
        for key in WINDOW_ORDER:
            attr = WINDOW_ATTRS[key]
            if key in visibility:
                setattr(state, attr, bool(visibility[key]))

        preset_name = str(payload.get("preset", state.ui_preset))
        state.ui_preset = preset_name
        sync_preset_name(state)
        state.ui_visibility_dirty = True

    return True


def save_state(state):
    ensure_defaults(state)

    payload = {
        "preset": getattr(state, "ui_preset", "overview"),
        "positions": {},
        "sizes": {},
        "visibility": {},
    }

    from modules.ui_presets import WINDOW_ATTRS

    for key in WINDOW_ORDER:
        pos = state.ui_window_positions.get(key, WINDOW_SPECS[key]["position"])
        size = state.ui_window_sizes.get(key, WINDOW_SPECS[key]["size"])
        payload["positions"][key] = [int(pos[0]), int(pos[1])]
        payload["sizes"][key] = [int(size[0]), int(size[1])]
        payload["visibility"][key] = bool(getattr(state, WINDOW_ATTRS[key], True))

    try:
        if not os.path.isdir(_SAVE_DIR):
            os.makedirs(_SAVE_DIR)
        with open(_SAVE_PATH, "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return True
    except Exception:
        return False


def _valid_pair(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return False
    try:
        int(value[0])
        int(value[1])
    except Exception:
        return False
    return True
