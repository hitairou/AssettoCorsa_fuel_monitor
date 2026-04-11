# modules/graph_renderer.py
# GL renderer for the 20-second power graph.

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


SERIES = [
    ("hist_engine", (0.92, 0.92, 0.95, 0.92)),
    ("hist_roll", (0.54, 0.88, 0.42, 0.92)),
    ("hist_aero", (0.40, 0.72, 0.96, 0.92)),
    ("hist_accel", (0.94, 0.42, 0.26, 0.92)),
    ("hist_grade", (0.92, 0.58, 0.24, 0.92)),
]


def draw(state, rect):
    if not _AC_OK:
        return

    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    scale = max(float(getattr(state, "power_graph_scale_w", 400.0)), 300.0)
    _draw_background(x, y, w, h)
    _draw_grid(x, y, w, h)
    _draw_zero_line(x, y, w, h)
    _draw_series(state, x, y, w, h, scale)


def _draw_background(x, y, w, h):
    ac.glColor4f(0.06, 0.07, 0.09, 0.88)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_grid(x, y, w, h):
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gx = x + frac * w
        ac.glColor4f(0.84, 0.86, 0.90, 0.12 if frac < 1.0 else 0.22)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(gx, y)
        ac.glVertex2f(gx, y + h)
        ac.glEnd()

    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        gy = y + frac * h
        ac.glColor4f(0.84, 0.86, 0.90, 0.10)
        ac.glBegin(_GL_LINES)
        ac.glVertex2f(x, gy)
        ac.glVertex2f(x + w, gy)
        ac.glEnd()


def _draw_zero_line(x, y, w, h):
    gy = y + h / 2.0
    ac.glColor4f(0.88, 0.90, 0.94, 0.26)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(x, gy)
    ac.glVertex2f(x + w, gy)
    ac.glEnd()


def _draw_series(state, x, y, w, h, scale):
    for attr, color in SERIES:
        buf = getattr(state, attr, None)
        if buf is None:
            continue

        values = buf.to_list()
        count = len(values)
        if count < 2:
            continue

        maxlen = max(getattr(buf, "maxlen", count), 2)
        offset = maxlen - count

        ac.glColor4f(color[0], color[1], color[2], color[3])
        ac.glBegin(_GL_LINE_STRIP)
        for idx, power_w in enumerate(values):
            px = _sample_to_px(offset + idx, maxlen, x, w)
            py = _power_to_py(power_w, y, h, scale)
            py = max(y + 2, min(y + h - 2, py))
            ac.glVertex2f(px, py)
        ac.glEnd()

        last_value = float(values[-1])
        dot_px = _sample_to_px(maxlen - 1, maxlen, x, w)
        dot_py = _power_to_py(last_value, y, h, scale)
        ac.glColor4f(color[0], color[1], color[2], 0.96)
        ac.glBegin(_GL_QUADS)
        ac.glVertex2f(dot_px - 2.2, dot_py - 2.2)
        ac.glVertex2f(dot_px + 2.2, dot_py - 2.2)
        ac.glVertex2f(dot_px + 2.2, dot_py + 2.2)
        ac.glVertex2f(dot_px - 2.2, dot_py + 2.2)
        ac.glEnd()


def _power_to_py(power_w, y, height, scale):
    center = y + height / 2.0
    px_per_w = (height / 2.0 - 4.0) / max(scale, 1.0)
    return center - float(power_w) * px_per_w


def _sample_to_px(index, count, x, width):
    if count <= 1:
        return x + width
    return x + (float(index) / float(count - 1)) * width
