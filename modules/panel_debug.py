# modules/panel_debug.py
# Debug window for raw/source audit values.

from modules.display_format import fmt_display_gear, fmt_float, fmt_int, fmt_pct, fmt_rpm
from modules.panel_common import add_label, set_text


WINDOW_SIZE = (280, 220)
PADDING = 8
ROW_H = 12
TITLE_SAFE_TOP = 28

ROWS = [
    ("raw_gear", "Raw Gear"),
    ("display_gear", "Display Gear"),
    ("raw_rpm", "Raw RPM"),
    ("grade_source", "Grade Source"),
    ("vert_idx", "Vertical Axis Index"),
    ("raw_coords", "Raw carCoordinates"),
    ("raw_distance", "Raw distanceTraveled"),
    ("raw_pitch", "Raw pitch"),
    ("demand_load", "Demand Load [%]"),
    ("demand_bsfc", "Demand BSFC [g/kWh]"),
    ("demand_fuel_flow", "Demand Fuel Flow [mL/s]"),
    ("estimate_source", "Estimate Source"),
    ("lap_progress", "Current Lap Progress [%]"),
    ("restart_count", "Session Restart Count"),
    ("engine_on_ratio", "Session Engine ON Ratio [%]"),
]


def create(window_id):
    labels = {}
    label_w = 156
    value_w = 108
    value_x = PADDING + label_w

    for idx, (key, title) in enumerate(ROWS):
        y = TITLE_SAFE_TOP + idx * ROW_H
        labels["lbl_" + key] = add_label(window_id, title, PADDING, y, label_w, ROW_H, 10, "left")
        labels["val_" + key] = add_label(window_id, "---", value_x, y, value_w, ROW_H, 10, "right")
    return labels


def update(labels, state):
    if state.measurement_active:
        elapsed = max(state.measurement_elapsed_time_s, 0.0)
        on_time = state.measurement_engine_on_time_s
    else:
        elapsed = max(state.session_elapsed_time, 0.0)
        on_time = state.session_engine_on_time
    on_ratio = (on_time / elapsed * 100.0) if elapsed > 0.0 else 0.0

    values = {
        "raw_gear": fmt_int(state.raw_gear),
        "display_gear": fmt_display_gear(state.display_gear),
        "raw_rpm": fmt_rpm(state.observed_rpm),
        "grade_source": state.grade_source,
        "vert_idx": str(state.strategy.get("vertical_axis_index", 1)),
        "raw_coords": _fmt_vec3(state.raw_car_coordinates),
        "raw_distance": fmt_float(state.raw_distance_traveled, 1),
        "raw_pitch": fmt_float(state.raw_pitch, 4),
        "demand_load": fmt_pct(state.demand_load_ratio * 100.0, 1),
        "demand_bsfc": fmt_float(state.demand_bsfc_g_per_kwh, 0),
        "demand_fuel_flow": fmt_float(state.demand_fuel_flow_ml_s, 4),
        "estimate_source": str(state.est_8lap_source),
        "lap_progress": fmt_pct(state.current_lap_progress * 100.0, 1),
        "restart_count": str(state.session_restart_count),
        "engine_on_ratio": fmt_float(on_ratio, 1),
    }

    for key, value in values.items():
        set_text(labels["val_" + key], value)


def _fmt_vec3(vec3):
    try:
        return "{0:.1f},{1:.1f},{2:.1f}".format(
            float(vec3[0]), float(vec3[1]), float(vec3[2])
        )
    except Exception:
        return "---"
