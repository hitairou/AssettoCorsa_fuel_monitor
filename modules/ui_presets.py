# modules/ui_presets.py
# Display preset definitions for multi-window dashboard layout.

WINDOW_ATTRS = {
    "main": "ui_show_main_window",
    "power": "ui_show_power_window",
    "lap": "ui_show_lap_window",
    "bsfc": "ui_show_bsfc_window",
    "debug": "ui_show_debug_window",
}

PRESETS = {
    "overview": {
        "main": True,
        "power": False,
        "lap": False,
        "bsfc": False,
        "debug": False,
    },
    "analysis": {
        "main": True,
        "power": True,
        "lap": False,
        "bsfc": False,
        "debug": False,
    },
    "lap": {
        "main": True,
        "power": False,
        "lap": True,
        "bsfc": False,
        "debug": False,
    },
    "bsfc": {
        "main": True,
        "power": False,
        "lap": False,
        "bsfc": True,
        "debug": False,
    },
    "debug": {
        "main": True,
        "power": True,
        "lap": False,
        "bsfc": False,
        "debug": True,
    },
}

PRESET_ORDER = ["overview", "analysis", "lap", "bsfc", "debug"]

PRESET_ABBREV = {
    "overview": "OVR",
    "analysis": "ANA",
    "lap": "LAP",
    "bsfc": "BSF",
    "debug": "DBG",
    "custom": "CST",
}


def apply_preset(state, preset_name):
    preset_name = preset_name if preset_name in PRESETS else "overview"
    config = PRESETS[preset_name]
    for window_key, attr in WINDOW_ATTRS.items():
        setattr(state, attr, bool(config.get(window_key, False)))
    state.ui_preset = preset_name
    state.ui_visibility_dirty = True


def cycle_preset(state):
    try:
        idx = PRESET_ORDER.index(state.ui_preset)
    except ValueError:
        idx = -1
    apply_preset(state, PRESET_ORDER[(idx + 1) % len(PRESET_ORDER)])


def set_window_visible(state, window_key, visible):
    attr = WINDOW_ATTRS.get(window_key)
    if attr is None:
        return
    setattr(state, attr, bool(visible))
    sync_preset_name(state)
    state.ui_visibility_dirty = True


def toggle_window(state, window_key):
    attr = WINDOW_ATTRS.get(window_key)
    if attr is None:
        return
    set_window_visible(state, window_key, not bool(getattr(state, attr, False)))


def visibility_map(state):
    return {key: bool(getattr(state, attr, False)) for key, attr in WINDOW_ATTRS.items()}


def sync_preset_name(state):
    flags = visibility_map(state)
    matched = matching_preset(flags)
    state.ui_preset = matched if matched is not None else "custom"


def matching_preset(flags):
    for name, config in PRESETS.items():
        if all(bool(flags.get(key, False)) == bool(config.get(key, False)) for key in WINDOW_ATTRS):
            return name
    return None
