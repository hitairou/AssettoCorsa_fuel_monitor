# modules/gate_detector.py
# Directional gate crossing detection on the XZ plane.


def dot_xz(a, b):
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1])


def project_xz(point3):
    return [float(point3[0]), float(point3[2])]


def detect_gate_cross(prev_pos3, curr_pos3, gate, speed_kmh, sim_time_s,
                      last_trigger_time, record_state,
                      run_elapsed_s=0.0, laps_completed=0,
                      minimum_valid_run_time_s=30.0,
                      minimum_valid_finish_lap_count=1):
    result = {
        "triggered": False,
        "reason": "",
        "s0": None,
        "s1": None,
        "u": None,
    }

    if prev_pos3 is None or curr_pos3 is None:
        result["reason"] = "missing_position"
        return result
    if not isinstance(gate, dict) or not gate.get("enabled", True):
        result["reason"] = "gate_disabled"
        return result

    kind = str(gate.get("kind", "gate"))
    if kind == "start" and record_state != "armed":
        result["reason"] = "state_not_armed"
        return result
    if kind == "lap" and record_state != "running":
        result["reason"] = "state_not_running"
        return result
    if kind == "finish" and record_state != "running":
        result["reason"] = "state_not_running"
        return result
    if kind == "finish":
        if (run_elapsed_s < float(minimum_valid_run_time_s) and
                int(laps_completed) < int(minimum_valid_finish_lap_count)):
            result["reason"] = "finish_guard"
            return result

    speed_kmh = float(speed_kmh)
    if speed_kmh < float(gate.get("min_speed_kmh", 3.0)):
        result["reason"] = "speed_guard"
        return result

    cooldown_s = max(float(gate.get("cooldown_s", 2.0)), 0.0)
    if float(sim_time_s) - float(last_trigger_time) < cooldown_s:
        result["reason"] = "cooldown"
        return result

    p0 = project_xz(prev_pos3)
    p1 = project_xz(curr_pos3)
    center = project_xz(gate.get("center_world", [0.0, 0.0, 0.0]))
    normal = project_xz(gate.get("forward_world", [1.0, 0.0, 0.0]))
    tangent = project_xz(gate.get("tangent_world", [0.0, 0.0, 1.0]))

    rel0 = [p0[0] - center[0], p0[1] - center[1]]
    rel1 = [p1[0] - center[0], p1[1] - center[1]]

    s0 = dot_xz(rel0, normal)
    s1 = dot_xz(rel1, normal)
    u = dot_xz(rel1, tangent)

    result["s0"] = s0
    result["s1"] = s1
    result["u"] = u

    directional = bool(gate.get("directional", True))
    if directional:
        crossed = (s0 < 0.0 and s1 >= 0.0)
    else:
        crossed = (s0 * s1 <= 0.0)
    if not crossed:
        result["reason"] = "no_cross"
        return result

    if abs(u) > float(gate.get("half_width_m", 4.0)):
        result["reason"] = "outside_width"
        return result

    result["triggered"] = True
    result["reason"] = "triggered"
    return result
