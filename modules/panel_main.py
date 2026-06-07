# modules/panel_main.py
# Main HUD-style window with three key values and four corner buttons.

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

from modules.display_format import fmt_float, fmt_sign, fmt_time_ms
from modules.panel_common import (
    add_button,
    add_label,
    move,
    set_button_state,
    set_color,
    set_text,
)
from modules.ui_presets import PRESET_ABBREV


WINDOW_SIZE = (640, 108)
TITLE_SAFE_TOP = 28
OUTER_PAD_X = 10
OUTER_PAD_Y = 8
BUTTON_W = 48
BUTTON_H = 20
BUTTON_COL_W = 112
BUTTON_ROW_GAP = 6


def layout(window_size):
    width, height = window_size
    body_x = OUTER_PAD_X
    body_y = TITLE_SAFE_TOP + OUTER_PAD_Y
    body_w = max(width - OUTER_PAD_X * 2, 240)
    body_h = max(height - body_y - OUTER_PAD_Y, 48)

    inner_pad = 18
    content_x = body_x + BUTTON_COL_W + inner_pad
    content_y = body_y + 12
    content_w = max(body_w - BUTTON_COL_W - inner_pad * 2, 200)
    content_h = max(body_h - 24, 24)
    block_w = content_w / 3.0

    return {
        "body_rect": (body_x, body_y, body_w, body_h),
        "buttons": {
            "power": (body_x + 6, body_y + 6),
            "lap": (body_x + BUTTON_W + 12, body_y + 6),
            "bsfc": (body_x + 6, body_y + BUTTON_H + BUTTON_ROW_GAP + 6),
            "debug": (body_x + BUTTON_W + 12, body_y + BUTTON_H + BUTTON_ROW_GAP + 6),
        },
        "value_rects": {
            "avg_econ": (content_x, content_y, block_w, content_h),
            "pace_delta": (content_x + block_w, content_y, block_w, content_h),
            "engine": (content_x + block_w * 2.0, content_y, block_w, content_h),
        },
    }


def create(window_id, callbacks):
    labels = {"window_id": window_id}
    labels["power_button"] = add_button(window_id, "PWR", 0, 0, BUTTON_W, BUTTON_H, callback=callbacks.get("power"))
    labels["lap_button"] = add_button(window_id, "LAP", 0, 0, BUTTON_W, BUTTON_H, callback=callbacks.get("lap"))
    labels["bsfc_button"] = add_button(window_id, "BSFC", 0, 0, BUTTON_W + 10, BUTTON_H, callback=callbacks.get("bsfc"))
    labels["debug_button"] = add_button(window_id, "DBG", 0, 0, BUTTON_W, BUTTON_H, callback=callbacks.get("debug"))
    labels["run_id"] = add_label(window_id, "REV: ------", 0, 0, 92, 14, 9, "right", (1.0, 1.0, 0.8, 1.0))
    labels["val_avg_econ"] = add_label(window_id, "---", 0, 0, 160, 36, 24, "center")
    labels["val_pace_delta"] = add_label(window_id, "---", 0, 0, 170, 42, 30, "center")
    labels["val_engine"] = add_label(window_id, "---", 0, 0, 120, 36, 24, "center")
    _apply_layout(labels, WINDOW_SIZE)
    return labels


def update(labels, state):
    size = tuple(state.ui_window_sizes.get("main", WINDOW_SIZE))
    _apply_layout(labels, size)

    econ_text = _fmt_kmpl(state.avg_fuel_econ_km_per_l)
    pace_text = _fmt_pace_delta(state.pace_delta_s)
    engine_text = "ON" if state.engine_on else "OFF"

    set_text(labels["val_avg_econ"], econ_text)
    set_text(labels["val_pace_delta"], pace_text)
    set_text(labels["val_engine"], engine_text)

    set_color(labels["val_avg_econ"], _econ_color(state.avg_fuel_econ_km_per_l))
    set_color(labels["val_pace_delta"], _pace_color(state.pace_delta_s))
    set_color(labels["val_engine"], _engine_color(state.engine_on))

    set_text(labels["run_id"], "REV: {0}".format(str(getattr(state, "build_id", "------"))))

    set_text(labels["power_button"], "PWR")
    set_text(labels["lap_button"], "LAP")
    set_text(labels["bsfc_button"], "BSFC")
    set_text(labels["debug_button"], "DBG")
    set_button_state(labels["power_button"], state.ui_show_power_window)
    set_button_state(labels["lap_button"], state.ui_show_lap_window)
    set_button_state(labels["bsfc_button"], state.ui_show_bsfc_window)
    set_button_state(labels["debug_button"], state.ui_show_debug_window)


