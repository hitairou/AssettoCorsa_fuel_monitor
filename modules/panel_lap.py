# modules/panel_lap.py
# Lap comparison table window.

from modules.display_format import fmt_float, fmt_kj
from modules.panel_common import add_label, set_color, set_text


WINDOW_SIZE = (620, 260)
PADDING = 8
HEADER_H = 16
ROW_H = 20
ROW_COUNT = 8
TITLE_SAFE_TOP = 28
COLS = [
    ("lap", "Lap", 32, "center"),
    ("econ", "Econ", 56, "right"),
    ("fuel", "Fuel", 52, "right"),
    ("speed", "Spd", 54, "right"),
    ("eng", "Eng kJ", 58, "right"),
    ("roll", "Roll", 58, "right"),
    ("aero", "Aero", 58, "right"),
    ("accel", "Accel", 58, "right"),
    ("grade", "Grade", 58, "right"),
    ("restart", "Rst", 42, "right"),
    ("on_ratio", "ON%", 52, "right"),
]


def layout(window_size):
    return {
        "start_x": PADDING,
        "header_y": TITLE_SAFE_TOP,
        "row_y": TITLE_SAFE_TOP + HEADER_H + 4,
    }


def create(window_id):
    labels = {"headers": [], "rows": []}
    geo = layout(WINDOW_SIZE)

    x = geo["start_x"]
    for _key, title, width, align in COLS:
        header = add_label(window_id, title, x, geo["header_y"], width, HEADER_H, 10, align)
        labels["headers"].append(header)
        x += width + 2

    for row_idx in range(ROW_COUNT):
        y = geo["row_y"] + row_idx * ROW_H
        labels["rows"].append(_create_row(window_id, y))
    return labels


def update(labels, state):
    rows = [None] * ROW_COUNT

    if state.measurement_active:
        completed = list(state.lap_rows[-max(ROW_COUNT - 1, 0):])
        offset = max((ROW_COUNT - 1) - len(completed), 0)
        for idx, row in enumerate(completed):
            rows[offset + idx] = row
        rows[-1] = _build_provisional_row(state)
    else:
        completed = list(state.lap_rows[-ROW_COUNT:])
        offset = max(ROW_COUNT - len(completed), 0)
        for idx, row in enumerate(completed):
            rows[offset + idx] = row

    for idx, row in enumerate(rows):
        controls = labels["rows"][idx]
        if row is None:
            _set_row(controls, [""] * len(COLS), (1.0, 1.0, 1.0, 1.0))
            continue

        color = (1.0, 0.95, 0.45, 1.0) if row.get("is_provisional") else (1.0, 1.0, 1.0, 1.0)
        _set_row(controls, _row_values(row), color)


def _create_row(window_id, y):
    controls = []
    x = PADDING
    for _key, _title, width, align in COLS:
        controls.append(add_label(window_id, "", x, y, width, ROW_H, 10, align))
        x += width + 2
    return controls


def _row_values(row):
    lap_text = str(row.get("lap_number", ""))
    if row.get("is_provisional"):
        lap_text = ">{0}".format(lap_text)
    return [
        lap_text,
        fmt_float(row.get("fuel_econ_km_per_l", 0.0), 2),
        fmt_float(row.get("fuel_used_ml", 0.0), 1),
        fmt_float(row.get("avg_speed_kmh", 0.0), 1),
        fmt_kj(row.get("energy_engine_j", 0.0), 1),
        fmt_kj(row.get("energy_roll_j", 0.0), 1),
        fmt_kj(row.get("energy_aero_j", 0.0), 1),
        fmt_kj(row.get("energy_accel_j", 0.0), 1),
        fmt_kj(row.get("energy_grade_j", 0.0), 1),
        str(int(row.get("restart_count", 0))),
        fmt_float(row.get("engine_on_ratio_pct", 0.0), 0),
    ]


def _build_provisional_row(state):
    lap_time = max(state.current_lap_time_s, 1e-9)
    fuel_used = state.current_lap_fuel_ml
    fuel_econ = (state.current_lap_dist_m / fuel_used) if fuel_used > 0.01 else 0.0
    avg_speed = (state.current_lap_dist_m / lap_time) * 3.6 if lap_time > 0.0 else 0.0
    on_ratio = (state.current_lap_engine_on_time / lap_time * 100.0) if lap_time > 0.0 else 0.0
    return {
        "lap_number": state.laps_completed + 1,
        "fuel_econ_km_per_l": fuel_econ,
        "fuel_used_ml": fuel_used,
        "avg_speed_kmh": avg_speed,
        "energy_engine_j": state.current_lap_E_engine_j,
        "energy_roll_j": state.current_lap_E_roll_j,
        "energy_aero_j": state.current_lap_E_aero_j,
        "energy_accel_j": state.current_lap_E_accel_j,
        "energy_grade_j": state.current_lap_E_grade_j,
        "restart_count": state.current_lap_restart_count,
        "engine_on_ratio_pct": on_ratio,
        "is_provisional": True,
    }


def _set_row(controls, values, color):
    for ctrl, value in zip(controls, values):
        set_text(ctrl, value)
        set_color(ctrl, color)
