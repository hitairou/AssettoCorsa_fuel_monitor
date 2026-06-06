# ecoran_fuel_monitor.py
# Assetto Corsa Python app entry point.

import math
import os
import sys
import traceback

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

try:
    import ac
    import acsys
    _AC_AVAILABLE = True
except ImportError:
    _AC_AVAILABLE = False

    class _AcStub(object):
        def __getattr__(self, name):
            def _noop(*args, **kwargs):
                return 0
            return _noop

    ac = _AcStub()

from modules.app_state import state
from modules.bsfc_interp import (
    build_bsfc_interpolator,
    build_tmax_lookup,
    low_load_correction,
)
from modules.data_loader import load_strategy_config, load_vehicle_config
from modules.display_format import apply_gear_display_offset
from modules.fuel_integrator import calc_km_per_l, compute_fuel_flow, euler_step
from modules.forces import calc_forces
from modules.grade_estimator import init_estimator
from modules.lap_tracker import init_tracker
from modules.rpm_load import calc_load
from modules.smoothing import BoundedDerivative, MovingAverage
from modules.strategy_metrics import build_8lap_estimate, pace_delta
from modules.telemetry_reader import read_telemetry, update_sim_info
from modules.ui_presets import apply_preset
from modules.window_manager import create_windows, shutdown_windows, update_windows
from modules import bsfc_renderer


_bsfc_interp = None
_tmax_lookup = None
_speed_ma = None
_accel_deriv = None
_grade_est = None
_lap_tracker = None

_elapsed_time_s = 0.0
_last_update_error = None

_LOG_DIR = os.environ.get("TEMP", _APP_DIR)
_LOG_FILE = os.path.join(_LOG_DIR, "ecoran_fuel_monitor_debug.txt")
_debug_mode = False


def _log(msg, force=False):
    if _debug_mode or force:
        try:
            log_dir = os.path.dirname(_LOG_FILE)
            if log_dir and not os.path.isdir(log_dir):
                os.makedirs(log_dir)
            with open(_LOG_FILE, "a") as handle:
                handle.write(msg + "\n")
        except Exception:
            pass


def _log_exception(context, exc):
    lines = ["{0}: {1}".format(context, exc)]
    try:
        lines.append(traceback.format_exc())
    except Exception:
        pass
    _log("\n".join(lines), force=True)
    try:
        ac.log("[ECORAN] {0}: {1}".format(context, exc))
    except Exception:
        pass


def _cfg_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    try:
        return bool(int(value))
    except Exception:
        s = str(value).strip().lower()
        if s in ("true", "yes", "on"):
            return True
        if s in ("false", "no", "off"):
            return False
    return default


def _detect_engine(rpm, display_gear, strategy):
    on_thr = int(strategy.get("rpm_on_threshold", 800))
    off_thr = int(strategy.get("rpm_off_threshold", 500))

    if state.engine_on:
        return rpm >= off_thr
    return (rpm > on_thr) and (display_gear > 0)


def _reset_lap_accumulators():
    state.current_lap_E_engine_j = 0.0
    state.current_lap_E_roll_j = 0.0
    state.current_lap_E_aero_j = 0.0
    state.current_lap_E_accel_j = 0.0
    state.current_lap_E_grade_j = 0.0
    state.current_lap_restart_count = 0
    state.current_lap_engine_on_time = 0.0
    state.current_lap_time_s = 0.0


def _start_measurement_session(abs_dist_m, at_sf):
    ignore_initial_partial = _cfg_bool(
        state.strategy.get("ignore_initial_partial_lap", 1), True
    )

    state.measurement_active = True
    state.measurement_armed = False
    state.measurement_started_at_sf = bool(at_sf)
    state.measurement_start_session_time_s = _elapsed_time_s
    state.measurement_start_abs_dist_m = float(abs_dist_m)
    state.measurement_fuel_start_ml = float(state.cumul_fuel_ml)
    state.measurement_elapsed_time_s = 0.0
    state.measurement_engine_on_time_s = 0.0
    state.measurement_dist_m = 0.0
    state.measurement_fuel_used_ml = 0.0
    state.avg_fuel_econ_km_per_l = None
    state.avg_speed_kmh = None
    state.time_remaining_s = None
    state.pace_delta_s = None
    state.lap_rows = []
    state.laps_completed = 0
    state.lap_fuel_history = []
    state.current_lap_fuel_ml = 0.0
    state.current_lap_dist_m = 0.0
    state.current_lap_progress = 0.0
    state.est_8lap_source = "measurement_started"
    _reset_lap_accumulators()

    _lap_tracker.start_measurement(
        abs_dist_m,
        state.cumul_fuel_ml,
        at_sf=at_sf,
        ignore_initial_partial=ignore_initial_partial,
    )


