# modules/graph_renderer.py
# GL renderer for the 10-second power graph.

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


Y_MAX = 2000.0

SERIES = [
    ("hist_engine", 1.0, 1.0, 1.0),
    ("hist_roll", 0.3, 1.0, 0.3),
    ("hist_aero", 0.3, 0.8, 1.0),
    ("hist_accel", 1.0, 0.6, 0.2),
    ("hist_grade", 1.0, 0.4, 0.9),
]


def draw(state, rect):
    if not _AC_OK:
        return

    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    scale = max(float(getattr(state, "power_graph_scale_w", Y_MAX)), 500.0)
    _draw_background(x, y, w, h)
    _draw_grid(x, y, w, h, scale)
    _draw_series(state, x, y, w, h, scale)


def _draw_background(x, y, w, h):
    ac.glColor4f(0.08, 0.08, 0.08, 0.85)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_grid(x, y, w, h, scale):
    for p_grid in (-scale, -scale * 0.5, 0.0, scale * 0.5, scale):
        gy = _power_to_py(p_grid, y, h, scale)
        if p_grid == 0.0:
            ac.glColor4f(0.8, 0.8, 0.8, 0.9)
        else:
            ac.glColor4f(0.3, 0.3, 0.3, 0.6)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(x, gy)
        ac.glVertex2f(x + w, gy)
        ac.glEnd()

    for frac in (0.0, 0.5, 1.0):
        gx = x + frac * w
        ac.glColor4f(0.25, 0.25, 0.25, 0.45)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(gx, y)
        ac.glVertex2f(gx, y + h)
        ac.glEnd()


def _draw_series(state, x, y, w, h, scale):
    for attr, r, g, b in SERIES:
        buf = getattr(state, attr, None)
        if buf is None:
            continue

        values = buf.to_list()
        count = len(values)
        if count < 2:
            continue

        ac.glColor4f(r, g, b, 0.9)
        ac.glBegin(_GL_LINE_STRIP)
        for idx, p_w in enumerate(values):
            px = _sample_to_px(idx, count, x, w)
            py = _power_to_py(p_w, y, h, scale)
            py = max(y, min(y + h, py))
            ac.glVertex2f(px, py)
        ac.glEnd()

        last_value = float(values[-1])
        dot_px = _sample_to_px(count - 1, count, x, w)
        dot_py = _power_to_py(last_value, y, h, scale)
        ac.glColor4f(r, g, b, 0.96)
        ac.glBegin(_GL_QUADS)
        ac.glVertex2f(dot_px - 2.2, dot_py - 2.2)
        ac.glVertex2f(dot_px + 2.2, dot_py - 2.2)
        ac.glVertex2f(dot_px + 2.2, dot_py + 2.2)
        ac.glVertex2f(dot_px - 2.2, dot_py + 2.2)
        ac.glEnd()


def _power_to_py(power_w, y, height, scale):
    center = y + height / 2.0
    px_per_w = (height / 2.0) / max(scale, 1.0)
    return center - power_w * px_per_w


def _sample_to_px(index, count, x, width):
    if count <= 1:
        return x + width
    return x + (float(index) / (count - 1)) * width
