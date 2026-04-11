# modules/rpm_load.py
# Computes gear ratio, total reduction, required engine torque, and load ratio.

import math

_EPSILON = 1e-9
_TWO_PI  = 2.0 * math.pi


def gear_ratios_from_config(vehicle):
    """
    Returns a dict mapping gear number (int) -> gear ratio (float).
    Gear 0 = neutral/reverse (ratio 0 treated as invalid).
    """
    ratios = {0: 0.0}
    for g in range(1, 9):
        key = "gear_{0}".format(g)
        if key in vehicle:
            ratios[g] = float(vehicle[key])
    return ratios


def calc_load(F_req_positive, rpm, vehicle, gear, tmax_fn):
    """
    Compute normalized engine load.

    Parameters
    ----------
    F_req_positive : max(F_req, 0.0) [N]
    rpm            : engine speed [rpm]
    vehicle        : vehicle config dict
    gear           : current gear (int)
    tmax_fn        : callable(rpm) -> Tmax_Nm

    Returns
    -------
    i_total : total gear reduction ratio
    T_req   : required engine torque [Nm]
    load    : normalized load clamped to [0, 1]
    """
    primary   = float(vehicle.get("primary_ratio",   4.058))
    secondary = float(vehicle.get("secondary_ratio", 2.944))
    eta_d     = float(vehicle.get("drivetrain_efficiency", 0.9))
    circ      = float(vehicle.get("rear_tire_circumference_m", 1.5))

    ratios    = gear_ratios_from_config(vehicle)
    gear_r    = ratios.get(gear, 0.0)

    rear_radius = circ / _TWO_PI

    if gear_r < _EPSILON:
        # Neutral / unknown gear - no drive torque
        return 0.0, 0.0, 0.0

    i_total = primary * gear_r * secondary
    denom   = max(i_total * eta_d, _EPSILON)

    T_req = (F_req_positive * rear_radius) / denom

    Tmax  = tmax_fn(float(rpm))
    if Tmax < _EPSILON:
        load = 0.0
    else:
        load = T_req / Tmax
        if load > 1.0:
            load = 1.0
        elif load < 0.0:
            load = 0.0

    return i_total, T_req, load
