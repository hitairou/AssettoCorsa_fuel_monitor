# modules/panel_lap.py
# Lap comparison table window.

try:
    import ac
    import acsys
    _GL_LINES = acsys.GL.Lines
    _GL_QUADS = acsys.GL.Quads
    _AC_OK = True
except (ImportError, AttributeError):
    _AC_OK = False
    _GL_LINES = 1
    _GL_QUADS = 7

from modules.display_format import fmt_float, fmt_kj, heat_good_bad_color
from modules.panel_common import add_label, move, set_color, set_text


WINDOW_SIZE = (760, 238)
PADDING = 8
HEADER_H = 18
ROW_H = 18
ROW_COUNT = 8
TITLE_SAFE_TOP = 28
COL_GAP = 2
COLS = [
    ("lap", "Lap", 48, "center", None),
    ("econ", "Econ [km/L]", 72, "right", True),
    ("fuel", "Fuel [mL]", 64, "right", False),
    ("restart", "RST", 42, "right", None),
    ("on_ratio", "ON [%]", 54, "right", False),
    ("lap_time", "Lap Time [s]", 72, "right", False),
    ("speed", "SPD [km/h]", 68, "right", True),
    ("eng", "Eng [kJ]", 60, "right", False),
    ("roll", "Roll [kJ]", 60, "right", False),
    ("aero", "Aero [kJ]", 60, "right", False),
    ("accel", "Accel [kJ]", 62, "right", False),
    ("grade", "Grade [kJ]", 62, "right", False),
]


def layout(window_size):
    return {
        "start_x": PADDING,
        "header_y": TITLE_SAFE_TOP,
        "row_y": TITLE_SAFE_TOP + HEADER_H + 4,
    }


def create(window_id):
    labels = {"headers": [], "rows": [], "window_id": window_id}
    _build_controls(window_id, labels)
    _apply_layout(labels, WINDOW_SIZE)
    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("lap", WINDOW_SIZE))
    _apply_layout(labels, size)

    rows = _visible_rows(state)
    metrics = _metric_ranges(state.lap_rows)

    for idx, row in enumerate(rows):
        controls = labels["rows"][idx]
        if row is None:
            _set_row(controls, [""] * len(COLS), [(1.0, 1.0, 1.0, 0.0)] * len(COLS))
            continue
        values = _row_values(row)
        colors = _row_colors(row, metrics)
        _set_row(controls, values, colors)


def render(state, window_size):
    if not _AC_OK:
        return

    geo = layout(window_size)
    table_w = _table_width()
    table_h = HEADER_H + 4 + ROW_COUNT * ROW_H
    x = geo["start_x"]
    y = geo["header_y"]

    _draw_rect(x, y, table_w, table_h, (0.06, 0.07, 0.09, 0.82))
    _draw_rect(x, y, table_w, HEADER_H, (0.12, 0.14, 0.17, 0.86))

    rows = _visible_rows(state)
    for idx, row in enumerate(rows):
        if row and row.get("is_provisional"):
            row_y = geo["row_y"] + idx * ROW_H
            _draw_rect(x, row_y, table_w, ROW_H, (0.38, 0.30, 0.08, 0.30))
        elif idx % 2 == 1:
            row_y = geo["row_y"] + idx * ROW_H
            _draw_rect(x, row_y, table_w, ROW_H, (0.10, 0.11, 0.14, 0.22))

    _draw_grid(geo)


def _build_controls(window_id, labels):
    for _key, title, width, align, _better in COLS:
        labels["headers"].append(add_label(window_id, title, 0, 0, width, HEADER_H, 9, align))
    for _row_idx in range(ROW_COUNT):
        row = []
        for _key, _title, width, align, _better in COLS:
            row.append(add_label(window_id, "", 0, 0, width, ROW_H, 9, align))
        labels["rows"].append(row)


def _apply_layout(labels, window_size):
    geo = layout(window_size)
    x = geo["start_x"]
    for idx, (_key, _title, width, _align, _better) in enumerate(COLS):
        move(labels["headers"][idx], x, geo["header_y"], width, HEADER_H)
        for row_idx in range(ROW_COUNT):
            move(labels["rows"][row_idx][idx], x, geo["row_y"] + row_idx * ROW_H, width, ROW_H)
        x += width + COL_GAP


def _visible_rows(state):
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
    return rows