def render(state, window_size):
    if not _AC_OK:
        return

    geo = layout(window_size)
    x, y, w, h = geo["body_rect"]
    if w <= 10 or h <= 10:
        return

    _draw_rect(x, y, w, h, (0.07, 0.09, 0.11, 0.78))
    _draw_rect(x + 1, y + 1, w - 2, 4, (0.22, 0.25, 0.29, 0.25))
    _draw_outline(x, y, w, h, (0.72, 0.76, 0.82, 0.18))
    _draw_line(x + BUTTON_COL_W, y + 4, x + BUTTON_COL_W, y + h - 4, (0.78, 0.82, 0.88, 0.14))

    for idx, key in enumerate(("avg_econ", "pace_delta", "engine")):
        rx, ry, rw, rh = geo["value_rects"][key]
        if idx < 2:
            divider_x = rx + rw
            _draw_line(divider_x, ry + 4, divider_x, ry + rh - 4, (0.78, 0.82, 0.88, 0.14))
        if key == "engine":
            accent = _engine_color(state.engine_on)
            _draw_rect(rx + 10, ry + 8, rw - 20, rh - 16, (accent[0], accent[1], accent[2], 0.11))
            _draw_outline(rx + 10, ry + 8, rw - 20, rh - 16, (accent[0], accent[1], accent[2], 0.28))


def _apply_layout(labels, size):
    geo = layout(size)
    move(labels["power_button"], geo["buttons"]["power"][0], geo["buttons"]["power"][1], BUTTON_W, BUTTON_H)
    move(labels["lap_button"], geo["buttons"]["lap"][0], geo["buttons"]["lap"][1], BUTTON_W, BUTTON_H)
    move(labels["bsfc_button"], geo["buttons"]["bsfc"][0], geo["buttons"]["bsfc"][1], BUTTON_W + 10, BUTTON_H)
    move(labels["debug_button"], geo["buttons"]["debug"][0], geo["buttons"]["debug"][1], BUTTON_W, BUTTON_H)
    move(labels["run_id"], int(size[0] - 180), 8, 170, 14)

    for key in ("avg_econ", "pace_delta", "engine"):
        rect = geo["value_rects"][key]
        move(labels["val_" + key], int(rect[0]), int(rect[1] + rect[3] * 0.18), int(rect[2]), int(rect[3] * 0.64))


def _fmt_kmpl(value):
    if value is None:
        return "---"
    return "{0} km/L".format(fmt_float(value, 1))


def _fmt_pace_delta(value):
    if value is None:
        return "---"
    return "{0} s".format(fmt_sign(value, 1))


def _econ_color(value):
    if value is None:
        return (0.95, 0.95, 0.95, 1.0)
    if value >= 550.0:
        return (0.30, 1.00, 0.30, 1.0)
    if value >= 350.0:
        return (1.00, 0.92, 0.25, 1.0)
    return (1.00, 0.45, 0.45, 1.0)


def _pace_color(value):
    if value is None:
        return (0.95, 0.95, 0.95, 1.0)
    if value > 10.0:
        return (0.30, 1.00, 0.30, 1.0)
    if value < -5.0:
        return (1.00, 0.40, 0.40, 1.0)
    return (1.00, 1.00, 0.30, 1.0)


def _engine_color(engine_on):
    return (0.30, 1.00, 0.40, 1.0) if engine_on else (1.00, 0.40, 0.40, 1.0)


def _draw_rect(x, y, w, h, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_outline(x, y, w, h, color):
    _draw_line(x, y, x + w, y, color)
    _draw_line(x, y + h, x + w, y + h, color)
    _draw_line(x, y, x, y + h, color)
    _draw_line(x + w, y, x + w, y + h, color)


def _draw_line(x0, y0, x1, y1, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(x0, y0)
    ac.glVertex2f(x1, y1)
    ac.glEnd()
