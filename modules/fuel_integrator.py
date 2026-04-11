# modules/fuel_integrator.py
# Euler integration of fuel consumption.

_EPSILON = 1e-9
_DEFAULT_FUEL_DENSITY = 0.778


def compute_fuel_flow(bsfc_g_kwh, P_engine_w, fuel_density_g_per_ml=None):
    """
    Compute fuel mass flow and volume flow.

    Parameters
    ----------
    bsfc_g_kwh : BSFC [g/kWh]
    P_engine_w : engine shaft power [W]

    Returns
    -------
    mf_dot_gs  : fuel mass flow [g/s]
    vf_dot_mls : fuel volume flow [mL/s]
    """
    P_kw = max(P_engine_w, 0.0) / 1000.0   # W -> kW
    mf_dot = bsfc_g_kwh * P_kw / 3600.0    # g/kWh * kW / 3600 = g/s
    density = fuel_density_g_per_ml
    try:
        density = float(density)
    except (TypeError, ValueError):
        density = _DEFAULT_FUEL_DENSITY
    if density <= _EPSILON:
        density = _DEFAULT_FUEL_DENSITY
    vf_dot = mf_dot / density               # g/s / (g/mL) = mL/s
    return mf_dot, vf_dot


def euler_step(fuel_ml, vf_dot_mls, dt):
    """Single Euler integration step. Returns updated fuel_ml."""
    return fuel_ml + vf_dot_mls * dt


def calc_km_per_l(dist_m, fuel_ml):
    """
    Compute fuel economy.

    Returns km/L or 0.0 if fuel_ml is negligible.
    """
    if fuel_ml < _EPSILON:
        return 0.0
    dist_km = dist_m / 1000.0
    fuel_l  = fuel_ml / 1000.0
    return dist_km / max(fuel_l, _EPSILON)
