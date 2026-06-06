# modules/bsfc_renderer.py
# GL renderer for BSFC heatmap, current point, and 10-second trace.

import math
import os
import tempfile

try:
    import ac
    import acsys
    _GL_LINE_STRIP = acsys.GL.LineStrip
    _GL_LINES = acsys.GL.Lines
    _GL_QUADS = acsys.GL.Quads
    _AC_OK = True
except (ImportError, AttributeError):
    _AC_OK = False
    _GL_LINE_STRIP = 3
    _GL_LINES = 1
    _GL_QUADS = 7


_rpm_min = 1000.0
_rpm_max = 6000.0
_load_min = 0.0
_load_max = 1.0
_bg_cells = []
_cell_labels = []
_font_index = None
_shadow_font_index = None
_debug_log_path = os.path.join(tempfile.gettempdir(), "ecoran_bsfc_render_debug.txt")
_debug_logged_draw = False


def init(bsfc_interp):
    global _rpm_min, _rpm_max, _load_min, _load_max, _bg_cells, _cell_labels
    global _font_index, _shadow_font_index, _debug_logged_draw

    _bg_cells = []
    _cell_labels = []
    _font_index = None
    _shadow_font_index = None
    _debug_logged_draw = False
    rpm_axis = getattr(bsfc_interp, "rpm_axis", [])
    load_axis = getattr(bsfc_interp, "load_axis", [])

    if not rpm_axis or not load_axis:
        return

    _rpm_min = float(rpm_axis[0])
    _rpm_max = float(rpm_axis[-1])
    _load_min = float(load_axis[0])
    _load_max = float(load_axis[-1])

    for ridx in range(len(rpm_axis) - 1):
        for lidx in range(len(load_axis) - 1):
            rpm0 = float(rpm_axis[ridx])
            rpm1 = float(rpm_axis[ridx + 1])
            load0 = float(load_axis[lidx])
            load1 = float(load_axis[lidx + 1])
            rpm_c = (rpm0 + rpm1) / 2.0
            load_c = (load0 + load1) / 2.0
            bsfc = bsfc_interp.query(rpm_c, load_c)
            r, g, b = _bsfc_to_color(bsfc)
            _bg_cells.append((rpm0, rpm1, load0, load1, r, g, b))
            _cell_labels.append({
                "rpm": rpm_c,
                "load": load_c,
                "text": str(int(round(bsfc))),
            })

    _init_fonts()
    _debug_log(
        "init cells={0} font={1} shadow={2}".format(
            len(_cell_labels), _font_index, _shadow_font_index
        )
    )


def get_cell_labels():
    return list(_cell_labels)


def draw(state, rect):
    if not _AC_OK:
        return

    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    _draw_background(rect)
    _draw_heatmap(rect)
    _draw_grid(rect)
    _draw_cell_labels(rect)
    _draw_trace(state, rect)
    _draw_current_point(state, rect)


def _draw_background(rect):
    x, y, w, h = rect
    ac.glColor4f(0.06, 0.06, 0.06, 0.88)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_heatmap(rect):
    for rpm0, rpm1, load0, load1, r, g, b in _bg_cells:
        x0 = _rpm_to_px(rpm0, rect)
        x1 = _rpm_to_px(rpm1, rect)
        y0 = _load_to_py(load1, rect)
        y1 = _load_to_py(load0, rect)
        ac.glColor4f(r, g, b, 0.58)
        ac.glBegin(_GL_QUADS)
        ac.glVertex2f(x0, y0)
        ac.glVertex2f(x1, y0)
        ac.glVertex2f(x1, y1)
        ac.glVertex2f(x0, y1)
        ac.glEnd()


def _draw_grid(rect):
    x, y, w, h = rect
    ac.glColor4f(0.42, 0.42, 0.42, 0.44)

    for rpm in (1000, 2000, 3000, 4000, 5000, 6000):
        px = _rpm_to_px(float(rpm), rect)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(px, y)
        ac.glVertex2f(px, y + h)
        ac.glEnd()

    for load in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        py = _load_to_py(load, rect)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(x, py)
        ac.glVertex2f(x + w, py)
        ac.glEnd()


