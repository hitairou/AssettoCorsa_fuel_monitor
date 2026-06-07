# modules/panel_power.py
# Power analysis window.

from modules.display_format import fmt_float, fmt_kj, fmt_w
from modules import graph_renderer
from modules.panel_common import add_label, move, set_color, set_text


WINDOW_SIZE = (720, 460)
PADDING = 8
GRAPH_H = 112
BAR_LABEL_W = 126
BAR_VALUE_W = 72
BAR_GAP = 8
TITLE_SAFE_TOP = 28
AXIS_W = 30
AXIS_H = 16

FORMULA_FONT = 8
ROW_FONT = 10
HEADER_FONT = 9

FORMULA_H = 11
ROW_H = 12
ROW_BLOCK_H = 25
GROUP_GAP = 10
BAR_H = 10
FORMULA_GAP = 2
MAX_FORMULA_TOKENS = 24

GROUP_HEADERS = [
    ("road", "Road Load Components"),
    ("summary", "Demand Summary"),
    ("engine", "Engine / Drivetrain"),
]

ROAD_LOAD_ROWS = [
    ("roll", "Roll [W]", (0.3, 1.0, 0.3, 1.0), "positive", 1),
    ("aero", "Aero [W]", (0.3, 0.8, 1.0, 1.0), "positive", 1),
    ("accel", "Accel [W]", (1.0, 0.6, 0.2, 1.0), "signed", 1),
    ("grade", "Grade [W]", (1.0, 0.4, 0.9, 1.0), "signed", 1),
]

SUMMARY_ROWS = [
    ("wheel", "Wheel Demand [W]", (1.0, 1.0, 1.0, 1.0), "positive", 1),
]

ENGINE_ROWS = [
    ("engine_supply", "Engine Supply [W]", (0.85, 0.85, 0.92, 1.0), "positive", 1),
    ("drivetrain_loss", "Drivetrain Loss [W]", (1.0, 0.75, 0.25, 1.0), "positive", 1),
    ("drivetrain_loss_energy", "Drivetrain Loss Energy [kJ]", (0.35, 0.75, 1.0, 1.0), "positive", 1),
]

POWER_ROWS = ROAD_LOAD_ROWS + SUMMARY_ROWS + ENGINE_ROWS

LEGEND = [
    ("Wheel Demand", (1.0, 1.0, 1.0, 1.0)),
    ("Roll", (0.3, 1.0, 0.3, 1.0)),
    ("Aero", (0.3, 0.8, 1.0, 1.0)),
    ("Accel", (1.0, 0.6, 0.2, 1.0)),
    ("Grade", (1.0, 0.4, 0.9, 1.0)),
]

_STYLE_COLORS = {
    "const": (0.95, 0.95, 0.98, 1.0),
    "var": None,
    "result": None,
}


