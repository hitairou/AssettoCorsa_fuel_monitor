# modules/panel_bsfc.py
# BSFC map analysis window.

from modules import bsfc_renderer

from modules.display_format import fmt_float, fmt_pct, fmt_rpm

from modules.panel_common import add_label, move, set_color, set_text

try:
    import ac
except ImportError:
    class _AcStub(object):
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return 0
            return _noop

    ac = _AcStub()


WINDOW_SIZE = (420, 340)
PADDING = 10
TITLE_SAFE_TOP = 28
AXIS_LEFT_W = 38
AXIS_BOTTOM_H = 28
TOP_H = 28


def layout(window_size):
    width, height = window_size
    map_x = PADDING + AXIS_LEFT_W
    map_y = TITLE_SAFE_TOP + TOP_H + 10
    map_w = max(width - PADDING * 2 - AXIS_LEFT_W, 180)
    map_h = max(height - map_y - PADDING - AXIS_BOTTOM_H, 110)
    return {
        "summary": (PADDING, TITLE_SAFE_TOP + 2, width - PADDING * 2, 20),
        "map_rect": (map_x, map_y, map_w, map_h),
        "y_title": (PADDING, map_y - 14, AXIS_LEFT_W + 22, 12),
        "x_title": (map_x + map_w / 2 - 48, map_y + map_h + 16, 96, 12),
    }


def create(window_id):
    labels = {"window_id": window_id}

    labels["summary"] = add_label(window_id, "---", 0, 0, 260, 18, 13, "center")
    labels["x_axis_title"] = add_label(window_id, "RPM [1/min]", 0, 0, 96, 12, 9, "center")
    labels["y_axis_title"] = add_label(window_id, "Load [%]", 0, 0, 62, 12, 9, "left")

    labels["x_ticks"] = []
    for _rpm in (1000, 2000, 3000, 4000, 5000, 6000):
        labels["x_ticks"].append(add_label(window_id, "---", 0, 0, 34, 12, 9, "center"))

    labels["y_ticks"] = []
    for _load in (100, 80, 60, 40, 20, 0):
        labels["y_ticks"].append(add_label(window_id, "---", 0, 0, 30, 12, 9, "right"))

    _apply_layout(labels, WINDOW_SIZE)
    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("bsfc", WINDOW_SIZE))
    _apply_layout(labels, size)

    current_rpm = 0 if state.current_load_display_ratio is None else state.observed_rpm
    current_load = None
    if state.current_load_display_ratio is not None:
        current_load = state.current_load_display_ratio * 100.0

    summary = "{0} rpm {1} % {2} g/kWh".format(
        fmt_rpm(current_rpm),
        fmt_pct(current_load, 1),
        fmt_float(state.current_bsfc_display_g_per_kwh, 0),
    )
    set_text(labels["summary"], summary)

    dim_alpha = 1.0 if state.engine_on else 0.42
    base_color = (0.94, 0.95, 0.98, dim_alpha)
    set_color(labels["summary"], base_color)
    set_color(labels["x_axis_title"], (0.86, 0.88, 0.92, 0.84 * dim_alpha))
    set_color(labels["y_axis_title"], (0.86, 0.88, 0.92, 0.84 * dim_alpha))
    for tick in labels["x_ticks"] + labels["y_ticks"]:
        set_color(tick, (0.82, 0.84, 0.88, 0.76 * dim_alpha))


def _apply_layout(labels, size):
    geo = layout(size)
    move(labels["summary"], geo["summary"][0], geo["summary"][1], geo["summary"][2], geo["summary"][3])
    move(labels["x_axis_title"], int(geo["x_title"][0]), int(geo["x_title"][1]), int(geo["x_title"][2]), 12)
    move(labels["y_axis_title"], int(geo["y_title"][0]), int(geo["y_title"][1]), int(geo["y_title"][2]), 12)

    map_rect = geo["map_rect"]
    x0, y0, w, h = map_rect

    rpms = (1000, 2000, 3000, 4000, 5000, 6000)
    for idx, rpm in enumerate(rpms):
        px = x0 + int((float(idx) / float(len(rpms) - 1)) * w) - 16
        set_text(labels["x_ticks"][idx], str(rpm))
        move(labels["x_ticks"][idx], px, y0 + h + 2, 34, 12)

    loads = (100, 80, 60, 40, 20, 0)
    for idx, load in enumerate(loads):
        py = y0 + int((float(idx) / float(len(loads) - 1)) * h) - 6
        set_text(labels["y_ticks"][idx], str(load))
        move(labels["y_ticks"][idx], PADDING, py, AXIS_LEFT_W - 6, 12)
