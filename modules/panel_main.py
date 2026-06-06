# modules/panel_main.py
# Main dashboard window: summary and current live values.

from modules.display_format import (
    fmt_display_gear,
    fmt_float,
    fmt_kj,
    fmt_pct,
    fmt_rpm,
    fmt_sign,
    fmt_time_ms,
    pace_delta_color,
)
from modules.panel_common import (
    add_button,
    add_label,
    set_button_state,
    set_color,
    set_text,
    set_visible,
)
from modules.ui_presets import PRESET_ABBREV


WINDOW_SIZE = (340, 240)
PADDING = 8
GAP = 8
FONT_LABEL = 10
FONT_VALUE = 11
BUTTON_H = 22
ROW_H = 15
TITLE_SAFE_TOP = 28

SUMMARY_ROWS = [
    ("avg_econ", "Avg Fuel Econ [km/L]"),
    ("avg_speed", "Avg Speed [km/h]"),
    ("remaining", "Remaining [mm:ss.s]"),
    ("pace_delta", "Pace Delta [s]"),
    ("fuel_used", "Fuel Used [mL]"),
    ("laps", "Laps Comp/Total"),
]

DETAIL_ROWS = [
    ("rpm", "RPM"),
    ("gear", "Display Gear"),
    ("throttle", "Throttle [%]"),
    ("grade", "Grade [%]"),
    ("engine", "Engine"),
    ("demand_load", "Demand Load [%]"),
    ("current_bsfc", "Current BSFC [g/kWh]"),
    ("fuel_flow", "Fuel Flow [mL/s]"),
    ("fuel_8lap", "8lap Fuel Est [mL]"),
    ("econ_8lap", "8lap Econ Est [km/L]"),
    ("net_energy", "Net Energy Balance [kJ]"),
]


def layout(window_size):
    width, _height = window_size
    left_w = (width - PADDING * 2 - GAP) // 2
    right_w = width - PADDING * 2 - GAP - left_w
    head_y = TITLE_SAFE_TOP + BUTTON_H + 6
    top_y = head_y + 18
    return {
        "left_x": PADDING,
        "right_x": PADDING + left_w + GAP,
        "col_w_left": left_w,
        "col_w_right": right_w,
        "head_y": head_y,
        "top_y": top_y,
    }


def create(window_id, callbacks):
    labels = {}
    geo = layout(WINDOW_SIZE)

    labels["preset_button"] = add_button(
        window_id, "OVR", 8, TITLE_SAFE_TOP, 44, BUTTON_H, callback=callbacks.get("preset")
    )
    labels["arm_button"] = add_button(
        window_id, "ARM", 56, TITLE_SAFE_TOP, 44, BUTTON_H, callback=callbacks.get("arm")
    )
    labels["power_button"] = add_button(
        window_id, "PWR", 104, TITLE_SAFE_TOP, 44, BUTTON_H, callback=callbacks.get("power")
    )
    labels["lap_button"] = add_button(
        window_id, "LAP", 152, TITLE_SAFE_TOP, 44, BUTTON_H, callback=callbacks.get("lap")
    )
    labels["bsfc_button"] = add_button(
        window_id, "BSFC", 200, TITLE_SAFE_TOP, 54, BUTTON_H, callback=callbacks.get("bsfc")
    )
    labels["debug_button"] = add_button(
        window_id, "DBG", 260, TITLE_SAFE_TOP, 44, BUTTON_H, callback=callbacks.get("debug")
    )

    labels["hdr_summary"] = add_label(
        window_id,
        "Summary",
        geo["left_x"],
        geo["head_y"],
        geo["col_w_left"],
        16,
        11,
        "left",
        (0.80, 0.92, 0.80, 1.0),
    )
    labels["hdr_live"] = add_label(
        window_id,
        "Live / Current",
        geo["right_x"],
        geo["head_y"],
        geo["col_w_right"],
        16,
        11,
        "left",
        (0.80, 0.92, 0.80, 1.0),
    )

    _create_rows(labels, window_id, SUMMARY_ROWS, geo["left_x"], geo["top_y"], geo["col_w_left"], 0.67, 10)
    _create_rows(labels, window_id, DETAIL_ROWS, geo["right_x"], geo["top_y"], geo["col_w_right"], 0.74, 9)
    return labels


def update(labels, state):
    total_laps = int(state.vehicle.get("total_laps", 8))
    values = {
        "avg_econ": fmt_float(state.avg_fuel_econ_km_per_l, 2),
        "avg_speed": fmt_float(state.avg_speed_kmh, 1),
        "remaining": fmt_time_ms(state.time_remaining_s),
        "pace_delta": fmt_sign(state.pace_delta_s, 1),
        "fuel_used": fmt_float(state.measurement_fuel_used_ml, 1),
        "laps": "{0}/{1}".format(int(state.laps_completed), total_laps),
        "rpm": fmt_rpm(state.observed_rpm),
        "gear": fmt_display_gear(state.display_gear),
        "throttle": fmt_pct(state.observed_throttle * 100.0, 1),
        "grade": fmt_pct(state.grade_smooth * 100.0, 2),
        "engine": "ON" if state.observed_engine_on else "OFF",
        "demand_load": fmt_pct(state.demand_load_ratio * 100.0, 1),
        "current_bsfc": fmt_float(state.current_bsfc_display_g_per_kwh, 0),
        "fuel_flow": fmt_float(state.current_fuel_flow_display_ml_s, 4, default="0.0000"),
        "fuel_8lap": fmt_float(state.est_8lap_fuel_ml_display, 1),
        "econ_8lap": fmt_float(state.est_8lap_econ_km_per_l_display, 2),
        "net_energy": fmt_kj(state.net_energy_balance_j, 1),
    }

    for key, value in values.items():
        set_text(labels["val_" + key], value)

    set_color(labels["val_pace_delta"], pace_delta_color(state.pace_delta_s))

    set_text(labels["preset_button"], PRESET_ABBREV.get(state.ui_preset, "CST"))
    manual_mode = str(state.measurement_start_mode) == "manual_arm_then_cross_sf"
    set_visible(labels["arm_button"], manual_mode)
    if manual_mode:
        if state.measurement_active:
            set_text(labels["arm_button"], "LIVE")
            set_button_state(labels["arm_button"], True)
        else:
            set_text(labels["arm_button"], "ARM")
            set_button_state(labels["arm_button"], state.measurement_armed)

    set_button_state(labels["power_button"], state.ui_show_power_window)
    set_button_state(labels["lap_button"], state.ui_show_lap_window)
    set_button_state(labels["bsfc_button"], state.ui_show_bsfc_window)
    set_button_state(labels["debug_button"], state.ui_show_debug_window)


def _create_rows(labels, window_id, row_defs, x, y, col_w, label_frac, label_font_size):
    label_w = int(col_w * label_frac)
    value_w = col_w - label_w
    value_x = x + label_w

    for idx, (key, title) in enumerate(row_defs):
        row_y = y + idx * ROW_H
        labels["lbl_" + key] = add_label(
            window_id, title, x, row_y, label_w, ROW_H, label_font_size, "left"
        )
        labels["val_" + key] = add_label(
            window_id, "---", value_x, row_y, value_w, ROW_H, FONT_VALUE, "right"
        )
