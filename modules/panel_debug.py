# modules/panel_debug.py
# Debug window for audit values and gate controls.

from modules.display_format import (
    describe_estimate_source,
    fmt_display_gear,
    fmt_float,
    fmt_pct,
    fmt_rpm,
    fmt_sign,
    fmt_time_ms,
    fmt_unit,
    fmt_vec3_unit,
)
from modules.panel_common import add_label, move, set_color, set_text
from modules import panel_gates


WINDOW_SIZE = (360, 720)
PADDING = 8
ROW_H = 14
TITLE_SAFE_TOP = 28
HEADER_H = 16
VALUE_W = 138
LABEL_W = 184

SECTIONS = [
    ("session", "Session Summary", [
        ("avg_econ", "Avg Fuel Econ [km/L]"),
        ("avg_speed", "Avg Speed [km/h]"),
        ("fuel_used", "Fuel Used [mL]"),
        ("remaining", "Remaining [mm:ss.s]"),
        ("pace_delta", "Pace Delta [s]"),
        ("laps", "Laps Comp/Total"),
        ("restart_count", "Session Restart Count"),
        ("engine_on_ratio", "Session Engine ON Ratio [%]"),
    ]),
    ("live", "Live Vehicle", [
        ("engine", "Engine"),
        ("rpm", "RPM [rpm]"),
        ("gear", "Display Gear"),
        ("throttle", "Throttle [%]"),
        ("grade", "Grade [%]"),
        ("lap_progress", "Current Lap Progress [%]"),
    ]),
    ("demand", "Demand / Model", [
        ("demand_load", "Demand Load [%]"),
        ("current_bsfc", "Current BSFC [g/kWh]"),
        ("fuel_flow", "Fuel Flow [mL/s]"),
        ("demand_bsfc", "Demand BSFC [g/kWh]"),
        ("demand_fuel_flow", "Demand Fuel Flow [mL/s]"),
        ("net_energy", "Net Energy Balance [kJ]"),
    ]),
    ("estimate", "Estimate / Race", [
        ("fuel_8lap", "8lap Fuel Est [mL]"),
        ("econ_8lap", "8lap Econ Est [km/L]"),
        ("estimate_source", "Estimate Source"),
    ]),
    ("raw", "Raw Source", [
        ("raw_gear", "Raw Gear"),
        ("raw_rpm", "Raw RPM [rpm]"),
        ("grade_source", "Grade Source"),
        ("vert_idx", "Vertical Axis Index"),
        ("raw_coords", "Raw carCoordinates [m]"),
        ("raw_distance", "Raw distanceTraveled [m]"),
        ("raw_pitch", "Raw pitch [rad]"),
        ("raw_heading", "Raw heading [rad]"),
    ]),
]