def layout(window_size):
    width, _height = window_size
    graph_x = PADDING + AXIS_W
    graph_y = TITLE_SAFE_TOP + 4
    graph_w = width - graph_x - PADDING
    bar_graph_x = PADDING + BAR_LABEL_W + BAR_GAP
    bar_value_x = width - PADDING - BAR_VALUE_W
    bar_graph_w = bar_value_x - BAR_GAP - bar_graph_x
    legend_y = graph_y + GRAPH_H + AXIS_H + 8

    rows = []
    group_headers = []
    current_y = legend_y + 18
    for group_key, group_title, group_rows in (
        ("road", "Road Load Components", ROAD_LOAD_ROWS),
        ("summary", "Demand Summary", SUMMARY_ROWS),
        ("engine", "Engine / Drivetrain", ENGINE_ROWS),
    ):
        if rows:
            current_y += GROUP_GAP
        group_headers.append(
            {
                "key": group_key,
                "title": group_title,
                "x": PADDING,
                "y": current_y - 12,
            }
        )
        for key, title, color, mode, formula_lines in group_rows:
            formula_h = FORMULA_H
            bar_y = current_y + formula_h + FORMULA_GAP
            row_h = max(BAR_H, 10)
            rows.append(
                {
                    "key": key,
                    "title": title,
                    "color": color,
                    "mode": mode,
                    "formula_lines": formula_lines,
                    "formula_y": current_y,
                    "formula_h": formula_h,
                    "formula_x": bar_graph_x,
                    "formula_w": bar_value_x - BAR_GAP - bar_graph_x,
                    "row_y": bar_y,
                    "title_y": bar_y,
                    "value_y": bar_y,
                    "bar_y": bar_y + 1,
                    "bar_h": row_h,
                }
            )
            current_y += formula_h + FORMULA_GAP + row_h + 4

    bar_rows = rows[:-1]
    energy_row = rows[-1]
    if bar_rows:
        bar_rect_y = bar_rows[0]["bar_y"] - 2
        bar_rect_h = bar_rows[-1]["bar_y"] + bar_rows[-1]["bar_h"] - bar_rect_y + 2
    else:
        bar_rect_y = current_y
        bar_rect_h = 20

    estore_rect = (bar_graph_x, energy_row["bar_y"] - 2, bar_graph_w, energy_row["bar_h"] + 6)
    return {
        "summary": (PADDING, TITLE_SAFE_TOP + 2, width - PADDING * 2, 20),
        "graph_rect": (graph_x, graph_y, graph_w, GRAPH_H),
        "graph_x": graph_x,
        "graph_y": graph_y,
        "graph_w": graph_w,
        "bar_label_x": PADDING,
        "bar_value_x": bar_value_x,
        "bar_graph_x": bar_graph_x,
        "bar_graph_w": bar_graph_w,
        "legend_y": legend_y,
        "bar_y": bar_rows[0]["row_y"] if bar_rows else current_y,
        "bar_rect": (bar_graph_x, bar_rect_y, bar_graph_w, bar_rect_h),
        "estore_rect": estore_rect,
        "estore_y": energy_row["row_y"] + 1,
        "rows": rows,
        "bar_rows": bar_rows,
        "energy_row": energy_row,
        "group_headers": group_headers,
    }


