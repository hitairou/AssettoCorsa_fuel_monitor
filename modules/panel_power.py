# modules/panel_power.py
# Power analysis window.

from modules.display_format import fmt_signed_unit, fmt_unit
from modules.gauge_renderer import BREAKDOWN_SPECS, build_power_breakdown
from modules.panel_common import add_label, move, set_color, set_text


WINDOW_SIZE = (520, 360)
TITLE_SAFE_TOP = 28
PADDING = 10
AXIS_W = 50
ROW_H = 15


def layout(window_size):
    width, height = window_size
    graph_x = PADDING + AXIS_W
    graph_y = TITLE_SAFE_TOP + 8
    graph_w = max(width - graph_x - PADDING, 180)
    graph_h = 132

    tick_y = graph_y + graph_h + 2
    list_y = tick_y + 16
    label_x = PADDING
    value_x = PADDING + 110
    pct_x = PADDING + 190
    bar_y = list_y + len(BREAKDOWN_SPECS) * ROW_H + 6
    bar_rect = (PADDING + 8, bar_y, width - PADDING * 2 - 16, 28)
    residual_y = bar_y + 36
    residual_rect = (PADDING + 8, residual_y + 16, width - PADDING * 2 - 16, max(height - residual_y - 24, 44))

    return {
        "graph_rect": (graph_x, graph_y, graph_w, graph_h),
        "bar_rect": bar_rect,
        "residual_rect": residual_rect,
        "axis_top": (PADDING, graph_y),
        "axis_mid": (PADDING, graph_y + graph_h * 0.5 - 7),
        "axis_bot": (PADDING, graph_y + graph_h - 14),
        "time_ticks": [
            ("-20s", graph_x - 2),
            ("-15s", graph_x + graph_w * 0.25 - 18),
            ("-10s", graph_x + graph_w * 0.50 - 18),
            ("-5s", graph_x + graph_w * 0.75 - 14),
            ("0s", graph_x + graph_w - 18),
        ],
        "list_y": list_y,
        "label_x": label_x,
        "value_x": value_x,
        "pct_x": pct_x,
        "residual_label": (PADDING, residual_y),
        "residual_value": (width - PADDING - 88, residual_y),
    }


def create(window_id):
    labels = {}
    geo = layout(WINDOW_SIZE)

    labels["axis_top"] = add_label(window_id, "+400 W", 0, 0, AXIS_W, 14, 9, "right")
    labels["axis_mid"] = add_label(window_id, "0 W", 0, 0, AXIS_W, 14, 9, "right")
    labels["axis_bot"] = add_label(window_id, "-400 W", 0, 0, AXIS_W, 14, 9, "right")

    labels["time_ticks"] = []
    for text, _x in geo["time_ticks"]:
        labels["time_ticks"].append(add_label(window_id, text, 0, 0, 34, 12, 9, "left"))

    labels["rows"] = []
    for _key, title, _side, _fn, color in BREAKDOWN_SPECS:
        labels["rows"].append({
            "name": add_label(window_id, title, 0, 0, 100, ROW_H, 10, "left", color),
            "value": add_label(window_id, "0 W", 0, 0, 76, ROW_H, 10, "right"),
            "pct": add_label(window_id, "0.0%", 0, 0, 56, ROW_H, 10, "right"),
        })

    labels["residual_label"] = add_label(window_id, "Residual Int.", 0, 0, 120, 14, 10, "left")
    labels["residual_value"] = add_label(window_id, "0.0 kJ", 0, 0, 88, 14, 10, "right")
    _apply_layout(labels, WINDOW_SIZE)
    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("power", WINDOW_SIZE))
    _apply_layout(labels, size)

    scale = max(float(state.power_graph_scale_w), 300.0)
    set_text(labels["axis_top"], fmt_signed_unit(scale, "W", digits=0))
    set_text(labels["axis_mid"], "0 W")
    set_text(labels["axis_bot"], fmt_signed_unit(-scale, "W", digits=0))

    breakdown = build_power_breakdown(state)
    for idx, row in enumerate(breakdown):
        ui = labels["rows"][idx]
        set_text(ui["value"], fmt_unit(row["value_w"], "W", digits=0))
        set_text(ui["pct"], "{0}%".format(fmt_unit(row["pct"], "", digits=1).replace(" ", "")))
        set_color(ui["value"], row["color"])
        set_color(ui["pct"], row["color"])

    set_text(labels["residual_value"], fmt_unit(state.net_energy_balance_j, "kJ", digits=1, scale=1000.0))
    if state.net_energy_balance_j >= 0.0:
        set_color(labels["residual_value"], (0.42, 0.82, 1.0, 1.0))
    else:
        set_color(labels["residual_value"], (0.96, 0.46, 0.40, 1.0))


def _apply_layout(labels, size):
    geo = layout(size)
    move(labels["axis_top"], geo["axis_top"][0], int(geo["axis_top"][1]), AXIS_W, 14)
    move(labels["axis_mid"], geo["axis_mid"][0], int(geo["axis_mid"][1]), AXIS_W, 14)
    move(labels["axis_bot"], geo["axis_bot"][0], int(geo["axis_bot"][1]), AXIS_W, 14)

    for idx, tick in enumerate(labels["time_ticks"]):
        text, tick_x = geo["time_ticks"][idx]
        set_text(tick, text)
        move(tick, int(tick_x), int(layout(size)["graph_rect"][1] + layout(size)["graph_rect"][3] + 2), 34, 12)

    for idx, row in enumerate(labels["rows"]):
        y = geo["list_y"] + idx * ROW_H
        move(row["name"], geo["label_x"], y, 100, ROW_H)
        move(row["value"], geo["value_x"], y, 76, ROW_H)
        move(row["pct"], geo["pct_x"], y, 56, ROW_H)

    move(labels["residual_label"], geo["residual_label"][0], geo["residual_label"][1], 120, 14)
    move(labels["residual_value"], geo["residual_value"][0], geo["residual_value"][1], 88, 14)