def create(window_id, callbacks=None):
    if callbacks is None:
        callbacks = {}
    labels = {
        "sections": {},
        "gate_section": panel_gates.create(window_id, callbacks),
    }
    for section_key, title, rows in SECTIONS:
        entry = {
            "header": add_label(window_id, title, 0, 0, 220, HEADER_H, 11, "left", (0.84, 0.90, 0.98, 1.0)),
            "rows": {},
        }
        for key, label_text in rows:
            entry["rows"][key] = {
                "label": add_label(window_id, label_text, 0, 0, LABEL_W, ROW_H, 10, "left"),
                "value": add_label(window_id, "---", 0, 0, VALUE_W, ROW_H, 10, "right"),
            }
        labels["sections"][section_key] = entry
    _apply_layout(labels, WINDOW_SIZE)
    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("debug", WINDOW_SIZE))
    _apply_layout(labels, size)

    elapsed = max(state.session_elapsed_time, 0.0)
    on_time = state.session_engine_on_time
    on_ratio = (on_time / elapsed * 100.0) if elapsed > 0.0 else 0.0
    total_laps = int(state.vehicle.get("total_laps", 8))

    values = {
        "avg_econ": fmt_unit(state.avg_fuel_econ_km_per_l, "km/L", digits=2),
        "avg_speed": fmt_unit(state.avg_speed_kmh, "km/h", digits=2),
        "fuel_used": fmt_unit(state.measurement_fuel_used_ml, "mL", digits=2),
        "remaining": fmt_time_ms(state.time_remaining_s),
        "pace_delta": _signed_value(state.pace_delta_s, "s"),
        "laps": "{0}/{1}".format(int(state.laps_completed), total_laps),
        "restart_count": str(int(state.session_restart_count)),
        "engine_on_ratio": fmt_unit(on_ratio, "%", digits=2),
        "engine": "ON" if state.engine_on else "OFF",
        "rpm": "{0} rpm".format(fmt_rpm(state.observed_rpm)),
        "gear": fmt_display_gear(state.display_gear),
        "throttle": fmt_unit(state.observed_throttle * 100.0, "%", digits=1),
        "grade": fmt_unit(state.grade_smooth * 100.0, "%", digits=2),
        "lap_progress": fmt_unit(state.current_lap_progress * 100.0, "%", digits=1),
        "demand_load": fmt_unit(state.demand_load_ratio * 100.0, "%", digits=1),
        "current_bsfc": fmt_unit(state.current_bsfc_display_g_per_kwh, "g/kWh", digits=0),
        "fuel_flow": fmt_unit(state.current_fuel_flow_display_ml_s, "mL/s", digits=4),
        "demand_bsfc": fmt_unit(state.demand_bsfc_g_per_kwh, "g/kWh", digits=0),
        "demand_fuel_flow": fmt_unit(state.demand_fuel_flow_ml_s, "mL/s", digits=4),
        "net_energy": fmt_unit(state.net_energy_balance_j, "kJ", digits=2, scale=1000.0),
        "fuel_8lap": fmt_unit(state.est_8lap_fuel_ml_display, "mL", digits=2),
        "econ_8lap": fmt_unit(state.est_8lap_econ_km_per_l_display, "km/L", digits=2),
        "estimate_source": describe_estimate_source(state.est_8lap_source),
        "raw_gear": str(int(state.raw_gear)),
        "raw_rpm": "{0} rpm".format(fmt_rpm(state.observed_rpm)),
        "grade_source": str(state.grade_source),
        "vert_idx": str(state.strategy.get("vertical_axis_index", 1)),
        "raw_coords": fmt_vec3_unit(state.raw_car_coordinates, unit="m", digits=1),
        "raw_distance": fmt_unit(state.raw_distance_traveled, "m", digits=2),
        "raw_pitch": fmt_unit(state.raw_pitch, "rad", digits=4),
        "raw_heading": fmt_unit(getattr(state, "raw_heading", 0.0), "rad", digits=4),
    }

    for section_key, _title, rows in SECTIONS:
        entry = labels["sections"][section_key]
        for key, _label_text in rows:
            set_text(entry["rows"][key]["value"], values.get(key, "---"))

    set_color(labels["sections"]["live"]["rows"]["engine"]["value"], (0.40, 0.84, 0.52, 1.0) if state.engine_on else (0.72, 0.76, 0.82, 1.0))
    set_color(labels["sections"]["session"]["rows"]["pace_delta"]["value"], (0.94, 0.84, 0.34, 1.0))
    panel_gates.update(labels["gate_section"], state, _gate_origin_y(size), size[0])


def _apply_layout(labels, size):
    width, _height = size
    y = TITLE_SAFE_TOP
    for section_key, _title, rows in SECTIONS:
        entry = labels["sections"][section_key]
        move(entry["header"], PADDING, y, width - PADDING * 2, HEADER_H)
        y += HEADER_H + 2
        for key, _label_text in rows:
            move(entry["rows"][key]["label"], PADDING, y, LABEL_W, ROW_H)
            move(entry["rows"][key]["value"], width - PADDING - VALUE_W, y, VALUE_W, ROW_H)
            y += ROW_H
        y += 8
    panel_gates.update(labels["gate_section"], _DummyState(), _gate_origin_y(size), size[0])


def _gate_origin_y(size):
    y = TITLE_SAFE_TOP
    for _section_key, _title, rows in SECTIONS:
        y += HEADER_H + 2
        y += len(rows) * ROW_H
        y += 8
    return y


def _signed_value(value, unit):
    text = fmt_sign(value, 1, default="---")
    if text == "---":
        return text
    return "{0} {1}".format(text, unit)


class _DummyState(object):
    gate_info_visible = True
    record_mode = "manual"
    record_state = "idle"
    gates = {"start": None, "lap": None, "finish": None}
    selected_gate_kind = "lap"
    gate_last_trigger_name = ""
    gate_last_trigger_sim_time = None
    track_key = "---"
    gate_last_status = "---"
