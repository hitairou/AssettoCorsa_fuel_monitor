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

    state.graph_renderer_diag = {}
    scale = max(float(getattr(state, "power_graph_scale_w", Y_MAX)), 1.0)
    strategy = getattr(state, "strategy", {})
    window_s = float(strategy.get("power_graph_window_s", 10.0))
    _draw_background(x, y, w, h)
    _draw_grid(x, y, w, h, scale)
    _draw_series(state, x, y, w, h, scale, window_s)


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


def _draw_series(state, x, y, w, h, scale, window_s):
    if not hasattr(state, "graph_renderer_diag"):
        state.graph_renderer_diag = {}

    for attr, current_attr, r, g, b in SERIES:
        buf = getattr(state, attr, None)
        if buf is None:
            continue

        values = buf.to_list()
        times_buf = getattr(state, "hist_power_time", None)
        times = times_buf.to_list() if times_buf is not None else []
        current_value = getattr(state, current_attr, None)
        now = _render_time_s(state)

        try:
            points, diag = _build_series_points(times, values, now, current_value, x, y, w, h, scale, window_s)
        except Exception as exc:
            _record_series_diag(state, attr, None, None, None, "build failed: {0}".format(exc), meta=None)
            continue

        if not points:
            _record_series_diag(state, attr, None, None, None, "no valid points", meta=diag)
            continue

        try:
            ac.glColor4f(r, g, b, 0.9)
            ac.glBegin(_GL_LINE_STRIP)
            for px, py in points:
                ac.glVertex2f(px, py)
            ac.glEnd()
        except Exception as exc:
            _record_series_diag(state, attr, points[0] if points else None, points[-2] if len(points) >= 2 else None, points[-1] if points else None, "line failed: {0}".format(exc), meta=diag)
            continue

        if len(points) >= 2:
            try:
                ac.glColor4f(r, g, b, 0.96)
                ac.glBegin(_GL_LINES)
                ac.glVertex2f(points[-2][0], points[-2][1])
                ac.glVertex2f(points[-1][0], points[-1][1])
                ac.glEnd()
            except Exception as exc:
                _record_series_diag(state, attr, points[0], points[-2] if len(points) >= 2 else None, points[-1], "tail failed: {0}".format(exc), meta=diag)
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
            _record_series_diag(state, attr, points[0], points[-2] if len(points) >= 2 else None, points[-1], "dot failed: {0}".format(exc), meta=diag)
            continue

        _record_series_diag(state, attr, points[0], points[-2] if len(points) >= 2 else None, points[-1], "", meta=diag)


def _build_series_points(times, values, now, current_value, x, y, w, h, scale, window_s):
    aligned_times, aligned_values = _align_samples(times, values)
    points = []
    dot_radius = 2.2
    current_x = x + max(w - dot_radius - 1.0, 0.0)
    live_gap = min(max(8.0, w * 0.02), 12.0)
    history_right_x = max(current_x - live_gap, x)
    history_width = max(history_right_x - x, 1.0)
    window_s = max(float(window_s), 0.1)
    visible_samples = []

    for sample_time, power_w in zip(aligned_times, aligned_values):
        sample_time = _to_float_or_none(sample_time)
        power_w = _to_float_or_none(power_w)
        if sample_time is None or power_w is None:
            continue
        age = float(now) - float(sample_time)
        if age < 0.0 or age > window_s:
            continue
        visible_samples.append((float(sample_time), float(power_w), float(age)))

    visible_samples.sort(key=lambda sample: sample[0])
    for sample_time, power_w, age in visible_samples:
        px = history_right_x - (age / window_s) * history_width
        py = _power_to_clamped_py(power_w, y, h, scale)
        points.append((px, py))

    current_value = _to_float_or_none(current_value)
    if current_value is not None and _valid_power_value(current_value):
        current_py = _power_to_clamped_py(current_value, y, h, scale)
        if not points:
            points.append((current_x, current_py))
        else:
            points.append((current_x, current_py))

    diag = {
        "now": float(now),
        "window_s": float(window_s),
        "hist_time_len": len(aligned_times),
        "hist_len": len(aligned_values),
        "last_time": float(aligned_times[-1]) if aligned_times else None,
        "last_value": float(aligned_values[-1]) if aligned_values else None,
    }
    return points, diag


def _power_to_py(power_w, y, height, scale):
    center = y + height / 2.0
    px_per_w = (height / 2.0) / max(scale, 1.0)
    return center - power_w * px_per_w


def _power_to_clamped_py(power_w, y, height, scale):
    py = _power_to_py(power_w, y, height, scale)
    return max(y, min(y + height, py))


def _align_samples(times, values):
    times = list(times)
    values = list(values)
    count = min(len(times), len(values))
    if count <= 0:
        return [], []
    times = times[-count:]
    values = values[-count:]
    return times, values


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


def _record_series_diag(state, attr, first_point, prev_point, current_point, error, meta=None):
    diag = getattr(state, "graph_renderer_diag", None)
    if diag is None:
        diag = {}
        state.graph_renderer_diag = diag
    diag[attr] = {
        "first_point": first_point,
        "tail_prev": prev_point,
        "tail_current": current_point,
        "error": error,
        "meta": meta or {},
    }


def _render_time_s(state):
    value = _to_float_or_none(getattr(state, "render_time_s", None))
    if value is not None:
        return value
    return _to_float_or_none(getattr(state, "session_elapsed_time", 0.0)) or 0.0
