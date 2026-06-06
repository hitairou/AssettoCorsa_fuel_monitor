# modules/telemetry_reader.py
# Wraps sim_info access.  All field-name variations are resolved here.
# Returns safe defaults on failure so the app never crashes on bad reads.

from modules.app_state import state

# sim_info singleton is imported once at module level to avoid repeated lookups
_sim_info = None

def _get_sim_info():
    global _sim_info
    if _sim_info is None:
        try:
            import sim_info as _si
            _sim_info = _si.info
        except Exception:
            _sim_info = None
    return _sim_info


def _safe_float(obj, *attrs):
    """Try each attribute name in turn; return 0.0 on any failure."""
    for attr in attrs:
        try:
            val = getattr(obj, attr)
            return float(val)
        except Exception:
            pass
    return 0.0


def _safe_int(obj, *attrs):
    for attr in attrs:
        try:
            val = getattr(obj, attr)
            return int(val)
        except Exception:
            pass
    return 0


def _safe_bool(obj, *attrs):
    for attr in attrs:
        try:
            return bool(int(getattr(obj, attr)))
        except Exception:
            pass
    return False


def _safe_vec3(obj, *attrs):
    """Return a [x,y,z] list; 0.0 on failure."""
    for attr in attrs:
        try:
            vec = getattr(obj, attr)
            return [float(vec[0]), float(vec[1]), float(vec[2])]
        except Exception:
            pass
    return [0.0, 0.0, 0.0]


def update_sim_info():
    """Call sim_info.update() to refresh shared memory."""
    si = _get_sim_info()
    if si is None:
        state.sim_info_ok = False
        return
    try:
        si.update()
        state.sim_info_ok = si.connected
    except Exception:
        state.sim_info_ok = False


def read_telemetry():
    """
    Populate state with latest telemetry values.
    On failure, retain previous values (fail-safe).
    """
    si = _get_sim_info()
    if si is None or not si.connected:
        state.sim_info_ok = False
        return

    try:
        ph = si.physics
        gr = si.graphics

        state.observed_speed_kmh = _safe_float(ph, "speedKmh")
        state.observed_speed_ms = state.observed_speed_kmh / 3.6
        state.observed_rpm = _safe_int(ph, "rpms")
        state.raw_gear = _safe_int(ph, "gear")
        state.observed_throttle = _safe_float(ph, "gas", "throttle")
        state.observed_brake = _safe_float(ph, "brake")
        state.observed_clutch = _safe_float(ph, "clutch")
        state.observed_fuel = _safe_float(ph, "fuel")
        state.raw_pitch = _safe_float(ph, "pitch")
        state.raw_velocity = _safe_vec3(ph, "velocity", "localVelocity")

        state.observed_lap_count = _safe_int(gr, "completedLaps")
        state.observed_norm_pos = _safe_float(gr, "normalizedCarPosition")
        state.raw_distance_traveled = _safe_float(gr, "distanceTraveled")
        state.raw_car_coordinates = _safe_vec3(gr, "carCoordinates")
        state.is_in_pit = _safe_bool(gr, "isInPit")
        state.is_in_pit_lane = _safe_bool(gr, "isInPitLane")

        # Backwards-compatible aliases
        state.speed_kmh = state.observed_speed_kmh
        state.speed_ms = state.observed_speed_ms
        state.rpm = state.observed_rpm
        state.gear = state.raw_gear
        state.throttle = state.observed_throttle
        state.brake = state.observed_brake
        state.clutch = state.observed_clutch
        state.fuel = state.observed_fuel
        state.pitch = state.raw_pitch
        state.velocity = list(state.raw_velocity)
        state.lap_count = state.observed_lap_count
        state.norm_pos = state.observed_norm_pos
        state.dist_traveled = state.raw_distance_traveled
        state.car_coords = list(state.raw_car_coordinates)

        state.sim_info_ok = True

    except Exception:
        state.sim_info_ok = False
