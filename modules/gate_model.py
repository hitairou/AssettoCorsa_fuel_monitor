# modules/gate_model.py
# Gate geometry helpers and serialization-safe normalization.

import math


DEFAULT_HALF_WIDTH_M = 4.0
DEFAULT_MIN_SPEED_KMH = 3.0
DEFAULT_COOLDOWN_S = 2.0


def clamp(value, lower, upper):
    try:
        value = float(value)
    except Exception:
        value = lower
    return max(float(lower), min(float(upper), value))


def default_gate(kind):
    return {
        "kind": str(kind),
        "center_world": [0.0, 0.0, 0.0],
        "forward_world": [1.0, 0.0, 0.0],
        "tangent_world": [0.0, 0.0, 1.0],
        "half_width_m": DEFAULT_HALF_WIDTH_M,
        "directional": True,
        "cooldown_s": DEFAULT_COOLDOWN_S,
        "min_speed_kmh": DEFAULT_MIN_SPEED_KMH,
        "enabled": True,
    }


def _length_xz(vec3):
    try:
        return math.sqrt(float(vec3[0]) * float(vec3[0]) + float(vec3[2]) * float(vec3[2]))
    except Exception:
        return 0.0


def normalize_xz(vec3, fallback=None):
    if fallback is None:
        fallback = [1.0, 0.0, 0.0]
    length = _length_xz(vec3)
    if length < 1e-9:
        return [float(fallback[0]), 0.0, float(fallback[2])]
    return [float(vec3[0]) / length, 0.0, float(vec3[2]) / length]


def tangent_from_forward(forward_world):
    forward = normalize_xz(forward_world)
    return normalize_xz([-forward[2], 0.0, forward[0]], fallback=[0.0, 0.0, 1.0])


def resolve_forward_world(heading_rad, raw_velocity, fallback=None):
    if fallback is None:
        fallback = [1.0, 0.0, 0.0]

    velocity_len = _length_xz(raw_velocity)
    velocity_dir = None
    if velocity_len >= 1e-6:
        velocity_dir = [
            float(raw_velocity[0]) / velocity_len,
            0.0,
            float(raw_velocity[2]) / velocity_len,
        ]

    heading = None
    try:
        heading = float(heading_rad)
    except Exception:
        heading = None

    candidates = []
    if heading is not None:
        base_a = [math.cos(heading), 0.0, math.sin(heading)]
        base_b = [math.sin(heading), 0.0, math.cos(heading)]
        candidates.extend([base_a, [-base_a[0], 0.0, -base_a[2]]])
        candidates.extend([base_b, [-base_b[0], 0.0, -base_b[2]]])

    if velocity_dir is not None:
        best = None
        best_score = -1e9
        for candidate in candidates:
            forward = normalize_xz(candidate, fallback=fallback)
            score = forward[0] * velocity_dir[0] + forward[2] * velocity_dir[2]
            if score > best_score:
                best = forward
                best_score = score
        if best is not None:
            return best
        return velocity_dir

    if candidates:
        return normalize_xz(candidates[0], fallback=fallback)
    return normalize_xz(fallback, fallback=[1.0, 0.0, 0.0])


def create_gate(kind, center_world, forward_world,
                half_width_m=DEFAULT_HALF_WIDTH_M,
                directional=True,
                cooldown_s=DEFAULT_COOLDOWN_S,
                min_speed_kmh=DEFAULT_MIN_SPEED_KMH,
                enabled=True):
    gate = default_gate(kind)
    gate["center_world"] = _coerce_vec3(center_world, fallback=[0.0, 0.0, 0.0])
    gate["forward_world"] = normalize_xz(forward_world, fallback=[1.0, 0.0, 0.0])
    gate["tangent_world"] = tangent_from_forward(gate["forward_world"])
    gate["half_width_m"] = clamp(half_width_m, 1.0, 20.0)
    gate["directional"] = bool(directional)
    gate["cooldown_s"] = max(float(cooldown_s), 0.0)
    gate["min_speed_kmh"] = max(float(min_speed_kmh), 0.0)
    gate["enabled"] = bool(enabled)
    return gate


def normalize_gate(kind, payload):
    if not isinstance(payload, dict):
        return None
    gate = create_gate(
        kind,
        payload.get("center_world", [0.0, 0.0, 0.0]),
        payload.get("forward_world", [1.0, 0.0, 0.0]),
        half_width_m=payload.get("half_width_m", DEFAULT_HALF_WIDTH_M),
        directional=payload.get("directional", True),
        cooldown_s=payload.get("cooldown_s", DEFAULT_COOLDOWN_S),
        min_speed_kmh=payload.get("min_speed_kmh", DEFAULT_MIN_SPEED_KMH),
        enabled=payload.get("enabled", True),
    )
    tangent = payload.get("tangent_world")
    if tangent is not None:
        gate["tangent_world"] = tangent_from_forward(gate["forward_world"])
    return gate


def serialize_gate(gate):
    if not gate:
        return None
    normalized = normalize_gate(gate.get("kind", "gate"), gate)
    if normalized is None:
        return None
    return {
        "enabled": bool(normalized["enabled"]),
        "center_world": list(normalized["center_world"]),
        "forward_world": list(normalized["forward_world"]),
        "tangent_world": list(normalized["tangent_world"]),
        "half_width_m": float(normalized["half_width_m"]),
        "directional": bool(normalized["directional"]),
        "cooldown_s": float(normalized["cooldown_s"]),
        "min_speed_kmh": float(normalized["min_speed_kmh"]),
    }


def build_track_key(track_name, track_layout):
    track_name = _slugify(track_name or "unknown_track")
    track_layout = _slugify(track_layout or "default")
    return "{0}_{1}".format(track_name, track_layout)


def gate_defined(gate):
    return isinstance(gate, dict) and "center_world" in gate and "forward_world" in gate


def _coerce_vec3(value, fallback):
    try:
        return [float(value[0]), float(value[1]), float(value[2])]
    except Exception:
        return [float(fallback[0]), float(fallback[1]), float(fallback[2])]


def _slugify(text):
    try:
        text = str(text)
    except Exception:
        text = "unknown"
    cleaned = []
    prev_sep = False
    for ch in text.strip().lower():
        if ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            cleaned.append(ch)
            prev_sep = False
        else:
            if not prev_sep:
                cleaned.append("_")
            prev_sep = True
    result = "".join(cleaned).strip("_")
    return result or "default"
