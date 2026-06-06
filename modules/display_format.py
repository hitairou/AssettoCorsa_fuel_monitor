# modules/display_format.py
# Formatting helpers for UI display values.

import math


def _finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def apply_gear_display_offset(raw_gear, gear_display_offset=-1):
    raw_gear = _finite(raw_gear)
    if raw_gear is None:
        return None
    offset = _finite(gear_display_offset)
    if offset is None:
        offset = -1.0
    return int(round(raw_gear + offset))


def fmt_float(value, digits=1, default="---"):
    value = _finite(value)
    if value is None:
        return default
    return ("{0:." + str(int(digits)) + "f}").format(value)


def fmt_int(value, default="---"):
    value = _finite(value)
    if value is None:
        return default
    return str(int(round(value)))


def fmt_sign(value, digits=1, default="---"):
    value = _finite(value)
    if value is None:
        return default
    return ("{0:+." + str(int(digits)) + "f}").format(value)


def fmt_time_ms(seconds, default="--:--.-"):
    seconds = _finite(seconds)
    if seconds is None:
        return default
    seconds = max(seconds, 0.0)
    minutes = int(seconds // 60.0)
    remain = seconds - minutes * 60.0
    if remain >= 59.95:
        minutes += 1
        remain = 0.0
    return "{0:02d}:{1:04.1f}".format(minutes, remain)


def fmt_display_gear(value, default="-"):
    value = _finite(value)
    if value is None:
        return default
    gear = int(round(value))
    if gear < 0:
        return "R"
    if gear == 0:
        return "N"
    return str(gear)


def fmt_gear(raw_gear, default="-"):
    return fmt_display_gear(raw_gear, default=default)


def fmt_rpm(value, default="---"):
    value = _finite(value)
    if value is None:
        return default
    rpm = int(round(value))
    if abs(rpm) < 100:
        rpm = 0
    return str(max(rpm, 0))


def fmt_w(value, digits=0, default="---"):
    return fmt_float(value, digits=digits, default=default)


def fmt_j(value, digits=0, default="---"):
    return fmt_float(value, digits=digits, default=default)


def fmt_kj(value, digits=1, default="---"):
    value = _finite(value)
    if value is None:
        return default
    return fmt_float(value / 1000.0, digits=digits, default=default)


def fmt_pct(value, digits=1, default="---"):
    return fmt_float(value, digits=digits, default=default)


def pace_delta_color(delta_s):
    delta_s = _finite(delta_s)
    if delta_s is None:
        return (1.0, 1.0, 1.0, 1.0)
    if delta_s > 10.0:
        return (0.3, 1.0, 0.3, 1.0)
    if delta_s < -5.0:
        return (1.0, 0.4, 0.4, 1.0)
    return (1.0, 1.0, 0.3, 1.0)
