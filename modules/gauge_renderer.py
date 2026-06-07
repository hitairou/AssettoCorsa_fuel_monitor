# modules/gauge_renderer.py
# GL renderer for power bars and drivetrain loss energy meter.

try:
    import ac
    import acsys
    from modules import panel_power
    _GL_LINES = acsys.GL.Lines
    _GL_QUADS = acsys.GL.Quads
    _AC_OK = True
except (ImportError, AttributeError):
    _AC_OK = False
    _GL_LINES = 1
    _GL_QUADS = 7
    panel_power = None


POWER_SCALE = 2000.0
ENERGY_SCALE_J = 5000.0


def draw(state, power_rect, estore_rect):
    if not _AC_OK:
        return

    size = tuple(state.ui_window_sizes.get("power", panel_power.WINDOW_SIZE)) if panel_power is not None else None
    geo = panel_power.layout(size) if panel_power is not None and size is not None else None

    _draw_power_bar(state, power_rect, geo["bar_rows"] if geo is not None else None)
    _draw_energy_bar(state, estore_rect, geo["energy_row"] if geo is not None else None)


def _draw_power_bar(state, rect, row_geos):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return

    if not row_geos:
        return

    power_scale = max(float(getattr(state, "power_graph_scale_w", POWER_SCALE)), 500.0)
    values = {
        "roll": state.demand_roll_power_w,
        "aero": state.demand_aero_power_w,
        "accel": state.demand_accel_power_w,
        "grade": state.demand_grade_power_w,
        "wheel": state.demand_wheel_power_w,
        "engine_supply": getattr(state, "engine_supply_power_w", 0.0),
        "drivetrain_loss": getattr(state, "drivetrain_loss_power_w", 0.0),
    }

    for row in row_geos:
        key = row["key"]
        power_w = float(values.get(key, 0.0))
        r, g, b, _alpha = row["color"]
        width_px = _signed_width(power_w, w, power_scale, row["mode"])
        bg_rect = (x, row["bar_y"] - 1.0, w, row["bar_h"] + 2.0)
        _draw_background(bg_rect)
        center_x = x + w / 2.0
        if row["mode"] == "signed":
            ac.glColor4f(0.7, 0.7, 0.7, 0.9)
            ac.glBegin(_GL_LINES)
            ac.glVertex2f(center_x, bg_rect[1] + 1.0)
            ac.glVertex2f(center_x, bg_rect[1] + bg_rect[3] - 1.0)
            ac.glEnd()
        _draw_bar(center_x, row["bar_y"], row["bar_h"], width_px, r, g, b, row["mode"])


def _draw_energy_bar(state, rect, row_geo):
    x, y, w, h = rect
    if w <= 4 or h <= 4:
        return
    if row_geo is None:
        return

    _draw_background(rect)

    left_x = x + 2.0
    right_x = x + w - 2.0
    ac.glColor4f(0.7, 0.7, 0.7, 0.9)
    ac.glBegin(_GL_LINES)
    ac.glVertex2f(left_x, y + h / 2.0)
    ac.glVertex2f(right_x, y + h / 2.0)
    ac.glEnd()

    energy_j = float(getattr(state, "drivetrain_loss_energy_j", 0.0))
    energy_scale = max(float(getattr(state, "net_energy_balance_scale_j", ENERGY_SCALE_J)), 1000.0)
    usable = max(right_x - left_x, 1.0)
    width_px = max(0.0, min(usable, (max(energy_j, 0.0) / max(energy_scale, 1e-9)) * usable))
    color = (0.35, 0.75, 1.0)
    _draw_positive_bar(left_x, row_geo["bar_y"], row_geo["bar_h"], width_px, color[0], color[1], color[2])


def _draw_background(rect):
    x, y, w, h = rect
    ac.glColor4f(0.08, 0.08, 0.08, 0.85)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(x, y)
    ac.glVertex2f(x + w, y)
    ac.glVertex2f(x + w, y + h)
    ac.glVertex2f(x, y + h)
    ac.glEnd()


def _signed_width(value, total_width, scale, mode):
    half = total_width / 2.0
    if mode == "positive":
        return _positive_width(value, total_width, scale)
    width_px = (value / max(scale, 1e-9)) * half
    return max(-half + 2.0, min(half - 2.0, width_px))


def _positive_width(value, total_width, scale):
    usable = max(total_width / 2.0 - 2.0, 1.0)
    width_px = max(0.0, float(value)) / max(scale, 1e-9) * usable
    return max(0.0, min(usable, width_px))


def _draw_bar(left_x, y, height, width_px, r, g, b, mode):
    if abs(width_px) < 1.0:
        return
    if mode == "positive":
        x0 = left_x
        x1 = left_x + width_px
    else:
        center_x = left_x
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


def _draw_positive_bar(left_x, y, height, width_px, r, g, b):
    if width_px < 1.0:
        return
    ac.glColor4f(r, g, b, 0.85)
    ac.glBegin(_GL_QUADS)
    ac.glVertex2f(left_x, y)
    ac.glVertex2f(left_x + width_px, y)
    ac.glVertex2f(left_x + width_px, y + height)
    ac.glVertex2f(left_x, y + height)
    ac.glEnd()
