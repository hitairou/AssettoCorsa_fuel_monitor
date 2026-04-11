# modules/strategy_metrics.py
# Demand/estimate helpers for race metrics.

_EPSILON = 1e-9


def predict_8lap_fuel_completed_only(lap_fuel_history, total_laps=8):
    if not lap_fuel_history:
        return None
    avg_lap_ml = sum(lap_fuel_history) / max(len(lap_fuel_history), 1)
    return avg_lap_ml * total_laps


def predict_8lap_econ_completed_only(lap_fuel_history, lap_distance_m, total_laps=8):
    total_fuel_ml = predict_8lap_fuel_completed_only(lap_fuel_history, total_laps)
    if total_fuel_ml is None or total_fuel_ml < _EPSILON:
        return None
    total_dist_m = float(lap_distance_m) * total_laps
    return total_dist_m / total_fuel_ml


def build_8lap_estimate(lap_fuel_history, lap_distance_m, total_laps,
                        current_lap_fuel_ml, current_lap_progress,
                        current_lap_time_s, use_dynamic=True,
                        min_progress=0.10, min_time_s=10.0):
    completed_fuel = predict_8lap_fuel_completed_only(lap_fuel_history, total_laps)
    completed_econ = predict_8lap_econ_completed_only(lap_fuel_history, lap_distance_m, total_laps)

    result = {
        "completed_fuel_ml": completed_fuel,
        "completed_econ_km_per_l": completed_econ,
        "dynamic_fuel_ml": completed_fuel,
        "dynamic_econ_km_per_l": completed_econ,
        "display_fuel_ml": completed_fuel,
        "display_econ_km_per_l": completed_econ,
        "source": "completed_only" if completed_fuel is not None else "no_data",
    }

    if not use_dynamic:
        return result

    if current_lap_progress < max(min_progress, _EPSILON) or current_lap_time_s < min_time_s:
        if completed_fuel is None:
            result["source"] = "insufficient_progress"
        return result

    projected_lap_fuel_ml = current_lap_fuel_ml / max(current_lap_progress, _EPSILON)
    if projected_lap_fuel_ml < _EPSILON:
        if completed_fuel is None:
            result["source"] = "insufficient_progress"
        return result

    if lap_fuel_history:
        avg_lap_ml = (
            sum(lap_fuel_history) + projected_lap_fuel_ml
        ) / float(len(lap_fuel_history) + 1)
        result["source"] = "completed_plus_provisional"
    else:
        avg_lap_ml = projected_lap_fuel_ml
        result["source"] = "provisional_only"

    result["dynamic_fuel_ml"] = avg_lap_ml * total_laps
    total_dist_m = float(lap_distance_m) * total_laps
    result["dynamic_econ_km_per_l"] = (
        total_dist_m / result["dynamic_fuel_ml"]
        if result["dynamic_fuel_ml"] > _EPSILON else None
    )
    result["display_fuel_ml"] = result["dynamic_fuel_ml"]
    result["display_econ_km_per_l"] = result["dynamic_econ_km_per_l"]
    return result


def pace_delta(measurement_dist_m, measurement_elapsed_time_s,
               rule_time_limit_s, rule_total_distance_m):
    if measurement_elapsed_time_s < _EPSILON:
        return None

    target_pace_ms = rule_total_distance_m / max(rule_time_limit_s, _EPSILON)
    target_dist_m = target_pace_ms * measurement_elapsed_time_s
    dist_delta_m = measurement_dist_m - target_dist_m
    return dist_delta_m / max(target_pace_ms, _EPSILON)


def estimate_remaining_fuel(lap_fuel_history, laps_completed, total_laps):
    remaining_laps = max(total_laps - laps_completed, 0)
    if not lap_fuel_history:
        return 0.0
    avg_lap_ml = sum(lap_fuel_history) / max(len(lap_fuel_history), 1)
    return avg_lap_ml * remaining_laps
