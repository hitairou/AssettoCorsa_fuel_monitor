# modules/panel_gates.py
# Gate editor / control section embedded in Debug.

from modules.display_format import fmt_float, fmt_time_ms
from modules.panel_common import (
    add_button,
    add_label,
    move,
    set_button_state,
    set_color,
    set_text,
    set_visible,
)


PADDING = 8
ROW_H = 14
BTN_H = 20
BTN_GAP = 4
INFO_ROWS = [
    ("mode", "Record Mode"),
    ("state", "Record State"),
    ("start", "Start Gate"),
    ("lap", "Lap Gate"),
    ("finish", "Finish Gate"),
    ("selected", "Selected Gate"),
    ("width", "Gate Width [m]"),
    ("last", "Last Trigger"),
    ("track", "Track Key"),
    ("status", "Status"),
]

BUTTON_ROWS = [
    [("mode_manual", "MODE MAN"), ("mode_semi", "MODE SEMI"), ("toggle_info", "INFO")],
    [("start", "START"), ("stop", "STOP"), ("arm", "ARM")],
    [("cancel", "CANCEL"), ("reset", "RESET"), ("legacy_arm", "LEG ARM")],
    [("reset_gates", "RESET G"), ("save", "SAVE"), ("load", "LOAD")],
    [("set_start", "SET START"), ("set_lap", "SET LAP"), ("set_finish", "SET FIN")],
    [("sel_start", "SEL START"), ("sel_lap", "SEL LAP"), ("sel_finish", "SEL FIN")],
    [("width_dec", "WIDTH -"), ("width_inc", "WIDTH +"), ("clear_selected", "CLEAR")],
]


def create(window_id, callbacks):
    labels = {
        "headers": {},
        "values": {},
        "buttons": {},
    }
    labels["title"] = add_label(window_id, "Gate Control", 0, 0, 160, 16, 11, "left", (0.86, 0.90, 0.98, 1.0))
    for key, title in INFO_ROWS:
        labels["headers"][key] = add_label(window_id, title, 0, 0, 132, ROW_H, 10, "left")
        labels["values"][key] = add_label(window_id, "---", 0, 0, 180, ROW_H, 10, "right")
    for row in BUTTON_ROWS:
        for key, text in row:
            if not key or not text:
                continue
            labels["buttons"][key] = add_button(window_id, text, 0, 0, 94, BTN_H, 10, callback=callbacks.get(key))
    return labels


def total_height(width, info_visible):
    info_h = 18 + (len(INFO_ROWS) * ROW_H if info_visible else 0)
    button_h = len(BUTTON_ROWS) * (BTN_H + BTN_GAP)
    return info_h + 8 + button_h


def update(labels, state, origin_y, width):
    info_visible = bool(getattr(state, "gate_info_visible", True))
    _apply_layout(labels, origin_y, width, info_visible)

    values = {
        "mode": "semi_auto" if state.record_mode == "semi_auto" else "manual",
        "state": str(state.record_state),
        "start": _gate_state_text(state.gates.get("start")),
        "lap": _gate_state_text(state.gates.get("lap")),
        "finish": _gate_state_text(state.gates.get("finish")),
        "selected": str(state.selected_gate_kind or "---"),
        "width": _selected_width_text(state),
        "last": _last_trigger_text(state),
        "track": str(state.track_key or "---"),
        "status": str(state.gate_last_status or "---"),
    }

    for key, value in values.items():
        set_text(labels["values"][key], value)
        set_visible(labels["headers"][key], info_visible)
        set_visible(labels["values"][key], info_visible)

    set_button_state(labels["buttons"]["mode_manual"], state.record_mode == "manual")
    set_button_state(labels["buttons"]["mode_semi"], state.record_mode == "semi_auto")
    set_button_state(labels["buttons"]["toggle_info"], info_visible)
    set_button_state(labels["buttons"]["start"], state.record_mode == "manual" and state.record_state == "running")
    set_button_state(labels["buttons"]["stop"], state.record_mode == "manual" and state.record_state == "finished")
    set_button_state(labels["buttons"]["arm"], state.record_mode == "semi_auto" and state.record_state == "armed")
    set_button_state(labels["buttons"]["cancel"], state.record_state in ("armed", "running"))
    legacy_arm_visible = (
        (not bool(getattr(state, "record_control_enabled", False))) and
        str(getattr(state, "measurement_start_mode", "")) == "manual_arm_then_cross_sf"
    )
    set_visible(labels["buttons"]["legacy_arm"], legacy_arm_visible)
    if legacy_arm_visible:
        set_button_state(labels["buttons"]["legacy_arm"], bool(getattr(state, "measurement_armed", False)))

    selected = state.selected_gate_kind or ""
    set_button_state(labels["buttons"]["sel_start"], selected == "start")
    set_button_state(labels["buttons"]["sel_lap"], selected == "lap")
    set_button_state(labels["buttons"]["sel_finish"], selected == "finish")
    set_button_state(labels["buttons"]["set_start"], bool(state.gates.get("start")))
    set_button_state(labels["buttons"]["set_lap"], bool(state.gates.get("lap")))
    set_button_state(labels["buttons"]["set_finish"], bool(state.gates.get("finish")))

    title_color = (0.86, 0.90, 0.98, 1.0)
    if state.record_state == "running":
        title_color = (0.46, 0.88, 0.56, 1.0)
    elif state.record_state == "armed":
        title_color = (0.96, 0.84, 0.34, 1.0)
    set_color(labels["title"], title_color)


def _apply_layout(labels, origin_y, width, info_visible):
    move(labels["title"], PADDING, origin_y, width - PADDING * 2, 16)

    y = origin_y + 18
    if info_visible:
        for key, _title in INFO_ROWS:
            move(labels["headers"][key], PADDING, y, 132, ROW_H)
            move(labels["values"][key], width - 186, y, 178, ROW_H)
            y += ROW_H

    y += 8
    cols = 3
    btn_w = max(int((width - PADDING * 2 - BTN_GAP * (cols - 1)) / float(cols)), 92)
    for row_idx, row in enumerate(BUTTON_ROWS):
        x = PADDING
        for key, text in row:
            if not key or not text:
                x += btn_w + BTN_GAP
                continue
            move(labels["buttons"][key], x, y + row_idx * (BTN_H + BTN_GAP), btn_w, BTN_H)
            x += btn_w + BTN_GAP


def _gate_state_text(gate):
    if not gate:
        return "NONE"
    if gate.get("enabled", True):
        return "SET"
    return "DISABLED"


def _selected_width_text(state):
    gate = state.gates.get(state.selected_gate_kind or "")
    if not gate:
        return "---"
    return "{0} m".format(fmt_float(gate.get("half_width_m", 0.0), 1))


def _last_trigger_text(state):
    if not state.gate_last_trigger_name:
        return "---"
    sim_t = state.gate_last_trigger_sim_time
    if sim_t is None:
        return str(state.gate_last_trigger_name)
    return "{0} @ {1}".format(state.gate_last_trigger_name, fmt_time_ms(sim_t))
