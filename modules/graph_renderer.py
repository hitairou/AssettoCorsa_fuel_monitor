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
    ("engine", "current_P_engine", 1.0, 1.0, 1.0),
    ("roll", "current_P_roll", 0.3, 1.0, 0.3),
    ("aero", "current_P_aero", 0.3, 0.8, 1.0),
    ("accel", "current_P_accel_term", 1.0, 0.6, 0.2),
    ("grade", "current_P_grade_term", 1.0, 0.4, 0.9),
]


def draw(state, rect):
    if not _AC_OK:
        return

    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    state.graph_renderer_diag = {}
    strategy = getattr(state, "strategy", {})
    window_s = float(strategy.get("power_graph_window_s", 10.0))
    scale = max(float(getattr(state, "power_graph_scale_w", Y_MAX)), 1.0)

    _draw_background(x, y, w, h)
    _draw_grid(x, y, w, h, scale)
    _draw_series(state, x, y, w, h, scale, window_s)


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


def _draw_series(state, x, y, w, h, scale, window_s):
    trace_samples = getattr(state, "power_trace_samples", None)
    now = _render_time_s(state)

    for series_key, current_attr, r, g, b in SERIES:
        current_value = _to_float_or_none(getattr(state, current_attr, None))
        try:
            samples = _collect_power_samples(state, now, window_s, trace_samples)
            points, meta = _build_series_points(samples, series_key, current_value, now, x, y, w, h, scale, window_s)
        except Exception as exc:
            _record_series_diag(
                state,
                series_key,
                {
                    "now": now,
                    "window_s": window_s,
                    "sample_count": len(trace_samples) if trace_samples is not None else 0,
                    "visible_count": 0,
                    "first_visible_time": None,
                    "last_visible_time": None,
                    "last_visible_age": None,
                    "point_count": 0,
                    "points0": None,
                    "points_prev": None,
                    "points_last": None,
                    "scale": scale,
                    "error": "build failed: {0}".format(exc),
                },
            )
            continue

        if not points:
            meta["error"] = "no valid points"
            _record_series_diag(state, series_key, meta)
            continue

        try:
            ac.glColor4f(r, g, b, 0.9)
            ac.glBegin(_GL_LINE_STRIP)
            for px, py in points:
                ac.glVertex2f(px, py)
            ac.glEnd()
        except Exception as exc:
            meta["error"] = "line failed: {0}".format(exc)
            meta["points0"] = points[0] if points else None
            meta["points_prev"] = points[-2] if len(points) >= 2 else None
            meta["points_last"] = points[-1] if points else None
            meta["point_count"] = len(points)
            _record_series_diag(state, series_key, meta)
            continue

        if len(points) >= 2:
            try:
                ac.glColor4f(r, g, b, 0.96)
                ac.glBegin(_GL_LINES)
                ac.glVertex2f(points[-2][0], points[-2][1])
                ac.glVertex2f(points[-1][0], points[-1][1])
                ac.glEnd()
            except Exception as exc:
                meta["error"] = "tail failed: {0}".format(exc)
                meta["points0"] = points[0]
                meta["points_prev"] = points[-2] if len(points) >= 2 else None
                meta["points_last"] = points[-1]
                meta["point_count"] = len(points)
                _record_series_diag(state, series_key, meta)
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
            meta["error"] = "dot failed: {0}".format(exc)
            meta["points0"] = points[0]
            meta["points_prev"] = points[-2] if len(points) >= 2 else None
            meta["points_last"] = points[-1]
            meta["point_count"] = len(points)
            _record_series_diag(state, series_key, meta)
            continue

        meta["error"] = ""
        meta["points0"] = points[0]
        meta["points_prev"] = points[-2] if len(points) >= 2 else None
        meta["points_last"] = points[-1]
        meta["point_count"] = len(points)
        _record_series_diag(state, series_key, meta)


def _collect_power_samples(state, now, window_s, trace_samples):
    samples = []
    if trace_samples is not None and len(trace_samples) > 0:
        for sample in trace_samples.to_list():
            sample_time = _to_float_or_none(sample.get("t"))
            if sample_time is None:
                continue
            age = float(now) - sample_time
            if age < 0.0 or age > window_s:
                continue
            samples.append({
                "t": sample_time,
                "engine": _to_float_or_none(sample.get("engine")),
                "roll": _to_float_or_none(sample.get("roll")),
                "aero": _to_float_or_none(sample.get("aero")),
                "accel": _to_float_or_none(sample.get("accel")),
                "grade": _to_float_or_none(sample.get("grade")),
            })
    else:
        times_buf = getattr(state, "hist_power_time", None)
        series_pairs = (
            ("engine", "hist_engine"),
            ("roll", "hist_roll"),
            ("aero", "hist_aero"),
            ("accel", "hist_accel"),
            ("grade", "hist_grade"),
        )
        times = times_buf.to_list() if times_buf is not None else []
        for attr_name, hist_attr in series_pairs:
            hist_buf = getattr(state, hist_attr, None)
            if hist_buf is None:
                continue
            values = hist_buf.to_list()
            count = min(len(times), len(values))
            for sample_time, sample_value in zip(times[-count:], values[-count:]):
                sample_time = _to_float_or_none(sample_time)
                sample_value = _to_float_or_none(sample_value)
                if sample_time is None or sample_value is None:
                    continue
                age = float(now) - sample_time
                if age < 0.0 or age > window_s:
                    continue
                existing = None
                for sample in samples:
                    if abs(sample["t"] - sample_time) < 1e-6:
                        existing = sample
                        break
                if existing is None:
                    existing = {"t": sample_time, "engine": None, "roll": None, "aero": None, "accel": None, "grade": None}
                    samples.append(existing)
                existing[attr_name] = sample_value

    live_sample = {
        "t": float(now),
        "engine": _to_float_or_none(getattr(state, "current_P_engine", None)),
        "roll": _to_float_or_none(getattr(state, "current_P_roll", None)),
        "aero": _to_float_or_none(getattr(state, "current_P_aero", None)),
        "accel": _to_float_or_none(getattr(state, "current_P_accel_term", None)),
        "grade": _to_float_or_none(getattr(state, "current_P_grade_term", None)),
    }
    samples.append(live_sample)
    samples.sort(key=lambda sample: sample["t"])
    samples = _dedupe_samples(samples)
    return samples


