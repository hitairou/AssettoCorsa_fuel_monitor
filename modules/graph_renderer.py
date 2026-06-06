# modules/graph_renderer.py
# GL renderer for the 10-second power graph.

try:
    import math
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
    ("hist_engine", "current_P_engine", 1.0, 1.0, 1.0),
    ("hist_roll", "current_P_roll", 0.3, 1.0, 0.3),
    ("hist_aero", "current_P_aero", 0.3, 0.8, 1.0),
    ("hist_accel", "current_P_accel_term", 1.0, 0.6, 0.2),
    ("hist_grade", "current_P_grade_term", 1.0, 0.4, 0.9),
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
    if not hasattr(state, "graph_renderer_diag"):
        state.graph_renderer_diag = {}

    for attr, current_attr, r, g, b in SERIES:
        buf = getattr(state, attr, None)
        if buf is None:
            continue

        values = buf.to_list()
        current_value = getattr(state, current_attr, None)

        try:
            points = _build_series_points(values, current_value, x, y, w, h, scale)
        except Exception as exc:
            _record_series_diag(state, attr, None, None, None, None, None, None, "build failed: {0}".format(exc))
            continue

        if not points:
            _record_series_diag(state, attr, None, None, None, None, None, None, "no valid points")
            continue

        try:
            ac.glColor4f(r, g, b, 0.9)
            ac.glBegin(_GL_LINE_STRIP)
            for px, py in points:
                ac.glVertex2f(px, py)
            ac.glEnd()
        except Exception as exc:
            _record_series_diag(
                state,
                attr,
                points[-1][0],
                points[-1][1],
                points[-1][0],
                points[-1][1],
                points[-1][0],
                points[-1][1],
                "line failed: {0}".format(exc),
            )
            continue

        dot_px, dot_py = points[-1]
        try:
            ac.glColor4f(r, g, b, 0.96)
            ac.glBegin(_GL_QUADS)
            ac.glVertex2f(dot_px - 2.2, dot_py - 2.2)
            ac.glVertex2f(dot_px + 2.2, dot_py - 2.2)
            ac.glVertex2f(dot_px + 2.2, dot_py + 2.2)
            ac.glVertex2f(dot_px - 2.2, dot_py + 2.2)
            ac.glEnd()
        except Exception as exc:
            _record_series_diag(
                state,
                attr,
                points[0][0],
                points[0][1],
                points[-1][0],
                points[-1][1],
                dot_px,
                dot_py,
                "dot failed: {0}".format(exc),
            )
            continue

        _record_series_diag(
            state,
            attr,
            points[0][0],
            points[0][1],
            points[-1][0],
            points[-1][1],
            dot_px,
            dot_py,
            "",
        )


def _build_series_points(values, current_value, x, y, w, h, scale):
    history = []
    for value in values:
        try:
            if not _valid_power_value(value):
                continue
            history.append(float(value))
        except Exception:
            continue

    points = []
    live_gap = min(max(6.0, w * 0.015), 10.0)
    history_width = max(w - live_gap, 1.0)

    history_count = len(history)
    if history_count:
        if history_count == 1:
            history_x_positions = [x + history_width]
        else:
            denom = float(history_count - 1)
            history_x_positions = [x + (float(idx) / denom) * history_width for idx in range(history_count)]
        for power_w, px in zip(history, history_x_positions):
            py = _power_to_clamped_py(power_w, y, h, scale)
            points.append((px, py))

    current_value = _to_float_or_none(current_value)
    if current_value is not None and _valid_power_value(current_value):
        current_px = x + w
        current_py = _power_to_clamped_py(current_value, y, h, scale)
        if not points:
            points.append((current_px, current_py))
        else:
            last_px, last_py = points[-1]
            if last_px != current_px or last_py != current_py:
                points.append((current_px, current_py))
            else:
                points[-1] = (current_px, current_py)

    return points


def _power_to_py(power_w, y, height, scale):
    center = y + height / 2.0
    px_per_w = (height / 2.0) / max(scale, 1.0)
    return center - power_w * px_per_w


def _power_to_clamped_py(power_w, y, height, scale):
    py = _power_to_py(power_w, y, height, scale)
    return max(y, min(y + height, py))


def _valid_power_value(value):
    try:
        value = float(value)
    except Exception:
        return False
    if math.isnan(value) or math.isinf(value):
        return False
    return True


def _to_float_or_none(value):
    try:
        return float(value)
    except Exception:
        return None


def _record_series_diag(state, attr, hist_x, hist_y, last_x, last_y, dot_x, dot_y, error):
    diag = getattr(state, "graph_renderer_diag", None)
    if diag is None:
        diag = {}
        state.graph_renderer_diag = diag
    diag[attr] = {
        "hist_last": (hist_x, hist_y),
        "current": (dot_x, dot_y),
        "last_point": (last_x, last_y),
        "error": error,
    }


def _sample_to_px(index, count, x, width):
    if count <= 1:
        return x + width
    return x + (float(index) / (count - 1)) * width