def create(window_id):
    labels = {}
    geo = layout(WINDOW_SIZE)

    labels["axis_top"] = add_label(
        window_id, "2000", PADDING, geo["graph_y"], AXIS_W - 2, 14, 9, "right"
    )
    labels["axis_zero"] = add_label(
        window_id, "0", PADDING, geo["graph_y"] + GRAPH_H / 2 - 7, AXIS_W - 2, 14, 9, "right"
    )
    labels["axis_bottom"] = add_label(
        window_id, "-2000", PADDING, geo["graph_y"] + GRAPH_H - 14, AXIS_W - 2, 14, 9, "right"
    )
    labels["axis_t_left"] = add_label(
        window_id, "-10s", geo["graph_x"], geo["graph_y"] + GRAPH_H + 1, 40, 12, 9, "left"
    )
    labels["axis_t_right"] = add_label(
        window_id, "0s", geo["graph_x"] + geo["graph_w"] - 20, geo["graph_y"] + GRAPH_H + 1, 20, 12, 9, "right"
    )

    labels["diag_rev"] = add_label(window_id, "", PADDING, 4, 560, 10, 8, "left")
    labels["diag_hist"] = add_label(window_id, "", PADDING, 16, 900, 10, 8, "left")
    labels["diag_state"] = add_label(window_id, "", PADDING, 28, 900, 10, 8, "left")

    legend_step = 82
    for idx, (text, color) in enumerate(LEGEND):
        x = PADDING + idx * legend_step
        labels["legend_" + str(idx)] = add_label(
            window_id, text, x, geo["legend_y"], 78, 14, 10, "left", color
        )

    for group_header in geo["group_headers"]:
        labels["group_" + group_header["key"]] = add_label(
            window_id,
            group_header["title"],
            group_header["x"],
            group_header["y"],
            260,
            12,
            HEADER_FONT,
            "left",
            (0.78, 0.82, 0.88, 0.95),
        )

    for row in geo["rows"]:
        labels["lbl_" + row["key"]] = add_label(
            window_id, row["title"], geo["bar_label_x"], row["title_y"], BAR_LABEL_W, ROW_H, ROW_FONT, "left"
        )
        labels["val_" + row["key"]] = add_label(
            window_id, "0", geo["bar_value_x"], row["value_y"], BAR_VALUE_W, ROW_H, ROW_FONT, "right"
        )
        labels["formula_" + row["key"]] = create_formula_tokens(window_id, row["key"], MAX_FORMULA_TOKENS)

    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("power", WINDOW_SIZE))
    geo = layout(size)

    values = {
        "roll": state.demand_roll_power_w,
        "aero": state.demand_aero_power_w,
        "accel": state.demand_accel_power_w,
        "grade": state.demand_grade_power_w,
        "wheel": state.demand_wheel_power_w,
        "engine_supply": getattr(state, "engine_supply_power_w", 0.0),
        "drivetrain_loss": getattr(state, "drivetrain_loss_power_w", 0.0),
        "drivetrain_loss_energy": getattr(state, "drivetrain_loss_energy_j", 0.0) / 1000.0,
    }

    for key, value in values.items():
        if key == "drivetrain_loss_energy":
            set_text(labels["val_" + key], fmt_kj(getattr(state, "drivetrain_loss_energy_j", 0.0), 1))
        else:
            set_text(labels["val_" + key], fmt_w(value, 0))

    set_text(labels["axis_top"], fmt_w(state.power_graph_scale_w, 0))
    set_text(labels["axis_bottom"], fmt_w(-state.power_graph_scale_w, 0))

    if _is_positive_metric(state.drivetrain_loss_energy_j):
        set_color(labels["val_drivetrain_loss_energy"], (0.35, 0.75, 1.0, 1.0))
    else:
        set_color(labels["val_drivetrain_loss_energy"], (1.0, 0.45, 0.45, 1.0))

    for row in geo["rows"]:
        row_key = row["key"]
        row_color = row["color"]
        move(labels["lbl_" + row_key], geo["bar_label_x"], row["title_y"], BAR_LABEL_W, ROW_H)
        move(labels["val_" + row_key], geo["bar_value_x"], row["value_y"], BAR_VALUE_W, ROW_H)
        update_formula_tokens(labels, row, state, row_color)
        set_color(labels["lbl_" + row_key], row_color)
        set_color(labels["val_" + row_key], row_color if row_key != "drivetrain_loss" else (1.0, 0.75, 0.25, 1.0))

    set_color(labels["val_wheel"], (1.0, 1.0, 1.0, 1.0))
    set_color(labels["val_engine_supply"], (0.85, 0.85, 0.92, 1.0))
    set_color(labels["val_drivetrain_loss"], (1.0, 0.75, 0.25, 1.0))

    if _show_power_diag(state):
        graph_diag = getattr(state, "graph_renderer_diag", {})
        wheel_diag = graph_diag.get("hist_wheel", {})
        accel_diag = graph_diag.get("hist_accel", {})
        set_text(labels["diag_rev"], "GREV: {0}".format(graph_renderer.GRAPH_RENDERER_REV))
        set_text(
            labels["diag_hist"],
            "epoch={0} histW={1} last={2} cur={3} pts={4} err={5} | histA={6} last={7} cur={8} pts={9} err={10}".format(
                getattr(state, "power_history_epoch", 0),
                len(state.hist_wheel),
                state.hist_wheel.to_list()[-1] if len(state.hist_wheel) else "",
                state.current_P_wheel,
                wheel_diag.get("points_count", ""),
                wheel_diag.get("error", ""),
                len(state.hist_accel),
                state.hist_accel.to_list()[-1] if len(state.hist_accel) else "",
                state.current_P_accel_term,
                accel_diag.get("points_count", ""),
                accel_diag.get("error", ""),
            ),
        )
        set_text(
            labels["diag_state"],
            "lastH={0} curP={1} loss={2} render={3}".format(
                wheel_diag.get("last_history_point", ""),
                wheel_diag.get("current_point", ""),
                getattr(state, "drivetrain_loss_power_w", 0.0),
                getattr(state, "last_render_error", ""),
            ),
        )
    else:
        set_text(labels["diag_rev"], "")
        set_text(labels["diag_hist"], "")
        set_text(labels["diag_state"], "")


def create_formula_tokens(window_id, row_key, token_count):
    labels = []
    for _idx in range(token_count):
        labels.append(add_label(window_id, "", 0, 0, 12, FORMULA_H, FORMULA_FONT, "left"))
    return labels


