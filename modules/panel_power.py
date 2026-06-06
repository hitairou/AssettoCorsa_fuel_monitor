# modules/panel_power.py
# Power analysis window.

from modules.display_format import fmt_kj, fmt_w
from modules.panel_common import add_label, set_color, set_text


WINDOW_SIZE = (420, 320)
PADDING = 8
GRAPH_H = 112
BAR_LABEL_W = 96
BAR_VALUE_W = 54
BAR_GAP = 6
ROW_H = 14
ROW_GAP = 2
TITLE_SAFE_TOP = 28
AXIS_W = 30
AXIS_H = 16

LEGEND = [
    ("Engine Demand", (1.0, 1.0, 1.0, 1.0)),
    ("Roll", (0.3, 1.0, 0.3, 1.0)),
    ("Aero", (0.3, 0.8, 1.0, 1.0)),
    ("Accel", (1.0, 0.6, 0.2, 1.0)),
    ("Grade", (1.0, 0.4, 0.9, 1.0)),
]

POWER_ROWS = [
    ("wheel", "Wheel Demand"),
    ("accel_pos", "Accel +"),
    ("grade_pos", "Grade +"),
    ("roll", "Roll"),
    ("aero", "Aero"),
    ("accel_neg", "Accel -"),
    ("grade_neg", "Grade -"),
]


def layout(window_size):
    width, _height = window_size
    graph_x = PADDING + AXIS_W
    graph_y = TITLE_SAFE_TOP + 4
    graph_w = width - graph_x - PADDING
    bar_graph_x = PADDING + BAR_LABEL_W + BAR_GAP
    bar_graph_w = width - bar_graph_x - PADDING - BAR_VALUE_W - BAR_GAP
    legend_y = graph_y + GRAPH_H + AXIS_H + 8
    bar_y = legend_y + 18
    estore_y = bar_y + (7 * ROW_H + 6 * ROW_GAP + 10) + 12
    return {
        "graph_rect": (graph_x, graph_y, graph_w, GRAPH_H),
        "bar_rect": (bar_graph_x, bar_y, bar_graph_w, 7 * ROW_H + 6 * ROW_GAP + 10),
        "estore_rect": (bar_graph_x, estore_y, bar_graph_w, 22),
        "graph_x": graph_x,
        "graph_y": graph_y,
        "graph_w": graph_w,
        "bar_label_x": PADDING,
        "bar_value_x": bar_graph_x + bar_graph_w + BAR_GAP,
        "legend_y": legend_y,
        "bar_y": bar_y,
        "estore_y": estore_y,
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

    legend_step = 82
    for idx, (text, color) in enumerate(LEGEND):
        x = PADDING + idx * legend_step
        labels["legend_" + str(idx)] = add_label(
            window_id, text, x, geo["legend_y"], 78, 14, 10, "left", color
        )

    for idx, (key, title) in enumerate(POWER_ROWS):
        row_y = geo["bar_y"] + 5 + idx * (ROW_H + ROW_GAP)
        labels["lbl_" + key] = add_label(
            window_id, title, geo["bar_label_x"], row_y, BAR_LABEL_W, ROW_H, 10, "left"
        )
        labels["val_" + key] = add_label(
            window_id, "0", geo["bar_value_x"], row_y, BAR_VALUE_W, ROW_H, 10, "right"
        )

    labels["lbl_estore"] = add_label(
        window_id, "Net Energy Balance [kJ]", PADDING, geo["estore_y"], 138, 14, 10, "left"
    )
    labels["val_estore"] = add_label(
        window_id, "0", geo["bar_value_x"], geo["estore_y"], BAR_VALUE_W, 14, 10, "right"
    )
    return labels


def update(labels, state):
    values = {
        "wheel": state.demand_wheel_power_w,
        "accel_pos": max(state.demand_accel_power_w, 0.0),
        "grade_pos": max(state.demand_grade_power_w, 0.0),
        "roll": state.demand_roll_power_w,
        "aero": state.demand_aero_power_w,
        "accel_neg": abs(min(state.demand_accel_power_w, 0.0)),
        "grade_neg": abs(min(state.demand_grade_power_w, 0.0)),
    }

    for key, value in values.items():
        set_text(labels["val_" + key], fmt_w(value, 0))

    set_text(labels["axis_top"], fmt_w(state.power_graph_scale_w, 0))
    set_text(labels["axis_bottom"], fmt_w(-state.power_graph_scale_w, 0))
    set_text(labels["val_estore"], fmt_kj(state.net_energy_balance_j, 1))

    if state.net_energy_balance_j >= 0.0:
        set_color(labels["val_estore"], (0.35, 0.75, 1.0, 1.0))
    else:
        set_color(labels["val_estore"], (1.0, 0.45, 0.45, 1.0))
