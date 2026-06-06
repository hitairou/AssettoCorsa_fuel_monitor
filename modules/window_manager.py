# modules/window_manager.py
# Multi-window manager for the ecoran dashboard.

import os
import traceback

try:
    import ac
except ImportError:
    class _AcStub(object):
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return 0
            return _noop

    ac = _AcStub()

from modules import bsfc_renderer, gauge_renderer, graph_renderer
from modules import panel_bsfc, panel_debug, panel_lap, panel_main, panel_power
from modules.panel_common import safe_call
from modules.ui_presets import cycle_preset, set_window_visible, toggle_window, visibility_map
from modules.ui_state import WINDOW_ORDER, WINDOW_SPECS, ensure_defaults, load_saved_state, save_state


PANELS = {
    "main": panel_main,
    "power": panel_power,
    "lap": panel_lap,
    "bsfc": panel_bsfc,
    "debug": panel_debug,
}

_state_ref = None
_window_by_app_id = {}
_ui_log_file = os.path.join(os.environ.get("TEMP", "."), "ecoran_fuel_monitor_debug.txt")
_last_render_error = {
    "power": None,
    "bsfc": None,
}


def create_windows(state):
    global _state_ref, _window_by_app_id

    _state_ref = state
    _window_by_app_id = {}

    ensure_defaults(state)
    load_saved_state(state)

    state.ui_windows = {}
    state.labels = {}

    for key in WINDOW_ORDER:
        spec = WINDOW_SPECS[key]
        app_id = ac.newApp(spec["app_name"])
        _configure_window(app_id, key, spec, state)

        if key == "main":
            labels = panel_main.create(app_id, {
                "preset": _on_preset_click,
                "arm": _on_arm_click,
                "power": _on_power_click,
                "lap": _on_lap_click,
                "bsfc": _on_bsfc_click,
                "debug": _on_debug_click,
            })
        else:
            labels = PANELS[key].create(app_id)

        state.ui_windows[key] = {
            "id": app_id,
            "labels": labels,
            "panel": PANELS[key],
        }
        state.labels[key] = labels
        _window_by_app_id[app_id] = key

        safe_call(ac.addOnAppActivatedListener, app_id, _on_app_activated)
        safe_call(ac.addOnAppDismissedListener, app_id, _on_app_dismissed)

        if spec.get("render") == "power":
            safe_call(ac.addRenderCallback, app_id, _render_power)
        elif spec.get("render") == "bsfc":
            safe_call(ac.addRenderCallback, app_id, _render_bsfc)

    _refresh_visibility(state, force=True)
    update_windows(state)
    return state.ui_windows


def update_windows(state):
    if not state.ui_windows:
        return

    if state.ui_visibility_dirty:
        _refresh_visibility(state)

    _sync_runtime_geometry(state)

    for key in WINDOW_ORDER:
        entry = state.ui_windows.get(key)
        if entry is None:
            continue
        try:
            entry["panel"].update(entry["labels"], state)
        except Exception:
            _log_exception("panel update failed: {0}".format(key))

    if state.session_elapsed_time - state.ui_last_layout_save_s >= 5.0:
        state.ui_last_layout_save_s = state.session_elapsed_time
        save_state(state)


def shutdown_windows(state):
    if not state.ui_windows:
        return
    _sync_runtime_geometry(state)
    save_state(state)


def _configure_window(app_id, key, spec, state):
    safe_call(ac.setTitle, app_id, spec["title"])
    safe_call(ac.setIconPosition, app_id, 0, 0)
    safe_call(ac.drawBorder, app_id, 1)
    safe_call(ac.setBackgroundColor, app_id, 0.12, 0.12, 0.12)
    safe_call(ac.setBackgroundOpacity, app_id, 0.72)

    size = tuple(state.ui_window_sizes.get(key, spec["size"]))
    position = tuple(state.ui_window_positions.get(key, spec["position"]))

    safe_call(ac.setSize, app_id, size[0], size[1])
    safe_call(ac.setPosition, app_id, position[0], position[1])


def _on_preset_click(*args):
    if _state_ref is not None:
        cycle_preset(_state_ref)


def _on_power_click(*args):
    if _state_ref is not None:
        toggle_window(_state_ref, "power")


def _on_arm_click(*args):
    if _state_ref is None:
        return
    if str(_state_ref.measurement_start_mode) != "manual_arm_then_cross_sf":
        return
    if _state_ref.measurement_active:
        return
    _state_ref.measurement_armed = not bool(_state_ref.measurement_armed)


def _on_lap_click(*args):
    if _state_ref is not None:
        toggle_window(_state_ref, "lap")


def _on_bsfc_click(*args):
    if _state_ref is not None:
        toggle_window(_state_ref, "bsfc")


def _on_debug_click(*args):
    if _state_ref is not None:
        toggle_window(_state_ref, "debug")


def _on_app_activated(*args):
    key = _window_key_from_args(args)
    if key is None or _state_ref is None:
        return
    set_window_visible(_state_ref, key, True)


def _on_app_dismissed(*args):
    key = _window_key_from_args(args)
    if key is None or _state_ref is None:
        return
    set_window_visible(_state_ref, key, False)


def _window_key_from_args(args):
    if not args:
        return None
    app_id = args[0]
    return _window_by_app_id.get(app_id)


def _refresh_visibility(state, force=False):
    visible = visibility_map(state)
    for key, is_visible in visible.items():
        entry = state.ui_windows.get(key)
        if entry is None:
            continue
        safe_call(ac.setVisible, entry["id"], 1 if is_visible else 0)
    if force or state.ui_visibility_dirty:
        state.ui_visibility_dirty = False
        save_state(state)


def _sync_runtime_geometry(state):
    for key in WINDOW_ORDER:
        entry = state.ui_windows.get(key)
        if entry is None:
            continue

        pos = safe_call(ac.getPosition, entry["id"])
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            state.ui_window_positions[key] = (int(pos[0]), int(pos[1]))

        size = safe_call(ac.getSize, entry["id"])
        if isinstance(size, (list, tuple)) and len(size) >= 2:
            state.ui_window_sizes[key] = (max(int(size[0]), 1), max(int(size[1]), 1))


def _render_power(*args):
    if _state_ref is None:
        return
    try:
        size = _state_ref.ui_window_sizes.get("power", WINDOW_SPECS["power"]["size"])
        geo = panel_power.layout(size)
        graph_renderer.draw(_state_ref, geo["graph_rect"])
        gauge_renderer.draw(_state_ref, geo["bar_rect"], geo["estore_rect"])
    except Exception:
        _log_render_exception("power")


def _render_bsfc(*args):
    if _state_ref is None:
        return
    try:
        size = _state_ref.ui_window_sizes.get("bsfc", WINDOW_SPECS["bsfc"]["size"])
        geo = panel_bsfc.layout(size)
        bsfc_renderer.draw(_state_ref, geo["map_rect"])
    except Exception:
        _log_render_exception("bsfc")


def _log_render_exception(key):
    err = traceback.format_exc()
    if err == _last_render_error.get(key):
        return
    _last_render_error[key] = err
    if _state_ref is not None:
        _state_ref.last_render_error = "render callback failed: {0}".format(key)
    _log_exception("render callback failed: {0}".format(key))


def _log_exception(context):
    try:
        with open(_ui_log_file, "a") as handle:
            handle.write(context + "\n")
            handle.write(traceback.format_exc())
            handle.write("\n")
    except Exception:
        pass
