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

from modules.gate_model import create_gate
from modules.gate_storage import load_gates, save_gates
from modules import bsfc_renderer, gauge_renderer, graph_renderer
from modules import panel_bsfc, panel_debug, panel_lap, panel_main, panel_power
from modules.panel_common import safe_call
from modules.ui_presets import set_window_visible, toggle_window, visibility_map
from modules.ui_state import WINDOW_ORDER, WINDOW_SPECS, ensure_defaults, load_saved_state, save_state
from modules.record_state_machine import (
    arm_semi_auto,
    cancel_run,
    reset_run,
    set_mode,
    start_manual,
    stop_manual,
)


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
    "main": None,
    "power": None,
    "lap": None,
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
                "power": _on_power_click,
                "lap": _on_lap_click,
                "bsfc": _on_bsfc_click,
                "debug": _on_debug_click,
            })
        elif key == "debug":
            labels = panel_debug.create(app_id, {
                "mode_manual": _on_gate_mode_manual,
                "mode_semi": _on_gate_mode_semi,
                "start": _on_gate_start,
                "stop": _on_gate_stop,
                "arm": _on_gate_arm,
                "cancel": _on_gate_cancel,
                "reset": _on_gate_reset,
                "reset_gates": _on_gate_reset_all,
                "legacy_arm": _on_legacy_arm,
                "set_start": _on_gate_set_start,
                "set_lap": _on_gate_set_lap,
                "set_finish": _on_gate_set_finish,
                "sel_start": _on_gate_select_start,
                "sel_lap": _on_gate_select_lap,
                "sel_finish": _on_gate_select_finish,
                "width_dec": _on_gate_width_dec,
                "width_inc": _on_gate_width_inc,
                "clear_selected": _on_gate_clear_selected,
                "save": _on_gate_save,
                "load": _on_gate_load,
                "toggle_info": _on_gate_toggle_info,
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

        if spec.get("render") == "main":
            safe_call(ac.addRenderCallback, app_id, _render_main)
        elif spec.get("render") == "power":
            safe_call(ac.addRenderCallback, app_id, _render_power)
        elif spec.get("render") == "lap":
            safe_call(ac.addRenderCallback, app_id, _render_lap)
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
    if key == "main":
        safe_call(ac.drawBorder, app_id, 0)
        safe_call(ac.setBackgroundColor, app_id, 0.0, 0.0, 0.0)
        safe_call(ac.setBackgroundOpacity, app_id, 0.0)
    else:
        safe_call(ac.drawBorder, app_id, 1)
        safe_call(ac.setBackgroundColor, app_id, 0.12, 0.12, 0.12)
        safe_call(ac.setBackgroundOpacity, app_id, 0.72)

    size = tuple(state.ui_window_sizes.get(key, spec["size"]))
    position = tuple(state.ui_window_positions.get(key, spec["position"]))

    safe_call(ac.setSize, app_id, size[0], size[1])
    safe_call(ac.setPosition, app_id, position[0], position[1])

def _on_power_click(*args):
    if _state_ref is not None:
        toggle_window(_state_ref, "power")

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
        gauge_renderer.draw(_state_ref, geo["bar_rect"], geo["residual_rect"])
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


def _render_main(*args):
    if _state_ref is None:
        return
    try:
        size = _state_ref.ui_window_sizes.get("main", WINDOW_SPECS["main"]["size"])
        panel_main.render(_state_ref, size)
    except Exception:
        _log_render_exception("main")


def _render_lap(*args):
    if _state_ref is None:
        return
    try:
        size = _state_ref.ui_window_sizes.get("lap", WINDOW_SPECS["lap"]["size"])
        panel_lap.render(_state_ref, size)
    except Exception:
        _log_render_exception("lap")


def _log_render_exception(key):
    err = traceback.format_exc()
    if err == _last_render_error.get(key):
        return
    _last_render_error[key] = err
    _log_exception("render callback failed: {0}".format(key))


def _log_exception(context):
    try:
        with open(_ui_log_file, "a") as handle:
            handle.write(context + "\n")
            handle.write(traceback.format_exc())
            handle.write("\n")
    except Exception:
        pass


def _gate_status(text):
    if _state_ref is not None:
        _state_ref.gate_last_status = str(text)


def _save_gate_state(activate_record_control=True):
    if _state_ref is None or not _state_ref.track_key:
        return False
    ok, reason, path = save_gates(_state_ref.track_key, _state_ref.record_mode, _state_ref.gates)
    _state_ref.gate_storage_path = path
    if ok:
        _state_ref.record_control_enabled = bool(activate_record_control)
        _gate_status("Saved gates for {0}".format(_state_ref.track_key))
    else:
        _gate_status("Gate save failed: {0}".format(reason))
    return ok


def _load_gate_state():
    if _state_ref is None or not _state_ref.track_key:
        return False
    ok, payload, reason, path = load_gates(_state_ref.track_key)
    _state_ref.gate_storage_path = path
    if ok:
        _state_ref.gates["start"] = payload["gates"].get("start")
        _state_ref.gates["lap"] = payload["gates"].get("lap")
        _state_ref.gates["finish"] = payload["gates"].get("finish")
        _state_ref.record_mode = str(payload.get("record_mode", "manual"))
        _state_ref.record_control_enabled = any(
            _state_ref.gates.get(kind) for kind in ("start", "lap", "finish")
        )
        _gate_status("Loaded gates for {0}".format(_state_ref.track_key))
    else:
        _gate_status("Gate load warning: {0}".format(reason))
    return ok


def _set_gate(kind):
    if _state_ref is None:
        return
    if _state_ref.record_state == "running":
        _gate_status("Gate edit disabled while running")
        return
    _state_ref.selected_gate_kind = kind
    _state_ref.gates[kind] = create_gate(
        kind,
        _state_ref.raw_car_coordinates,
        _state_ref.last_forward_world,
        half_width_m=4.0,
    )
    _state_ref.record_control_enabled = True
    _save_gate_state()


def _select_gate(kind):
    if _state_ref is None:
        return
    _state_ref.selected_gate_kind = kind
    _gate_status("Selected {0} gate".format(kind))


def _adjust_selected_gate(delta):
    if _state_ref is None:
        return
    kind = _state_ref.selected_gate_kind
    gate = _state_ref.gates.get(kind)
    if not gate:
        _gate_status("No selected gate")
        return
    width = max(1.0, min(20.0, float(gate.get("half_width_m", 4.0)) + float(delta)))
    gate["half_width_m"] = width
    _save_gate_state()


def _on_gate_mode_manual(*args):
    if _state_ref is None:
        return
    _gate_status(set_mode(_state_ref, "manual")[1])


def _on_gate_mode_semi(*args):
    if _state_ref is None:
        return
    _gate_status(set_mode(_state_ref, "semi_auto")[1])


def _on_gate_start(*args):
    if _state_ref is None:
        return
    ok, message = start_manual(_state_ref)
    _gate_status(message)
    if ok:
        _state_ref.pending_record_command = "start_manual"


def _on_gate_stop(*args):
    if _state_ref is None:
        return
    ok, message = stop_manual(_state_ref)
    _gate_status(message)
    if ok:
        _state_ref.pending_record_command = "stop_manual"


def _on_gate_arm(*args):
    if _state_ref is None:
        return
    ok, message = arm_semi_auto(_state_ref)
    _gate_status(message)


def _on_gate_cancel(*args):
    if _state_ref is None:
        return
    ok, message = cancel_run(_state_ref)
    _gate_status(message)
    if ok:
        _state_ref.pending_record_command = "cancel_run"


def _on_gate_reset(*args):
    if _state_ref is None:
        return
    ok, message = reset_run(_state_ref)
    _gate_status(message)
    if ok:
        _state_ref.pending_record_command = "reset_run"


def _on_gate_reset_all(*args):
    if _state_ref is None:
        return
    _state_ref.gates["start"] = None
    _state_ref.gates["lap"] = None
    _state_ref.gates["finish"] = None
    _state_ref.selected_gate_kind = "lap"
    _state_ref.record_mode = "manual"
    _state_ref.record_control_enabled = False
    _save_gate_state(activate_record_control=False)


def _on_gate_set_start(*args):
    _set_gate("start")


def _on_gate_set_lap(*args):
    _set_gate("lap")


def _on_gate_set_finish(*args):
    _set_gate("finish")


def _on_gate_select_start(*args):
    _select_gate("start")


def _on_gate_select_lap(*args):
    _select_gate("lap")


def _on_gate_select_finish(*args):
    _select_gate("finish")


def _on_gate_width_dec(*args):
    _adjust_selected_gate(-0.5)


def _on_gate_width_inc(*args):
    _adjust_selected_gate(0.5)


def _on_gate_clear_selected(*args):
    if _state_ref is None:
        return
    kind = _state_ref.selected_gate_kind
    _state_ref.gates[kind] = None
    _save_gate_state()


def _on_gate_save(*args):
    _save_gate_state()


def _on_gate_load(*args):
    _load_gate_state()


def _on_gate_toggle_info(*args):
    if _state_ref is None:
        return
    _state_ref.gate_info_visible = not bool(_state_ref.gate_info_visible)


def _on_legacy_arm(*args):
    if _state_ref is None:
        return
    if str(_state_ref.measurement_start_mode) != "manual_arm_then_cross_sf":
        return
    _state_ref.measurement_armed = not bool(_state_ref.measurement_armed)
    _gate_status("Legacy ARM {0}".format("ON" if _state_ref.measurement_armed else "OFF"))