def _dedupe_samples(samples):
    deduped = []
    for sample in samples:
        if deduped and abs(deduped[-1]["t"] - sample["t"]) < 1e-6:
            deduped[-1] = sample
        else:
            deduped.append(sample)
    return deduped


def _build_series_points(samples, series_key, current_value, now, x, y, w, h, scale, window_s):
    visible = [sample for sample in samples if sample.get(series_key) is not None and 0.0 <= now - float(sample["t"]) <= window_s]
    visible.sort(key=lambda sample: sample["t"])

    meta = {
        "now": float(now),
        "window_s": float(window_s),
        "sample_count": len(samples),
        "visible_count": len(visible),
        "first_visible_time": float(visible[0]["t"]) if visible else None,
        "last_visible_time": float(visible[-1]["t"]) if visible else None,
        "last_visible_age": float(now - visible[-1]["t"]) if visible else None,
        "point_count": 0,
        "points0": None,
        "points_prev": None,
        "points_last": None,
        "scale": float(scale),
        "error": "",
    }

    if not visible:
        live_value = _to_float_or_none(current_value)
        if live_value is None:
            return [], meta
        current_x = _current_x(x, w)
        current_py = _power_to_clamped_py(live_value, y, h, scale)
        point = (current_x, current_py)
        meta["visible_count"] = 0
        meta["points0"] = point
        meta["points_last"] = point
        meta["point_count"] = 1
        return [point], meta

    dense_count = max(120, int(window_s * 12.0))
    current_x = _current_x(x, w)
    time_width = max(current_x - x, 1.0)
    points = []

    for idx in range(dense_count):
        target_t = now - window_s + (window_s * float(idx) / float(dense_count - 1))
        if target_t < visible[0]["t"] or target_t > visible[-1]["t"]:
            continue
        value = _interpolate_sample_value(visible, series_key, target_t)
        if value is None:
            continue
        age = now - target_t
        px = current_x - (age / window_s) * time_width
        py = _power_to_clamped_py(value, y, h, scale)
        points.append((px, py))

    live_value = _to_float_or_none(current_value)
    if live_value is not None:
        live_point = (current_x, _power_to_clamped_py(live_value, y, h, scale))
        if not points or abs(points[-1][0] - live_point[0]) > 1e-6 or abs(points[-1][1] - live_point[1]) > 1e-6:
            points.append(live_point)

    if not points:
        return [], meta

    meta["points0"] = points[0]
    meta["points_prev"] = points[-2] if len(points) >= 2 else None
    meta["points_last"] = points[-1]
    meta["point_count"] = len(points)
    return points, meta


def _interpolate_sample_value(samples, series_key, target_t):
    if not samples:
        return None

    first = samples[0]
    last = samples[-1]
    if target_t <= first["t"]:
        value = first.get(series_key)
        return value if value is not None else None
    if target_t >= last["t"]:
        value = last.get(series_key)
        return value if value is not None else None

    left = samples[0]
    for right in samples[1:]:
        if target_t <= right["t"]:
            left_value = left.get(series_key)
            right_value = right.get(series_key)
            if left_value is None:
                return right_value
            if right_value is None:
                return left_value
            span = float(right["t"]) - float(left["t"])
            if span <= 1e-9:
                return right_value
            ratio = (float(target_t) - float(left["t"])) / span
            return float(left_value) + (float(right_value) - float(left_value)) * ratio
        left = right
    value = last.get(series_key)
    return value if value is not None else None


def _current_x(x, width):
    dot_radius = 2.2
    return x + max(width - dot_radius - 1.0, 0.0)


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


def _record_series_diag(state, series_key, meta):
    diag = getattr(state, "graph_renderer_diag", None)
    if diag is None:
        diag = {}
        state.graph_renderer_diag = diag
    diag[series_key] = meta


def _render_time_s(state):
    value = _to_float_or_none(getattr(state, "render_time_s", None))
    if value is not None:
        return value
    return _to_float_or_none(getattr(state, "session_elapsed_time", 0.0)) or 0.0