def update_formula_tokens(labels, row, state, row_color):
    token_labels = labels.get("formula_" + row["key"], [])
    formula_x = row["formula_x"]
    formula_y = row["formula_y"]
    formula_w = row["formula_w"]
    line_h = FORMULA_H
    max_lines = row["formula_lines"]
    tokens = _choose_formula_tokens(row["key"], state, formula_w, max_lines)
    layout = _layout_formula_tokens(tokens, formula_x, formula_y, formula_w, line_h, max_lines)
    for idx, label in enumerate(token_labels):
        if idx < len(layout):
            item = layout[idx]
            move(label, item["x"], item["y"], item["w"], FORMULA_H)
            set_text(label, item["text"])
            set_color(label, _style_color(item["style"], row["key"], row_color))
        else:
            move(label, formula_x, formula_y, 12, FORMULA_H)
            set_text(label, "")
            set_color(label, (1.0, 1.0, 1.0, 0.0))


def _layout_formula_tokens(tokens, formula_x, formula_y, formula_w, line_h, max_lines):
    laid_out = []
    line = 0
    cursor_x = formula_x
    line_start_x = formula_x
    line_width = 0
    for idx, (text, style) in enumerate(tokens):
        token_w = _estimate_token_width(text)
        if line_width > 0 and cursor_x + token_w > formula_x + formula_w:
            line += 1
            if line >= max_lines:
                break
            cursor_x = line_start_x
            line_width = 0
        laid_out.append(
            {
                "text": text,
                "style": style,
                "x": cursor_x,
                "y": formula_y + line * (line_h + 1),
                "w": token_w,
            }
        )
        cursor_x += token_w
        line_width += token_w
    return _trim_formula_layout(laid_out, formula_x, formula_y, formula_w, line_h, max_lines)


def _trim_formula_layout(laid_out, formula_x, formula_y, formula_w, line_h, max_lines):
    if not laid_out:
        return laid_out
    last_y = laid_out[-1]["y"]
    if last_y <= formula_y + (max_lines - 1) * (line_h + 1):
        return laid_out
    if max_lines <= 1:
        return _truncate_to_fit(laid_out, formula_x, formula_y, formula_w)
    return laid_out


def _truncate_to_fit(laid_out, formula_x, formula_y, formula_w):
    clipped = []
    cursor_x = formula_x
    for token in laid_out:
        token_w = min(_estimate_token_width(token["text"]), formula_w)
        if cursor_x + token_w > formula_x + formula_w:
            break
        clipped.append(
            {
                "text": token["text"],
                "style": token["style"],
                "x": cursor_x,
                "y": formula_y,
                "w": token_w,
            }
        )
        cursor_x += token_w
    if clipped and clipped[-1]["text"] != "…":
        ellipsis_w = _estimate_token_width("…")
        if cursor_x + ellipsis_w <= formula_x + formula_w:
            clipped.append(
                {
                    "text": "…",
                    "style": "const",
                    "x": cursor_x,
                    "y": formula_y,
                    "w": ellipsis_w,
                }
            )
    return clipped if clipped else laid_out[:1]


def _choose_formula_tokens(row_key, state, formula_w, max_lines):
    detailed = _formula_tokens_for_row(row_key, state, compact=False)
    if _fits_line(detailed, formula_w):
        return detailed
    compact = _formula_tokens_for_row(row_key, state, compact=True)
    if _fits_line(compact, formula_w):
        return compact
    if max_lines > 1:
        if _fits_line(_formula_tokens_for_row(row_key, state, compact="minimal"), formula_w):
            return _formula_tokens_for_row(row_key, state, compact="minimal")
    return _formula_tokens_for_row(row_key, state, compact="minimal")


def _fits_line(tokens, formula_w):
    return sum(_estimate_token_width(text) for text, _style in tokens) <= formula_w


