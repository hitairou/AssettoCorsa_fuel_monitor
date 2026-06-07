# modules/forces.py
# Calculates required drive force, wheel power, and individual power components.

import math

_EPSILON = 1e-9


def calc_force_components(v_ms, accel_ms2, grade_smooth, vehicle):
    """
    Compute required drive force, wheel power, and individual power components.

    Parameters
    ----------
    v_ms        : vehicle speed [m/s]
    accel_ms2   : longitudinal acceleration [m/s^2]
    grade_smooth: smoothed road grade (dh/ds, dimensionless)
    vehicle     : dict from vehicle.ini

    Returns
    -------
    dict with:
        theta        : road inclination angle [rad]
        F_roll       : rolling resistance force [N]
        F_aero       : aerodynamic drag force [N]
        F_grav       : gravity grade force [N]
        F_inertia    : inertia force [N]
        F_req        : required longitudinal force [N]  (signed)
        P_roll       : rolling resistance power [W]     (always >= 0)
        P_aero       : aerodynamic drag power [W]       (always >= 0)
        P_accel_term : inertia power term [W]           (signed; + = accelerating)
        P_grade_term : gravity grade power term [W]     (signed; + = uphill)
        P_wheel      : wheel power [W]                  (>= 0, driving only)
    """
    m   = float(vehicle.get("mass_total",   98.65))
    crr = float(vehicle.get("crr",          0.0025))
    cd  = float(vehicle.get("cd",           0.355))
    A   = float(vehicle.get("frontal_area", 0.3846))
    rho = float(vehicle.get("rho_air",      1.225))
    g   = float(vehicle.get("gravity",      9.81))

    theta = math.atan(grade_smooth)

    F_roll    = crr * m * g * math.cos(theta)
    F_aero    = 0.5 * rho * cd * A * v_ms * v_ms
    F_grav    = m * g * math.sin(theta)
    F_inertia = m * accel_ms2

    F_req = F_roll + F_aero + F_grav + F_inertia

    # Only positive force contributes to fuel consumption
    F_drive = max(F_req, 0.0)
    P_wheel = F_drive * v_ms

    # Individual power components
    P_roll       = F_roll    * v_ms   # always >= 0
    P_aero       = F_aero    * v_ms   # always >= 0
    P_accel_term = F_inertia * v_ms   # signed
    P_grade_term = F_grav    * v_ms   # signed

    return {
        "theta": theta,
        "F_roll": F_roll,
        "F_aero": F_aero,
        "F_grav": F_grav,
        "F_inertia": F_inertia,
        "F_req": F_req,
        "P_roll": P_roll,
        "P_aero": P_aero,
        "P_accel_term": P_accel_term,
        "P_grade_term": P_grade_term,
        "P_wheel": P_wheel,
    }


def calc_forces(v_ms, accel_ms2, grade_smooth, vehicle):
    data = calc_force_components(v_ms, accel_ms2, grade_smooth, vehicle)
    return (
        data["F_req"],
        data["P_wheel"],
        data["theta"],
        data["P_roll"],
        data["P_aero"],
        data["P_accel_term"],
        data["P_grade_term"],
    )
