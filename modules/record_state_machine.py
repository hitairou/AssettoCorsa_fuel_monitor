# modules/record_state_machine.py
# Manual / semi-auto recording state transitions.


def set_mode(state, mode):
    mode = str(mode or "manual")
    if mode not in ("manual", "semi_auto"):
        mode = "manual"
    state.record_mode = mode
    state.record_control_enabled = True
    if mode == "manual" and state.record_state == "armed":
        state.record_state = "idle"
    return True, "Mode: {0}".format("SEMI AUTO" if mode == "semi_auto" else "MANUAL")


def can_arm(state):
    gates = getattr(state, "gates", {})
    for kind in ("start", "lap", "finish"):
        gate = gates.get(kind)
        if not gate or not gate.get("enabled", True):
            return False
    return True


def start_manual(state):
    state.record_control_enabled = True
    state.record_mode = "manual"
    state.record_state = "running"
    state.measurement_finished = False
    return True, "Manual START"


def stop_manual(state):
    if state.record_mode != "manual" or state.record_state != "running":
        return False, "STOP ignored"
    state.record_state = "finished"
    return True, "Manual STOP"


def arm_semi_auto(state):
    state.record_control_enabled = True
    state.record_mode = "semi_auto"
    if not can_arm(state):
        return False, "Need start/lap/finish gates"
    state.record_state = "armed"
    state.measurement_finished = False
    return True, "SEMI AUTO armed"


def cancel_run(state):
    if state.record_state not in ("armed", "running"):
        return False, "CANCEL ignored"
    state.record_state = "idle"
    state.measurement_finished = False
    return True, "Run cancelled"


def reset_run(state):
    state.record_state = "idle"
    state.measurement_finished = False
    return True, "Run reset"


def handle_gate_trigger(state, gate_kind):
    gate_kind = str(gate_kind or "")
    if state.record_mode != "semi_auto":
        return None
    if gate_kind == "start" and state.record_state == "armed":
        state.record_state = "running"
        state.measurement_finished = False
        return "start"
    if gate_kind == "lap" and state.record_state == "running":
        return "lap"
    if gate_kind == "finish" and state.record_state == "running":
        state.record_state = "finished"
        return "finish"
    return None
