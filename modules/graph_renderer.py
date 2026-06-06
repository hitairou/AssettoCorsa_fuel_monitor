# modules/graph_renderer.py
# GL renderer for the 10-second power graph.

try:
    import math
    import ac
    import acsys
    _GL_LINES = acsys.GL.Lines
    _GL_QUADS = acsys.GL.Quads
    _AC_OK = True
except (ImportError, AttributeError):
    _AC_OK = False
    _GL_LINES = 1
    _GL_QUADS = 7


Y_MAX = 2000.0
GRAPH_RENDERER_REV = "power-graph-segments-003"
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
    _draw_background(x, y, w, h)
    _draw_grid(x, y, w, h, scale)
    if _debug_overlay_enabled(state):
        _draw_test_frame(x, y, w, h, scale)
    _draw_series(state, x, y, w, h, scale)


def _draw_background(x, y, w, h):
    margin = 1.0
    ac.glColor4f(0.08, 0.08, 0.08, 1.0)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x - margin, y - margin)
    ac.glVertex2f(x + w + margin, y - margin)
    ac.glVertex2f(x + w + margin, y + h + margin)
    ac.glVertex2f(x - margin, y + h + margin)
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


def _draw_test_frame(x, y, w, h, scale):
    current_x = _current_x(x, w)
    ac.glColor4f(1.0, 0.2, 0.2, 0.85)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(current_x, y)
    ac.glVertex2f(current_x, y + h)
    ac.glEnd()


def _draw_series(state, x, y, w, h, scale):
    diag = {}
    first_error = ""
    for attr, current_attr, r, g, b in SERIES:
        buf = getattr(state, attr, None)
        values = buf.to_list() if buf is not None else []
        count = len(values)
        capacity = max(int(getattr(buf, "_maxlen", max(count, 1))), 1)
        current_x = _current_x(x, w)
        live_gap = min(max(8.0, w * 0.02), 12.0)
        history_right_x = max(current_x - live_gap, x)
        history_width = max(history_right_x - x, 1.0)
        dx = history_width / max(capacity - 1, 1)
        start_x = history_right_x - dx * max(count - 1, 0)

        segments = []
        prev = None
        last_valid_point = None
        first_valid_value = None
        last_valid_value = None
        valid_count = 0
        for idx, value in enumerate(values):
            if not _valid_power_value(value):
                prev = None
                continue
            value = float(value)
            px = start_x + dx * idx
            py = _power_to_clamped_py(value, y, h, scale)
            cur = (px, py)
            if first_valid_value is None:
                first_valid_value = value
            last_valid_value = value
            last_valid_point = cur
            valid_count += 1
            if prev is not None:
                segments.append((prev, cur, idx))
            prev = cur

        current_value = _to_float_or_none(getattr(state, current_attr, None))
        current_point = None
        if current_value is not None and _valid_power_value(current_value):
            current_point = (current_x, _power_to_clamped_py(current_value, y, h, scale))

        error = ""
        if segments:
            try:
                # AC Python OpenGL can show stale updates with long GL_LINES batches.
                # Match the BSFC renderer and submit each segment separately.
                total = float(max(count - 1, 1))
                for p0, p1, idx in segments:
                    age = float(idx) / total
                    alpha = 0.20 + age * 0.70
                    ac.glColor4f(r, g, b, alpha)
                    ac.glBegin(_GL_LINES)
                    ac.glVertex2f(p0[0], p0[1])
                    ac.glVertex2f(p1[0], p1[1])
                    ac.glEnd()
            except Exception as exc:
                error = "line failed: {0}".format(exc)
                if not first_error:
                    first_error = error

        if last_valid_point is not None and current_point is not None:
            try:
                ac.glColor4f(r, g, b, 0.96)
                ac.glBegin(_GL_LINES)
                ac.glVertex2f(last_valid_point[0], last_valid_point[1])
                ac.glVertex2f(current_point[0], current_point[1])
                ac.glEnd()
            except Exception as exc:
                error = error or "current link failed: {0}".format(exc)
                if not first_error:
                    first_error = error

        if current_point is not None:
            try:
                ac.glColor4f(r, g, b, 0.96)
                ac.glBegin(_GL_QUADS)
                ac.glVertex2f(current_point[0] - 2.2, current_point[1] - 2.2)
                ac.glVertex2f(current_point[0] + 2.2, current_point[1] - 2.2)
                ac.glVertex2f(current_point[0] + 2.2, current_point[1] + 2.2)
                ac.glVertex2f(current_point[0] - 2.2, current_point[1] + 2.2)
                ac.glEnd()
            except Exception as exc:
                error = error or "dot failed: {0}".format(exc)
                if not first_error:
                    first_error = error

        diag[attr] = {
            "raw_hist_len": len(values),
            "valid_hist_len": valid_count,
            "first_value": first_valid_value,
            "last_value": last_valid_value,
            "current_value": current_value,
            "first_point": segments[0][0] if segments else last_valid_point,
            "last_history_point": last_valid_point,
            "current_point": current_point,
            "history_capacity": capacity,
            "history_start_x": start_x,
            "current_x": current_x,
            "history_width": history_width,
            "graph_rect": (x, y, w, h),
            "scale": scale,
            "points_count": valid_count + (1 if current_point is not None else 0),
            "segments_count": len(segments),
            "error": error,
        }

    state.graph_renderer_diag = diag
    if first_error:
        state.last_render_error = "power_graph: {0}".format(first_error)


def _current_x(x, width):
    dot_radius = 2.2
    return x + max(width - dot_radius - 1.0, 0.0)


def _debug_overlay_enabled(state):
    strategy = getattr(state, "strategy", {}) or {}
    value = strategy.get("power_graph_debug_overlay", 0)
    try:
        return bool(int(value))
    except Exception:
        return str(value).strip().lower() in ("1", "true", "yes", "on")


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
        value = float(value)
    except Exception:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value
