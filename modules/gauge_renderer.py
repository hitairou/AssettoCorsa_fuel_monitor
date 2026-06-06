# modules/gauge_renderer.py
# GL renderer for power bars and net energy balance meter.

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


POWER_SCALE = 2000.0
ESTORE_SCALE = 5000.0


def draw(state, power_rect, estore_rect):
    if not _AC_OK:
        return
    _draw_power_bar(state, power_rect)
    _draw_estore_bar(state, estore_rect)


def _draw_power_bar(state, rect):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    _draw_background(rect)

    mid_x = x + w / 2.0
    ac.glColor4f(0.7, 0.7, 0.7, 0.9)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(mid_x, y + 2)
    ac.glVertex2f(mid_x, y + h - 2)
    ac.glEnd()

    row_gap = 2.0
    row_h = max((h - 10.0 - row_gap * 4.0) / 5.0, 6.0)
    row_y = y + 5.0
    power_scale = max(float(getattr(state, "power_graph_scale_w", POWER_SCALE)), 500.0)

    rows = [
        (state.demand_wheel_power_w, 0.9, 0.9, 0.2),
        (state.demand_accel_power_w, 1.0, 0.6, 0.2),
        (state.demand_grade_power_w, 1.0, 0.4, 0.9),
        (-state.demand_roll_power_w, 0.3, 1.0, 0.3),
        (-state.demand_aero_power_w, 0.3, 0.8, 1.0),
    ]

    for power_w, r, g, b in rows:
        width_px = _signed_width(power_w, w, power_scale)
        _draw_bar(mid_x, row_y, row_h, width_px, r, g, b)
        row_y += row_h + row_gap


def _draw_estore_bar(state, rect):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    _draw_background(rect)

    mid_x = x + w / 2.0
    ac.glColor4f(0.7, 0.7, 0.7, 0.9)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(mid_x, y + 2)
    ac.glVertex2f(mid_x, y + h - 2)
    ac.glEnd()

    estore_scale = max(float(getattr(state, "net_energy_balance_scale_j", ESTORE_SCALE)), 1000.0)
    width_px = _signed_width(state.net_energy_balance_j, w, estore_scale)
    if state.net_energy_balance_j >= 0.0:
        color = (0.2, 0.5, 1.0)
    else:
        color = (1.0, 0.3, 0.3)
    _draw_bar(mid_x, y + 3.0, h - 6.0, width_px, color[0], color[1], color[2])


def _draw_background(rect):
    x, y, w, h = rect
    ac.glColor4f(0.08, 0.08, 0.08, 0.85)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _signed_width(value, total_width, scale):
    half = total_width / 2.0
    width_px = (value / max(scale, 1e-9)) * half
    return max(-half + 2.0, min(half - 2.0, width_px))


def _draw_bar(center_x, y, height, width_px, r, g, b):
    if abs(width_px) < 1.0:
        return
    if width_px >= 0.0:
        x0 = center_x
        x1 = center_x + width_px
    else:
        x0 = center_x + width_px
        x1 = center_x
    ac.glColor4f(r, g, b, 0.85)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x0, y)
    ac.glVertex2f(x1, y)
    ac.glVertex2f(x1, y + height)
    ac.glVertex2f(x0, y + height)
    ac.glEnd()