def _draw_cell_labels(rect):
    if not _cell_labels or _font_index is None:
        return

    global _debug_logged_draw
    if not _debug_logged_draw:
        _debug_logged_draw = True
        _debug_log("draw cell labels count={0} rect={1}".format(len(_cell_labels), rect))

    for cell in _cell_labels:
        px = _rpm_to_px(cell["rpm"], rect)
        py = _load_to_py(cell["load"], rect)
        text = str(cell["text"])
        shadow_pos = (px + 1.0, py + 1.0)
        text_pos = (px, py)
        try:
            ac.ext_glFontColor(_shadow_font_index, (0.0, 0.0, 0.0, 0.85))
            ac.ext_glFontUse(_shadow_font_index, text, shadow_pos, 1.0, 2)
            ac.ext_glFontColor(_font_index, (1.0, 1.0, 1.0, 1.0))
            ac.ext_glFontUse(_font_index, text, text_pos, 1.0, 2)
        except Exception:
            continue


def _draw_trace(state, rect):
    trace_rpm = state.bsfc_trace_rpm.to_list()
    trace_load = state.bsfc_trace_load.to_list()
    count = min(len(trace_rpm), len(trace_load))
    if count < 2:
        return

    ac.glColor4f(1.0, 1.0, 0.3, 0.7)
    drawing = False
    for idx in range(count):
        rpm = float(trace_rpm[idx])
        load = float(trace_load[idx])
        if math.isnan(rpm) or math.isnan(load) or math.isinf(rpm) or math.isinf(load):
            if drawing:
                ac.glEnd()
                drawing = False
            continue
        if not drawing:
            ac.glBegin(_GL_LINE_STRIP)
            drawing = True
        ac.glVertex2f(_rpm_to_px(rpm, rect), _load_to_py(load, rect))
    if drawing:
        ac.glEnd()


def _draw_current_point(state, rect):
    if state.current_load_display_ratio is None:
        return

    px = _rpm_to_px(float(state.observed_rpm), rect)
    py = _load_to_py(float(state.current_load_display_ratio), rect)
    size = 7.0

    ac.glColor4f(1.0, 0.18, 0.82, 0.98)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(px - size, py - size)
    ac.glVertex2f(px + size, py - size)
    ac.glVertex2f(px + size, py + size)
    ac.glVertex2f(px - size, py + size)
    ac.glEnd()

    ac.glColor4f(1.0, 1.0, 1.0, 1.0)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(px - size * 0.9, py)
    ac.glVertex2f(px + size * 0.9, py)
    ac.glVertex2f(px, py - size * 0.9)
    ac.glVertex2f(px, py + size * 0.9)
    ac.glEnd()


def _init_fonts():
    global _font_index, _shadow_font_index
    if not _AC_OK:
        return
    if _font_index is not None and _shadow_font_index is not None:
        return
    try:
        _font_index = ac.ext_glFontCreate("arial", 8.5, 0, 400)
        _shadow_font_index = ac.ext_glFontCreate("arial", 8.5, 0, 400)
        _debug_log("font create ok font={0} shadow={1}".format(_font_index, _shadow_font_index))
    except Exception:
        _font_index = None
        _shadow_font_index = None
        _debug_log("font create failed")


def cell_label_position(rpm, load, rect):
    return _rpm_to_px(rpm, rect), _load_to_py(load, rect)


def _debug_log(message):
    try:
        with open(_debug_log_path, "a") as handle:
            handle.write(message + "\n")
    except Exception:
        pass


def _rpm_to_px(rpm, rect):
    x, _y, w, _h = rect
    frac = (float(rpm) - _rpm_min) / max(_rpm_max - _rpm_min, 1.0)
    frac = max(0.0, min(1.0, frac))
    return x + frac * w


def _load_to_py(load, rect):
    _x, y, _w, h = rect
    frac = (float(load) - _load_min) / max(_load_max - _load_min, 1.0)
    frac = max(0.0, min(1.0, frac))
    return y + h - frac * h


def _bsfc_to_color(bsfc, bsfc_min=250.0, bsfc_max=600.0):
    t = (bsfc - bsfc_min) / max(bsfc_max - bsfc_min, 1.0)
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        return (t * 2.0, 1.0, 0.0)
    return (1.0, (1.0 - t) * 2.0, 0.0)
