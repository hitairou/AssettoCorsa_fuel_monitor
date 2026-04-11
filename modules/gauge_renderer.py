# modules/gauge_renderer.py
# GL renderer for the stacked power bar and residual sparkline.

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


BREAKDOWN_SPECS = [
    ("engine", "Engine", "positive", lambda state: max(state.demand_engine_power_w, 0.0), (0.92, 0.92, 0.95, 0.92)),
    ("downhill", "Downhill", "positive", lambda state: max(-state.demand_grade_power_w, 0.0), (0.36, 0.84, 0.52, 0.92)),
    ("inertia", "Inertia", "positive", lambda state: max(-state.demand_accel_power_w, 0.0), (0.40, 0.76, 0.92, 0.92)),
    ("roll", "Roll", "negative", lambda state: max(state.demand_roll_power_w, 0.0), (0.54, 0.88, 0.42, 0.92)),
    ("aero", "Aero", "negative", lambda state: max(state.demand_aero_power_w, 0.0), (0.40, 0.72, 0.96, 0.92)),
    ("climb", "Climb", "negative", lambda state: max(state.demand_grade_power_w, 0.0), (0.94, 0.58, 0.22, 0.92)),
    ("accel", "Accel", "negative", lambda state: max(state.demand_accel_power_w, 0.0), (0.94, 0.42, 0.26, 0.92)),
]


def build_power_breakdown(state):
    rows = []
    total_abs = 0.0
    for key, label, side, fn, color in BREAKDOWN_SPECS:
        value = float(fn(state))
        total_abs += abs(value)
        rows.append({
            "key": key,
            "label": label,
            "side": side,
            "value_w": value,
            "color": color,
        })
    total_abs = max(total_abs, 1e-9)
    for row in rows:
        row["pct"] = abs(row["value_w"]) / total_abs * 100.0
    return rows


def draw(state, power_rect, residual_rect):
    if not _AC_OK:
        return
    _draw_stacked_bar(state, power_rect)
    _draw_residual_sparkline(state, residual_rect)


def _draw_stacked_bar(state, rect):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    rows = build_power_breakdown(state)
    scale = max(float(getattr(state, "power_graph_scale_w", 400.0)), 1.0)
    mid_x = x + w / 2.0

    _draw_background(rect, 0.82)
    _draw_line(mid_x, y + 2, mid_x, y + h - 2, (0.88, 0.90, 0.94, 0.34))

    half_w = w / 2.0 - 4.0
    pos_cursor = mid_x
    neg_cursor = mid_x

    for row in rows:
        width_px = min(abs(float(row["value_w"])) / scale * half_w, half_w)
        if width_px <= 0.6:
            continue
        if row["side"] == "positive":
            x0 = pos_cursor
            x1 = min(pos_cursor + width_px, x + w - 4.0)
            pos_cursor = x1
        else:
            x0 = max(neg_cursor - width_px, x + 4.0)
            x1 = neg_cursor
            neg_cursor = x0
        _draw_rect(x0, y + 5, x1 - x0, h - 10, row["color"])

    _draw_outline(rect, (0.82, 0.84, 0.88, 0.18))


def _draw_residual_sparkline(state, rect):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    _draw_background(rect, 0.82)
    scale = max(float(getattr(state, "net_energy_balance_scale_j", 1000.0)), 1000.0)
    zero_y = y + h / 2.0
    _draw_line(x, zero_y, x + w, zero_y, (0.86, 0.88, 0.92, 0.24))

    values = state.hist_residual_balance_j.to_list()
    count = len(values)
    if count >= 2:
        ac.glColor4f(0.40, 0.78, 1.0, 0.88)
        ac.glBegin(_GL_LINE_STRIP)
        maxlen = max(getattr(state.hist_residual_balance_j, "maxlen", count), 2)
        offset = maxlen - count
        for idx, value in enumerate(values):
            frac_x = float(offset + idx) / float(maxlen - 1)
            px = x + frac_x * w
            frac_y = max(-1.0, min(1.0, float(value) / scale))
            py = zero_y - frac_y * (h / 2.0 - 4.0)
            ac.glVertex2f(px, py)
        ac.glEnd()

        last_value = float(values[-1])
        px = x + w
        py = zero_y - max(-1.0, min(1.0, last_value / scale)) * (h / 2.0 - 4.0)
        _draw_rect(px - 2.5, py - 2.5, 5.0, 5.0, (0.82, 0.92, 1.0, 0.96))

    _draw_outline(rect, (0.82, 0.84, 0.88, 0.16))


def _draw_background(rect, alpha):
    x, y, w, h = rect
    _draw_rect(x, y, w, h, (0.06, 0.07, 0.09, alpha))


def _draw_rect(x, y, w, h, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _draw_line(x0, y0, x1, y1, color):
    ac.glColor4f(color[0], color[1], color[2], color[3])
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(x0, y0)
    ac.glVertex2f(x1, y1)
    ac.glEnd()


def _draw_outline(rect, color):
    x, y, w, h = rect
    _draw_line(x, y, x + w, y, color)
    _draw_line(x, y + h, x + w, y + h, color)
    _draw_line(x, y, x, y + h, color)
    _draw_line(x + w, y, x + w, y + h, color)
