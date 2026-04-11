# modules/bsfc_renderer.py
# GL renderer for BSFC heatmap, trace, current point, and gear candidates.

import math

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


def init(bsfc_interp):
    global _rpm_min, _rpm_max, _load_min, _load_max, _bg_cells, _cell_labels

    _bg_cells = []
    _cell_labels = []
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


def get_cell_labels():
    return list(_cell_labels)


def draw(state, rect):
    if not _AC_OK:
        return

    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    dim = 1.0 if state.engine_on else 0.38
    _draw_background(rect, dim)
    _draw_heatmap(rect, dim)
    _draw_grid(rect, dim)
    _draw_trace(state, rect, dim)
    _draw_gear_candidates(state, rect, dim)
    _draw_current_point(state, rect, dim)


def _draw_background(rect, dim):
    x, y, w, h = rect
    ac.glColor4f(0.06, 0.06, 0.06, 0.88 * dim + 0.10)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_heatmap(rect, dim):
    for rpm0, rpm1, load0, load1, r, g, b in _bg_cells:
        x0 = _rpm_to_px(rpm0, rect)
        x1 = _rpm_to_px(rpm1, rect)
        y0 = _load_to_py(load1, rect)
        y1 = _load_to_py(load0, rect)
        ac.glColor4f(r, g, b, 0.58 * dim)
        ac.glBegin(_GL_QUADS)
        ac.glVertex2f(x0, y0)
        ac.glVertex2f(x1, y0)
        ac.glVertex2f(x1, y1)
        ac.glVertex2f(x0, y1)
        ac.glEnd()


def _draw_grid(rect, dim):
    x, y, w, h = rect
    ac.glColor4f(0.42, 0.42, 0.42, 0.44 * dim)

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


def _draw_trace(state, rect, dim):
    trace_rpm = state.bsfc_trace_rpm.to_list()
    trace_load = state.bsfc_trace_load.to_list()
    count = min(len(trace_rpm), len(trace_load))
    if count < 2:
        return

    segments = []
    prev = None
    for idx in range(count):
        rpm = float(trace_rpm[idx])
        load = float(trace_load[idx])
        if not _valid_point(rpm, load):
            prev = None
            continue
        cur = (_rpm_to_px(rpm, rect), _load_to_py(load, rect))
        if prev is not None:
            segments.append((prev, cur, idx))
        prev = cur

    if not segments:
        return

    total = float(max(count - 1, 1))
    for p0, p1, idx in segments:
        age = float(idx) / total
        alpha = (0.14 + age * 0.72) * dim
        color = (1.0, 0.96, 0.36)
        ac.glColor4f(color[0], color[1], color[2], alpha)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(p0[0], p0[1])
        ac.glVertex2f(p1[0], p1[1])
        ac.glEnd()


def _draw_current_point(state, rect, dim):
    if state.current_load_display_ratio is None:
        return

    px = _rpm_to_px(float(state.observed_rpm), rect)
    py = _load_to_py(float(state.current_load_display_ratio), rect)
    size = 5.0

    ac.glColor4f(1.0, 1.0, 1.0, 0.92 * dim)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(px - size, py - size)
    ac.glVertex2f(px + size, py - size)
    ac.glVertex2f(px + size, py + size)
    ac.glVertex2f(px - size, py + size)
    ac.glEnd()


def _draw_gear_candidates(state, rect, dim):
    for candidate in getattr(state, "bsfc_gear_candidates", []):
        rpm = float(candidate.get("rpm", 0.0))
        load = float(candidate.get("load", 0.0))
        if not _valid_point(rpm, load):
            continue
        px = _rpm_to_px(rpm, rect)
        py = _load_to_py(load, rect)
        size = 4.0 if candidate.get("is_current") else 2.8
        color = (1.0, 0.88, 0.28, 0.82 * dim) if candidate.get("is_current") else (0.88, 0.90, 0.96, 0.44 * dim)
        ac.glColor4f(color[0], color[1], color[2], color[3])
        ac.glBegin(_GL_QUADS)
        ac.glVertex2f(px - size, py - size)
        ac.glVertex2f(px + size, py - size)
        ac.glVertex2f(px + size, py + size)
        ac.glVertex2f(px - size, py + size)
        ac.glEnd()


def cell_label_position(rpm, load, rect):
    return _rpm_to_px(rpm, rect), _load_to_py(load, rect)


def _valid_point(rpm, load):
    return (
        not math.isnan(rpm) and
        not math.isnan(load) and
        not math.isinf(rpm) and
        not math.isinf(load)
    )


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