def _update_measurement_state(lap_event, vehicle):
    mode = str(state.strategy.get("measurement_start_mode", "first_cross_sf")).strip()
    if mode not in ("session_start", "first_cross_sf", "manual_arm_then_cross_sf"):
        mode = "first_cross_sf"
    state.measurement_start_mode = mode

    if not state.measurement_active:
        if mode == "session_start":
            _start_measurement_session(state.session_dist_m, at_sf=False)
        elif lap_event["sf_crossed"]:
            if mode == "first_cross_sf":
                _start_measurement_session(lap_event["cross_abs_dist_m"], at_sf=True)
            elif mode == "manual_arm_then_cross_sf" and state.measurement_armed:
                _start_measurement_session(lap_event["cross_abs_dist_m"], at_sf=True)

    if state.measurement_active and lap_event["sf_crossed"]:
        if lap_event["measurement_lap_completed"]:
            _save_lap_row(vehicle, lap_event["completed_lap_fuel_ml"])
        _reset_lap_accumulators()

    if not state.measurement_active:
        state.measurement_elapsed_time_s = 0.0
        state.measurement_dist_m = 0.0
        state.measurement_fuel_used_ml = 0.0
        state.current_lap_fuel_ml = 0.0
        state.current_lap_dist_m = 0.0
        state.current_lap_progress = 0.0
        state.laps_completed = 0
        state.lap_fuel_history = []
        state.avg_fuel_econ_km_per_l = None
        state.avg_speed_kmh = None
        state.time_remaining_s = None
        state.pace_delta_s = None
        state.est_8lap_fuel_ml_completed_only = None
        state.est_8lap_fuel_ml_dynamic = None
        state.est_8lap_fuel_ml_display = None
        state.est_8lap_econ_km_per_l_completed_only = None
        state.est_8lap_econ_km_per_l_dynamic = None
        state.est_8lap_econ_km_per_l_display = None
        if mode == "manual_arm_then_cross_sf" and not state.measurement_armed:
            state.est_8lap_source = "waiting_for_arm"
        else:
            state.est_8lap_source = "waiting_for_first_cross"
        state.est_8lap_fuel_ml = 0.0
        state.est_8lap_econ_km_per_l = 0.0
        return

    state.measurement_elapsed_time_s = max(
        _elapsed_time_s - state.measurement_start_session_time_s, 0.0
    )
    state.measurement_dist_m = _lap_tracker.measurement_dist_m
    state.measurement_fuel_used_ml = max(
        state.cumul_fuel_ml - state.measurement_fuel_start_ml, 0.0
    )
    state.current_lap_fuel_ml = _lap_tracker.current_lap_fuel_ml
    state.current_lap_dist_m = _lap_tracker.current_lap_dist_m
    state.current_lap_progress = _lap_tracker.current_lap_progress
    state.current_lap_is_provisional = True
    state.laps_completed = _lap_tracker.laps_completed
    state.lap_fuel_history = list(_lap_tracker.lap_fuel_history)

    if state.measurement_fuel_used_ml > 0.0 and state.measurement_dist_m > 0.0:
        state.avg_fuel_econ_km_per_l = calc_km_per_l(
            state.measurement_dist_m, state.measurement_fuel_used_ml
        )
        state.estimated_km_per_l = state.avg_fuel_econ_km_per_l
    else:
        state.avg_fuel_econ_km_per_l = None

    if state.measurement_elapsed_time_s > 1.0:
        state.avg_speed_kmh = (
            (state.measurement_dist_m / 1000.0)
            / (state.measurement_elapsed_time_s / 3600.0)
        )
    else:
        state.avg_speed_kmh = None

    rule_time_limit_s = float(vehicle.get("rule_time_limit_s", 2536.70))
    rule_total_distance_m = float(vehicle.get("rule_total_distance_m", 17616.0))
    total_laps = int(vehicle.get("total_laps", 8))
    lap_distance_m = float(vehicle.get("lap_distance_m", 2202.0))

    state.time_remaining_s = max(rule_time_limit_s - state.measurement_elapsed_time_s, 0.0)

    if state.is_in_pit or state.is_in_pit_lane:
        state.pace_delta_s = None
    else:
        state.pace_delta_s = pace_delta(
            state.measurement_dist_m,
            state.measurement_elapsed_time_s,
            rule_time_limit_s,
            rule_total_distance_m,
        )

    estimate = build_8lap_estimate(
        state.lap_fuel_history,
        lap_distance_m,
        total_laps,
        state.current_lap_fuel_ml,
        state.current_lap_progress,
        state.current_lap_time_s,
        use_dynamic=_cfg_bool(state.strategy.get("use_dynamic_8lap_estimate", 1), True),
        min_progress=float(state.strategy.get("min_progress_for_dynamic_estimate", 0.10)),
        min_time_s=float(state.strategy.get("min_time_for_dynamic_estimate", 10.0)),
    )

    state.est_8lap_fuel_ml_completed_only = estimate["completed_fuel_ml"]
    state.est_8lap_fuel_ml_dynamic = estimate["dynamic_fuel_ml"]
    state.est_8lap_fuel_ml_display = estimate["display_fuel_ml"]
    state.est_8lap_econ_km_per_l_completed_only = estimate["completed_econ_km_per_l"]
    state.est_8lap_econ_km_per_l_dynamic = estimate["dynamic_econ_km_per_l"]
    state.est_8lap_econ_km_per_l_display = estimate["display_econ_km_per_l"]
    state.est_8lap_source = estimate["source"]
    state.est_8lap_fuel_ml = (
        state.est_8lap_fuel_ml_display
        if state.est_8lap_fuel_ml_display is not None else 0.0
    )
    state.est_8lap_econ_km_per_l = (
        state.est_8lap_econ_km_per_l_display
        if state.est_8lap_econ_km_per_l_display is not None else 0.0
    )


