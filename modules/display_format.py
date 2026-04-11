# modules/display_format.py
# Formatting, color, and interpolation helpers for UI display values.

import math


def finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def is_valid_number(value):
    return finite(value) is not None


def clamp(value, lower, upper):
    value = finite(value)
    if value is None:
        return lower
    return max(lower, min(upper, value))


def lerp(a, b, t):
    return float(a) + (float(b) - float(a)) * float(t)


def inverse_lerp(a, b, value):
    value = finite(value)
    if value is None:
        return 0.0
    span = float(b) - float(a)
    if abs(span) < 1e-9:
        return 0.0
    return clamp((value - float(a)) / span, 0.0, 1.0)


def lerp_color(c0, c1, t):
    t = clamp(t, 0.0, 1.0)
    return (
        lerp(c0[0], c1[0], t),
        lerp(c0[1], c1[1], t),
        lerp(c0[2], c1[2], t),
        lerp(c0[3], c1[3], t),
    )


def blend_color_stops(value, stops):
    if not stops:
        return (1.0, 1.0, 1.0, 1.0)
    if len(stops) == 1:
        return stops[0][1]

    value = finite(value)
    if value is None:
        return stops[0][1]

    ordered = sorted(stops, key=lambda item: item[0])
    if value <= ordered[0][0]:
        return ordered[0][1]
    if value >= ordered[-1][0]:
        return ordered[-1][1]

    for idx in range(len(ordered) - 1):
        left = ordered[idx]
        right = ordered[idx + 1]
        if value <= right[0]:
            t = inverse_lerp(left[0], right[0], value)
            return lerp_color(left[1], right[1], t)
    return ordered[-1][1]


def with_alpha(color, alpha):
    return (color[0], color[1], color[2], alpha)


def dim_color(color, factor):
    factor = clamp(factor, 0.0, 1.0)
    return (
        color[0] * factor,
        color[1] * factor,
        color[2] * factor,
        color[3],
    )


def apply_gear_display_offset(raw_gear, gear_display_offset=-1):
    raw_gear = finite(raw_gear)
    if raw_gear is None:
        return None
    offset = finite(gear_display_offset)
    if offset is None:
        offset = -1.0
    return int(round(raw_gear + offset))


def fmt_float(value, digits=1, default="---"):
    value = finite(value)
    if value is None:
        return default
    return ("{0:." + str(int(digits)) + "f}").format(value)


def fmt_int(value, default="---"):
    value = finite(value)
    if value is None:
        return default
    return str(int(round(value)))


def fmt_sign(value, digits=1, default="---"):
    value = finite(value)
    if value is None:
        return default
    return ("{0:+." + str(int(digits)) + "f}").format(value)


def fmt_unit(value, unit, digits=1, default="---", scale=1.0):
    value = finite(value)
    if value is None:
        return default
    scaled = value / max(float(scale), 1e-12)
    return "{0} {1}".format(fmt_float(scaled, digits=digits, default=default), unit)


def fmt_signed_unit(value, unit, digits=1, default="---", scale=1.0):
    value = finite(value)
    if value is None:
        return default
    scaled = value / max(float(scale), 1e-12)
    return "{0} {1}".format(fmt_sign(scaled, digits=digits, default=default), unit)


def fmt_time_ms(seconds, default="--:--.-"):
    seconds = finite(seconds)
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
    value = finite(value)
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
    value = finite(value)
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
    value = finite(value)
    if value is None:
        return default
    return fmt_float(value / 1000.0, digits=digits, default=default)


def fmt_pct(value, digits=1, default="---"):
    return fmt_float(value, digits=digits, default=default)


def fmt_unit_or_dash(value, unit, digits=1, scale=1.0, default="---"):
    return fmt_unit(value, unit, digits=digits, scale=scale, default=default)


def fmt_vec3(vec3, digits=1, default="---"):
    try:
        return "[{0}, {1}, {2}]".format(
            fmt_float(vec3[0], digits=digits, default=default),
            fmt_float(vec3[1], digits=digits, default=default),
            fmt_float(vec3[2], digits=digits, default=default),
        )
    except Exception:
        return default


def fmt_vec3_unit(vec3, unit="m", digits=1, default="---"):
    text = fmt_vec3(vec3, digits=digits, default=default)
    if text == default:
        return default
    return "{0} {1}".format(text, unit)


def percentile(values, q, default=None):
    if not values:
        return default
    q = clamp(q, 0.0, 1.0)
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    idx = int(math.floor(pos))
    frac = pos - idx
    if idx >= len(ordered) - 1:
        return ordered[-1]
    return lerp(ordered[idx], ordered[idx + 1], frac)


def pace_delta_color(delta_s):
    delta_s = finite(delta_s)
    if delta_s is None:
        return (0.86, 0.88, 0.92, 1.0)
    return blend_color_stops(delta_s, [
        (-20.0, (0.88, 0.30, 0.30, 1.0)),
        (-5.0, (0.92, 0.64, 0.18, 1.0)),
        (0.0, (0.96, 0.88, 0.36, 1.0)),
        (20.0, (0.36, 0.82, 0.42, 1.0)),
    ])


def econ_color(econ_kmpl, warn_kmpl=350.0, good_kmpl=550.0):
    econ_kmpl = finite(econ_kmpl)
    if econ_kmpl is None:
        return (0.86, 0.88, 0.92, 1.0)
    mid = (float(warn_kmpl) + float(good_kmpl)) * 0.5
    return blend_color_stops(econ_kmpl, [
        (float(warn_kmpl), (0.84, 0.32, 0.30, 1.0)),
        (mid, (0.90, 0.78, 0.30, 1.0)),
        (float(good_kmpl), (0.32, 0.82, 0.42, 1.0)),
    ])


def engine_state_color(engine_on):
    if engine_on:
        return (0.34, 0.82, 0.48, 1.0)
    return (0.56, 0.62, 0.70, 1.0)


def heat_good_bad_color(value, low, high, higher_is_better=True,
                        neutral=(0.90, 0.92, 0.96, 1.0)):
    value = finite(value)
    low = finite(low)
    high = finite(high)
    if value is None or low is None or high is None:
        return neutral
    if abs(high - low) < 1e-9:
        return neutral

    if not higher_is_better:
        value = -value
        low, high = -high, -low

    return blend_color_stops(value, [
        (low, (0.86, 0.34, 0.34, 1.0)),
        ((low + high) * 0.5, (0.92, 0.86, 0.58, 1.0)),
        (high, (0.34, 0.80, 0.44, 1.0)),
    ])


def describe_estimate_source(source):
    source = str(source or "")
    mapping = {
        "inactive": "Inactive",
        "no_data": "No data",
        "completed_only": "Completed laps only",
        "completed_plus_provisional": "Completed + provisional",
        "provisional_only": "Provisional lap only",
        "insufficient_progress": "Waiting for enough provisional progress",
        "measurement_started": "Measurement running",
        "waiting_for_arm": "Waiting for ARM",
        "waiting_for_first_cross": "Waiting for first lap trigger",
        "gate_idle": "Gate mode idle",
        "gate_finished": "Gate run finished",
    }
    label = mapping.get(source, source.replace("_", " ").strip().title())
    if source:
        return "{0} ({1})".format(label, source)
    return label