def _row_values(row):
    lap_text = str(row.get("lap_number", ""))
    if row.get("is_provisional"):
        lap_text = "LIVE {0}".format(lap_text)
    return [
        lap_text,
        fmt_float(row.get("fuel_econ_km_per_l", 0.0), 2),
        fmt_float(row.get("fuel_used_ml", 0.0), 2),
        str(int(row.get("restart_count", 0))),
        fmt_float(row.get("engine_on_ratio_pct", 0.0), 2),
        fmt_float(row.get("lap_time_s", 0.0), 2),
        fmt_float(row.get("avg_speed_kmh", 0.0), 2),
        fmt_kj(row.get("energy_engine_j", 0.0), 2),
        fmt_kj(row.get("energy_roll_j", 0.0), 2),
        fmt_kj(row.get("energy_aero_j", 0.0), 2),
        fmt_kj(row.get("energy_accel_j", 0.0), 2),
        fmt_kj(row.get("energy_grade_j", 0.0), 2),
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
        "lap_time_s": lap_time,
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


def _metric_ranges(rows):
    metrics = {}
    keys = [
        ("fuel_econ_km_per_l", True),
        ("fuel_used_ml", False),
        ("engine_on_ratio_pct", False),
        ("lap_time_s", False),
        ("avg_speed_kmh", True),
        ("energy_engine_j", False),
        ("energy_roll_j", False),
        ("energy_aero_j", False),
        ("energy_accel_j", False),
        ("energy_grade_j", False),
    ]
    completed = [row for row in rows if isinstance(row, dict) and not row.get("is_provisional")]
    for key, higher_is_better in keys:
        values = []
        for row in completed:
            try:
                values.append(float(row.get(key, 0.0)))
            except Exception:
                pass
        if values:
            metrics[key] = (min(values), max(values), higher_is_better)
    return metrics


def _row_colors(row, metrics):
    neutral = (0.92, 0.94, 0.98, 1.0)
    provisional = (1.0, 0.96, 0.72, 1.0)
    if row.get("is_provisional"):
        return [provisional] * len(COLS)

    color_map = {
        "econ": _metric_color("fuel_econ_km_per_l", row, metrics),
        "fuel": _metric_color("fuel_used_ml", row, metrics),
        "on_ratio": _metric_color("engine_on_ratio_pct", row, metrics),
        "lap_time": _metric_color("lap_time_s", row, metrics),
        "speed": _metric_color("avg_speed_kmh", row, metrics),
        "eng": _metric_color("energy_engine_j", row, metrics),
        "roll": _metric_color("energy_roll_j", row, metrics),
        "aero": _metric_color("energy_aero_j", row, metrics),
        "accel": _metric_color("energy_accel_j", row, metrics),
        "grade": _metric_color("energy_grade_j", row, metrics),
    }
    colors = []
    for key, _title, _width, _align, _better in COLS:
        colors.append(color_map.get(key, neutral))
    return colors


def _metric_color(metric_key, row, metrics):
    if metric_key not in metrics:
        return (0.92, 0.94, 0.98, 1.0)
    low, high, higher_is_better = metrics[metric_key]
    return heat_good_bad_color(
        float(row.get(metric_key, 0.0)),
        low,
        high,
        higher_is_better=higher_is_better,
    )


def _set_row(controls, values, colors):
    for ctrl, value, color in zip(controls, values, colors):
        set_text(ctrl, value)
        set_color(ctrl, color)


def _table_width():
    total = 0
    for _key, _title, width, _align, _better in COLS:
        total += width
    total += COL_GAP * (len(COLS) - 1)
    return total


def _draw_rect(x, y, w, h, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_line(x0, y0, x1, y1, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(x0, y0)
    ac.glVertex2f(x1, y1)
    ac.glEnd()


def _draw_grid(geo):
    x = geo["start_x"]
    y = geo["header_y"]
    table_w = _table_width()
    table_h = HEADER_H + 4 + ROW_COUNT * ROW_H
    color = (0.82, 0.84, 0.88, 0.18)

    _draw_line(x, y, x + table_w, y, color)
    _draw_line(x, y + HEADER_H, x + table_w, y + HEADER_H, color)
    _draw_line(x, y + table_h, x + table_w, y + table_h, color)

    for row_idx in range(ROW_COUNT + 1):
        py = geo["row_y"] + row_idx * ROW_H
        _draw_line(x, py, x + table_w, py, color)

    cursor = x
    _draw_line(cursor, y, cursor, y + table_h, color)
    for _key, _title, width, _align, _better in COLS:
        cursor += width
        _draw_line(cursor, y, cursor, y + table_h, color)
        cursor += COL_GAP
