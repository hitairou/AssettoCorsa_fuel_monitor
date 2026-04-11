# modules/forces.py
# Calculates required drive force, wheel power, and individual power components.

import math

_EPSILON = 1e-9


def calc_forces(v_ms, accel_ms2, grade_smooth, vehicle):
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
    F_req        : required longitudinal force [N]  (signed)
    P_wheel      : wheel power [W]                  (>= 0, driving only)
    theta        : road inclination angle [rad]
    P_roll       : rolling resistance power [W]     (always >= 0)
    P_aero       : aerodynamic drag power [W]       (always >= 0)
    P_accel_term : inertia power term [W]           (signed; + = accelerating)
    P_grade_term : gravity grade power term [W]     (signed; + = uphill)
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

    return F_req, P_wheel, theta, P_roll, P_aero, P_accel_term, P_grade_term