def acMain(ac_version):
    global _bsfc_interp, _tmax_lookup, _speed_ma, _accel_deriv, _grade_est, _lap_tracker
    global _debug_mode

    stage = "start"
    try:
        stage = "load configs"
        vehicle = load_vehicle_config()
        strategy = load_strategy_config()
        state.vehicle = vehicle
        state.strategy = strategy

        _debug_mode = _cfg_bool(strategy.get("debug_mode", 0), False)

        state.measurement_start_mode = str(
            strategy.get("measurement_start_mode", "first_cross_sf")
        ).strip()
        state.measurement_armed = state.measurement_start_mode != "manual_arm_then_cross_sf"

        log_dir = os.path.join(_APP_DIR, "logs")
        if not os.path.isdir(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception:
                pass

        _log("acMain called. AC version: {0}".format(ac_version), force=True)

        initial_preset = str(strategy.get("ui.preset", "overview"))
        apply_preset(state, initial_preset)

        stage = "create ui"
        create_windows(state)

        stage = "build interpolators"
        _bsfc_interp = build_bsfc_interpolator()
        _tmax_lookup = build_tmax_lookup()

        stage = "init bsfc renderer"
        try:
            bsfc_renderer.init(_bsfc_interp)
        except Exception as exc:
            _log("bsfc_renderer.init failed: {0}".format(exc), force=True)

        try:
            bsfc_window = state.ui_windows.get("bsfc")
            if bsfc_window is not None:
                from modules import panel_bsfc as _panel_bsfc
                _panel_bsfc.prime_cell_labels(bsfc_window["labels"])
        except Exception as exc:
            _log("panel_bsfc.prime_cell_labels failed: {0}".format(exc), force=True)

        stage = "create smoothing"
        _speed_ma = MovingAverage(window=int(strategy.get("speed_window", 5)))
        _accel_deriv = BoundedDerivative(max_abs=20.0)

        stage = "init grade estimator"
        init_estimator(strategy)
        import modules.grade_estimator as _ge_mod
        _grade_est = _ge_mod.estimator

        stage = "init lap tracker"
        init_tracker(vehicle, strategy)
        import modules.lap_tracker as _lt_mod
        _lap_tracker = _lt_mod.tracker

        stage = "connect shared memory"
        update_sim_info()
        _log("sim_info connected: {0}".format(state.sim_info_ok), force=True)

        return "ecoran_fuel_monitor"
    except Exception as exc:
        _log_exception("acMain failed at {0}".format(stage), exc)
        return "ecoran_fuel_monitor"


def acUpdate(delta_t):
    global _elapsed_time_s, _last_update_error

    stage = "start"
    try:
        if not state.ui_windows:
            return

        dt = float(delta_t)
        _elapsed_time_s += dt

        stage = "telemetry"
        update_sim_info()
        read_telemetry()
        if not state.sim_info_ok:
            return

        stage = "main update"
        state.accum_t += dt
        update_interval = float(state.strategy.get("update_interval_s", 0.1))
        if state.accum_t >= update_interval:
            _main_update(state.accum_t)
            state.accum_t = 0.0

        stage = "ui refresh"
        update_windows(state)
        _last_update_error = None
    except Exception as exc:
        err_sig = "{0}: {1}".format(type(exc).__name__, exc)
        if err_sig != _last_update_error:
            _last_update_error = err_sig
            _log_exception("acUpdate failed at {0}".format(stage), exc)


def _main_update(dt):
    strategy = state.strategy
    vehicle = state.vehicle

    gear_display_offset = int(strategy.get("gear_display_offset", -1))
    state.display_gear = apply_gear_display_offset(state.raw_gear, gear_display_offset)
    if state.display_gear is None:
        state.display_gear = 0

    v_ms = state.observed_speed_ms
    v_smooth = _speed_ma.update(v_ms)
    accel = _accel_deriv.update(_elapsed_time_s, v_smooth)
    state.accel_ms2 = accel

    grade_smooth, grade_src = _grade_est.update(
        state.raw_distance_traveled,
        state.raw_car_coordinates,
        state.raw_pitch,
        state.session_dist_m,
    )
    state.grade_smooth = grade_smooth
    state.grade_source = grade_src
    state.theta_rad = math.atan(grade_smooth)

    was_on = state.engine_on
    state.observed_engine_on = _detect_engine(
        state.observed_rpm, state.display_gear, strategy
    )
    state.engine_on = state.observed_engine_on
    state.prev_engine_on = was_on

    just_started = (not was_on) and state.engine_on
    if just_started:
        state.session_restart_count += 1
        if state.measurement_active:
            state.current_lap_restart_count += 1

    (F_req, P_wheel, theta,
     P_roll, P_aero, P_accel_t, P_grade_t) = calc_forces(
        v_ms, accel, grade_smooth, vehicle
    )

    state.demand_force_n = F_req
    state.demand_wheel_power_w = P_wheel
    state.theta_rad = theta
    state.demand_roll_power_w = P_roll
    state.demand_aero_power_w = P_aero
    state.demand_accel_power_w = P_accel_t
    state.demand_grade_power_w = P_grade_t

    eta_d = float(vehicle.get("drivetrain_efficiency", 0.9))
    demand_engine_power_w = max(P_wheel / max(eta_d, 1e-9), 0.0)
    state.demand_engine_power_w = demand_engine_power_w

    net_energy_rate_w = demand_engine_power_w - P_roll - P_aero - P_accel_t - P_grade_t
    state.net_energy_balance_j += net_energy_rate_w * dt

    state.hist_engine.append(demand_engine_power_w)
    state.hist_roll.append(P_roll)
    state.hist_aero.append(P_aero)
    state.hist_accel.append(P_accel_t)
    state.hist_grade.append(P_grade_t)

    if _cfg_bool(strategy.get("power_graph_auto_scale", 1), True):
        power_samples = []
        for attr in ("hist_engine", "hist_roll", "hist_aero", "hist_accel", "hist_grade"):
            power_samples.extend([abs(float(v)) for v in getattr(state, attr).to_list()])
        peak_power = max(power_samples) if power_samples else 0.0
        state.power_graph_scale_w = max(2000.0, peak_power * 1.15, 500.0)
    else:
        state.power_graph_scale_w = float(strategy.get("power_graph_scale_w", 2000.0))
    state.net_energy_balance_scale_j = max(5000.0, abs(state.net_energy_balance_j) * 1.15)

    engaged_display_gear = state.display_gear if state.display_gear > 0 else 0
    i_total, T_req, demand_load = calc_load(
        max(F_req, 0.0),
        state.observed_rpm,
        vehicle,
        engaged_display_gear,
        lambda rpm: _tmax_lookup.query(rpm),
    )
    state.demand_required_torque_nm = T_req
    state.demand_load_ratio = demand_load

    demand_bsfc = low_load_correction(
        _bsfc_interp.query(state.observed_rpm, demand_load),
        demand_load,
    )
    state.demand_bsfc_g_per_kwh = demand_bsfc

    fuel_density = float(vehicle.get("fuel_density_g_per_ml", 0.778))
    mf_dot, vf_dot = compute_fuel_flow(
        demand_bsfc, demand_engine_power_w, fuel_density
    )
    state.demand_fuel_mass_flow_g_s = mf_dot
    state.demand_fuel_flow_ml_s = vf_dot

    engine_point_valid = state.engine_on and state.display_gear > 0 and state.observed_rpm >= 100
    if engine_point_valid:
        state.current_bsfc_display_g_per_kwh = demand_bsfc
        state.current_load_display_ratio = demand_load
        state.current_fuel_flow_display_ml_s = vf_dot
    else:
        state.current_bsfc_display_g_per_kwh = None
        state.current_load_display_ratio = None
        state.current_fuel_flow_display_ml_s = 0.0

    if engine_point_valid:
        state.bsfc_trace_rpm.append(float(state.observed_rpm))
        state.bsfc_trace_load.append(float(demand_load))
    else:
        state.bsfc_trace_rpm.append(float("nan"))
        state.bsfc_trace_load.append(float("nan"))

    if state.engine_on:
        state.cumul_fuel_ml = euler_step(state.cumul_fuel_ml, vf_dot, dt)

    if just_started:
        penalty = float(strategy.get("start_penalty_ml", 0.5))
        state.cumul_fuel_ml += penalty
        _log("Engine restart penalty: {0} mL".format(penalty))

    state.session_elapsed_time = _elapsed_time_s
    if state.engine_on:
        state.session_engine_on_time += dt
        if state.measurement_active:
            state.measurement_engine_on_time_s += dt

    if state.measurement_active:
        state.current_lap_time_s += dt
        state.current_lap_E_engine_j += demand_engine_power_w * dt
        state.current_lap_E_roll_j += P_roll * dt
        state.current_lap_E_aero_j += P_aero * dt
        state.current_lap_E_accel_j += P_accel_t * dt
        state.current_lap_E_grade_j += P_grade_t * dt
        if state.engine_on:
            state.current_lap_engine_on_time += dt

    lap_event = _lap_tracker.update(
        state.observed_norm_pos, state.observed_lap_count, state.cumul_fuel_ml
    )
    state.session_dist_m = _lap_tracker.session_dist_m

    _update_measurement_state(lap_event, vehicle)
    if not state.measurement_active:
        state.current_lap_is_provisional = False

    state.F_req = state.demand_force_n
    state.P_wheel = state.demand_wheel_power_w
    state.P_engine = state.demand_engine_power_w
    state.T_req = state.demand_required_torque_nm
    state.load = state.demand_load_ratio
    state.bsfc = state.demand_bsfc_g_per_kwh
    state.mf_dot = state.demand_fuel_mass_flow_g_s
    state.vf_dot = state.demand_fuel_flow_ml_s
    state.current_P_roll = state.demand_roll_power_w
    state.current_P_aero = state.demand_aero_power_w
    state.current_P_accel_term = state.demand_accel_power_w
    state.current_P_grade_term = state.demand_grade_power_w
    state.current_P_engine = state.demand_engine_power_w
    state.current_E_store = state.net_energy_balance_j

    state.first_update = False

    _log(
        "dt={0:.3f} rawGear={1} dispGear={2} engineOn={3} "
        "dLoad={4:.3f} curBsfc={5} estSource={6} measActive={7}".format(
            dt,
            state.raw_gear,
            state.display_gear,
            int(state.engine_on),
            state.demand_load_ratio,
            state.current_bsfc_display_g_per_kwh,
            state.est_8lap_source,
            int(state.measurement_active),
        )
    )


def _save_lap_row(vehicle, fuel_used_ml=None):
    try:
        if not state.measurement_active:
            return

        lap_time = max(state.current_lap_time_s, 1e-9)
        lap_distance_m = float(vehicle.get("lap_distance_m", 2202.0))
        fuel_used_ml = (
            float(fuel_used_ml)
            if fuel_used_ml is not None else float(state.current_lap_fuel_ml)
        )
        fuel_econ = (lap_distance_m / fuel_used_ml) if fuel_used_ml > 0.01 else 0.0
        avg_speed = (lap_distance_m / lap_time) * 3.6
        on_ratio = state.current_lap_engine_on_time / lap_time * 100.0

        row = {
            "lap_number": state.laps_completed + 1,
            "fuel_econ_km_per_l": fuel_econ,
            "fuel_used_ml": fuel_used_ml,
            "avg_speed_kmh": avg_speed,
            "energy_engine_j": state.current_lap_E_engine_j,
            "energy_roll_j": state.current_lap_E_roll_j,
            "energy_aero_j": state.current_lap_E_aero_j,
            "energy_accel_j": state.current_lap_E_accel_j,
            "energy_grade_j": state.current_lap_E_grade_j,
            "restart_count": state.current_lap_restart_count,
            "engine_on_ratio_pct": on_ratio,
        }
        state.lap_rows.append(row)
    except Exception as exc:
        _log("_save_lap_row error: {0}".format(exc), force=True)


def acShutdown():
    try:
        _log("acShutdown called.", force=True)
        shutdown_windows(state)
        try:
            import sim_info as _si
            _si.info.close()
        except Exception:
            pass
    except Exception as exc:
        _log_exception("acShutdown failed", exc)