def _formula_tokens_for_row(row_key, state, compact=False):
    v_ms = getattr(state, "observed_speed_ms", 0.0) if state is not None else 0.0
    accel_ms2 = getattr(state, "accel_ms2", 0.0) if state is not None else 0.0
    theta = getattr(state, "theta_rad", 0.0) if state is not None else 0.0
    wheel = getattr(state, "demand_wheel_power_w", 0.0) if state is not None else 0.0
    roll = getattr(state, "demand_roll_power_w", 0.0) if state is not None else 0.0
    aero = getattr(state, "demand_aero_power_w", 0.0) if state is not None else 0.0
    accel = getattr(state, "demand_accel_power_w", 0.0) if state is not None else 0.0
    grade = getattr(state, "demand_grade_power_w", 0.0) if state is not None else 0.0
    engine_supply = getattr(state, "engine_supply_power_w", 0.0) if state is not None else 0.0
    drivetrain_loss = getattr(state, "drivetrain_loss_power_w", 0.0) if state is not None else 0.0
    loss_energy_kj = getattr(state, "drivetrain_loss_energy_j", 0.0) / 1000.0 if state is not None else 0.0
    eta_d = float(getattr(state, "vehicle", {}).get("drivetrain_efficiency", 0.9)) if state is not None else 0.9
    crr = float(getattr(state, "vehicle", {}).get("crr", 0.0025)) if state is not None else 0.0025
    mass = float(getattr(state, "vehicle", {}).get("mass_total", 98.65)) if state is not None else 98.65
    g = float(getattr(state, "vehicle", {}).get("gravity", 9.81)) if state is not None else 9.81
    rho = float(getattr(state, "vehicle", {}).get("rho_air", 1.225)) if state is not None else 1.225
    cd = float(getattr(state, "vehicle", {}).get("cd", 0.355)) if state is not None else 0.355
    area = float(getattr(state, "vehicle", {}).get("frontal_area", 0.3846)) if state is not None else 0.3846

    if row_key == "roll":
        if compact == "minimal":
            return [("Crr×m×g×cosθ×v", "const")]
        if compact:
            return [
                ("Crr[" + fmt_float(crr, 4) + "]", "const"),
                ("×", "const"),
                ("m[" + fmt_float(mass, 1) + "]", "const"),
                ("×", "const"),
                ("g[" + fmt_float(g, 2) + "]", "const"),
                ("×cosθ[", "const"),
                (fmt_float(theta, 3), "var"),
                ("]×", "const"),
                ("v[", "const"),
                (fmt_float(v_ms, 2), "var"),
                ("]", "const"),
            ]
        return [
            ("Crr [" + fmt_float(crr, 4) + "]", "const"),
            (" × ", "const"),
            ("m[" + fmt_float(mass, 1) + "]", "const"),
            (" × ", "const"),
            ("g[" + fmt_float(g, 2) + "]", "const"),
            (" × cosθ[", "const"),
            (fmt_float(theta, 3), "var"),
            ("] × v[", "const"),
            (fmt_float(v_ms, 2), "var"),
            ("]", "const"),
        ]
    if row_key == "aero":
        if compact == "minimal":
            return [("0.5×ρ×Cd×A×v^3", "const")]
        if compact:
            return [
                ("0.5×ρ[" + fmt_float(rho, 3) + "]", "const"),
                ("×Cd[" + fmt_float(cd, 3) + "]", "const"),
                ("×A[" + fmt_float(area, 4) + "]", "const"),
                ("×v[", "const"),
                (fmt_float(v_ms, 2), "var"),
                ("]^3", "const"),
            ]
        return [
            ("0.5", "const"),
            (" × ", "const"),
            ("ρ [" + fmt_float(rho, 3) + "]", "const"),
            (" × ", "const"),
            ("Cd [" + fmt_float(cd, 3) + "]", "const"),
            (" × ", "const"),
            ("A [" + fmt_float(area, 4) + "]", "const"),
            (" × ", "const"),
            ("v [" + fmt_float(v_ms, 2) + "]", "var"),
            ("^3", "const"),
        ]
    if row_key == "accel":
        if compact == "minimal":
            return [("m×a×v", "const")]
        if compact:
            return [
                ("m[" + fmt_float(mass, 1) + "]", "const"),
                ("×a[", "const"),
                (fmt_float(accel_ms2, 3), "var"),
                ("]×v[", "const"),
                (fmt_float(v_ms, 2), "var"),
                ("]", "const"),
            ]
        return [
            ("m[" + fmt_float(mass, 1) + "]", "const"),
            (" × ", "const"),
            ("a[" + fmt_float(accel_ms2, 3) + "]", "var"),
            (" × ", "const"),
            ("v[" + fmt_float(v_ms, 2) + "]", "var"),
        ]
    if row_key == "grade":
        if compact == "minimal":
            return [("m×g×sinθ×v", "const")]
        if compact:
            return [
                ("m[" + fmt_float(mass, 1) + "]", "const"),
                ("×g[" + fmt_float(g, 2) + "]", "const"),
                ("×sinθ[", "const"),
                (fmt_float(theta, 3), "var"),
                ("]×v[", "const"),
                (fmt_float(v_ms, 2), "var"),
                ("]", "const"),
            ]
        return [
            ("m[" + fmt_float(mass, 1) + "]", "const"),
            (" × ", "const"),
            ("g[" + fmt_float(g, 2) + "]", "const"),
            (" × sinθ[", "const"),
            (fmt_float(theta, 3), "var"),
            ("] × v[", "const"),
            (fmt_float(v_ms, 2), "var"),
            ("]", "const"),
        ]
    if row_key == "wheel":
        if compact == "minimal":
            return [("max(R+A+Ac+G,0)", "const")]
        if compact:
            return [
                ("max(", "const"),
                ("R[", "const"),
                (fmt_float(roll, 1), "var"),
                ("]+A[", "const"),
                (fmt_float(aero, 1), "var"),
                ("]+Ac[", "const"),
                (fmt_float(accel, 1), "var"),
                ("]+G[", "const"),
                (fmt_float(grade, 1), "var"),
                ("]", "const"),
                (",0)", "const"),
            ]
        return [
            ("max(", "const"),
            ("Roll[", "const"),
            (fmt_float(roll, 1), "var"),
            ("]+Aero[", "const"),
            (fmt_float(aero, 1), "var"),
            ("]+Accel[", "const"),
            (fmt_float(accel, 1), "var"),
            ("]+Grade[", "const"),
            (fmt_float(grade, 1), "var"),
            ("]", "const"),
            (",0)", "const"),
        ]
    if row_key == "engine_supply":
        if compact == "minimal":
            return [("Wheel/ηd", "const")]
        if compact:
            return [
                ("Wheel[", "const"),
                (fmt_float(wheel, 1), "var"),
                ("]/", "const"),
                ("ηd[", "const"),
                (fmt_float(eta_d, 3), "var"),
                ("]", "const"),
            ]
        return [
            ("engine_on ? Wheel[", "const"),
            (fmt_float(wheel, 1), "var"),
            ("] / ηd[", "const"),
            (fmt_float(eta_d, 3), "var"),
            ("] : 0", "const"),
        ]
    if row_key == "drivetrain_loss":
        if compact == "minimal":
            return [("Eng-Wheel", "const")]
        if compact:
            return [
                ("Eng[", "const"),
                (fmt_float(engine_supply, 1), "var"),
                ("]-Wheel[", "const"),
                (fmt_float(wheel, 1), "var"),
                ("]", "const"),
            ]
        return [
            ("engine_on ? Eng[", "const"),
            (fmt_float(engine_supply, 1), "var"),
            ("] - Wheel[", "const"),
            (fmt_float(wheel, 1), "var"),
            ("] : 0", "const"),
        ]
    if row_key == "drivetrain_loss_energy":
        if compact == "minimal":
            return [("∫Loss dt/1000", "const")]
        if compact:
            return [
                ("∫Loss[", "const"),
                (fmt_float(drivetrain_loss, 1), "var"),
                ("]dt/1000", "const"),
            ]
        return [
            ("∫Loss[", "const"),
            (fmt_float(drivetrain_loss, 1), "var"),
            ("] dt / 1000", "const"),
        ]
    return [("", "const")]


def _style_color(style, row_key, row_color=None):
    if style == "const":
        return _STYLE_COLORS["const"]
    if row_color is None:
        row_color = _row_color_for_key(row_key)
    return row_color


def _row_color_for_key(row_key):
    for spec in POWER_ROWS:
        if spec[0] == row_key:
            return spec[2]
    return (0.95, 0.95, 0.98, 1.0)


def _estimate_token_width(text):
    return max(12, int(len(text) * 6.2) + 4)


def _is_positive_metric(value):
    try:
        return float(value) >= 0.0
    except Exception:
        return False


def _show_power_diag(state):
    strategy = getattr(state, "strategy", {}) or {}
    return _cfg_bool(strategy.get("debug_mode", 0)) or _cfg_bool(
        strategy.get("power_graph_debug_overlay", 0)
    )


def _cfg_bool(value):
    try:
        return bool(int(value))
    except Exception:
        return str(value).strip().lower() in ("true", "yes", "on")
