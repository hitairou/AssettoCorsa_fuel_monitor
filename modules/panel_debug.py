# modules/panel_debug.py
# Debug window for raw/source audit values.

from modules.display_format import fmt_display_gear, fmt_float, fmt_int, fmt_pct, fmt_rpm
from modules.panel_common import add_label, set_text


WINDOW_SIZE = (330, 390)
PADDING = 8
ROW_H = 12
TITLE_SAFE_TOP = 28

ROWS = [
    ("raw_gear", "Raw Gear"),
    ("display_gear", "Display Gear"),
    ("rpm_source", "RPM Source"),
    ("raw_rpm", "Raw RPM"),
    ("model_rpm", "Model RPM"),
    ("calculated_rpm", "Calculated RPM"),
    ("telemetry_clamped_rpm", "Telemetry Clamped RPM"),
    ("model_raw_delta", "Model-Raw Delta"),
    ("calc_raw_delta", "Calc-Raw Delta"),
    ("rear_tire_circ", "Rear Tire Circ [m]"),
    ("grade_source", "Grade Source"),
    ("vert_idx", "Vertical Axis Index"),
    ("raw_coords", "Raw carCoordinates"),
    ("raw_distance", "Raw distanceTraveled"),
    ("raw_pitch", "Raw pitch"),
    ("demand_load", "Demand Load [%]"),
    ("demand_bsfc_raw", "BSFC Raw [g/kWh]"),
    ("demand_bsfc", "BSFC Corrected [g/kWh]"),
    ("low_load_correction", "Low Load Correction"),
    ("bsfc_map_file", "BSFC Map"),
    ("bsfc_map_min", "BSFC Min"),
    ("demand_fuel_flow", "Demand Fuel Flow [mL/s]"),
    ("cumul_fuel", "Cumul Fuel [mL]"),
    ("measurement_fuel", "Meas Fuel [mL]"),
    ("avg_econ", "Avg Econ [km/L]"),
    ("estimate_source", "Estimate Source"),
    ("lap_progress", "Current Lap Progress [%]"),
    ("restart_count", "Session Restart Count"),
    ("engine_on_ratio", "Session Engine ON Ratio [%]"),
]


def create(window_id):
    labels = {}
    label_w = 176
    value_w = 138
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
        "rpm_source": str(getattr(state, "engine_rpm_source", "")),
        "raw_rpm": fmt_rpm(state.observed_rpm),
        "model_rpm": fmt_rpm(getattr(state, "model_engine_rpm", 0.0)),
        "calculated_rpm": fmt_rpm(getattr(state, "calculated_engine_rpm", 0.0)),
        "telemetry_clamped_rpm": fmt_rpm(getattr(state, "telemetry_clamped_engine_rpm", 0.0)),
        "model_raw_delta": fmt_float(
            getattr(state, "model_engine_rpm", 0.0) - float(state.observed_rpm), 0
        ),
        "calc_raw_delta": fmt_float(
            getattr(state, "calculated_engine_rpm", 0.0) - float(state.observed_rpm), 0
        ),
        "rear_tire_circ": fmt_float(state.vehicle.get("rear_tire_circumference_m", 0.0), 3),
        "grade_source": state.grade_source,
        "vert_idx": str(state.strategy.get("vertical_axis_index", 1)),
        "raw_coords": _fmt_vec3(state.raw_car_coordinates),
        "raw_distance": fmt_float(state.raw_distance_traveled, 1),
        "raw_pitch": fmt_float(state.raw_pitch, 4),
        "demand_load": fmt_pct(state.demand_load_ratio * 100.0, 1),
        "demand_bsfc_raw": fmt_float(getattr(state, "demand_bsfc_raw_g_per_kwh", 0.0), 0),
        "demand_bsfc": fmt_float(state.demand_bsfc_g_per_kwh, 0),
        "low_load_correction": "ON" if getattr(state, "low_load_correction_enabled", False) else "OFF",
        "bsfc_map_file": str(getattr(state, "bsfc_map_file", "")),
        "bsfc_map_min": _fmt_bsfc_min(state),
        "demand_fuel_flow": fmt_float(state.demand_fuel_flow_ml_s, 4),
        "cumul_fuel": fmt_float(state.cumul_fuel_ml, 3),
        "measurement_fuel": fmt_float(state.measurement_fuel_used_ml, 3),
        "avg_econ": fmt_float(state.avg_fuel_econ_km_per_l, 2),
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


def _fmt_bsfc_min(state):
    value = getattr(state, "bsfc_map_min_value", None)
    rpm = getattr(state, "bsfc_map_min_rpm", None)
    load = getattr(state, "bsfc_map_min_load", None)
    if value is None or rpm is None or load is None:
        return "---"
    try:
        return "{0:.0f} @ {1:.0f}/{2:.2f}".format(float(value), float(rpm), float(load))
    except Exception:
        return "---"
