# modules/app_state.py
# Global mutable state container for ecoran_fuel_monitor.

_HIST_LEN = 200   # 20 s at 10 Hz


class AppState(object):
    def __init__(self):
        from modules.history_buffers import RingBuffer

        # ------------------------------------------------------------------
        # Observed / actual telemetry from shared memory
        # ------------------------------------------------------------------
        self.observed_speed_kmh = 0.0
        self.observed_speed_ms = 0.0
        self.observed_rpm = 0
        self.raw_gear = 0
        self.display_gear = 0
        self.observed_throttle = 0.0
        self.observed_brake = 0.0
        self.observed_clutch = 0.0
        self.observed_fuel = 0.0
        self.observed_lap_count = 0
        self.observed_norm_pos = 0.0
        self.raw_distance_traveled = 0.0
        self.raw_car_coordinates = [0.0, 0.0, 0.0]
        self.raw_velocity = [0.0, 0.0, 0.0]
        self.raw_pitch = 0.0
        self.raw_heading = 0.0
        self.is_in_pit = False
        self.is_in_pit_lane = False

        # Backwards-compatible aliases
        self.speed_kmh = 0.0
        self.speed_ms = 0.0
        self.rpm = 0
        self.gear = 0
        self.throttle = 0.0
        self.brake = 0.0
        self.clutch = 0.0
        self.fuel = 0.0
        self.lap_count = 0
        self.norm_pos = 0.0
        self.dist_traveled = 0.0
        self.car_coords = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        self.pitch = 0.0
        self.heading = 0.0

        # ------------------------------------------------------------------
        # Derived / inferred values
        # ------------------------------------------------------------------
        self.accel_ms2 = 0.0
        self.grade_raw = 0.0
        self.grade_smooth = 0.0
        self.theta_rad = 0.0
        self.grade_source = "init"

        self.demand_force_n = 0.0
        self.demand_wheel_power_w = 0.0
        self.demand_engine_power_w = 0.0
        self.demand_required_torque_nm = 0.0
        self.demand_load_ratio = 0.0
        self.demand_bsfc_g_per_kwh = 400.0
        self.demand_fuel_mass_flow_g_s = 0.0
        self.demand_fuel_flow_ml_s = 0.0

        self.current_bsfc_display_g_per_kwh = None
        self.current_load_display_ratio = None
        self.current_fuel_flow_display_ml_s = 0.0

        self.demand_roll_power_w = 0.0
        self.demand_aero_power_w = 0.0
        self.demand_accel_power_w = 0.0
        self.demand_grade_power_w = 0.0

        self.net_energy_balance_j = 0.0

        # Backwards-compatible aliases used by renderers
        self.F_req = 0.0
        self.P_wheel = 0.0
        self.P_engine = 0.0
        self.T_req = 0.0
        self.load = 0.0
        self.bsfc = 400.0
        self.mf_dot = 0.0
        self.vf_dot = 0.0
        self.current_P_roll = 0.0
        self.current_P_aero = 0.0
        self.current_P_accel_term = 0.0
        self.current_P_grade_term = 0.0
        self.current_P_engine = 0.0
        self.current_E_store = 0.0

        # ------------------------------------------------------------------
        # Histories
        # ------------------------------------------------------------------
        self.hist_engine = RingBuffer(_HIST_LEN)
        self.hist_roll = RingBuffer(_HIST_LEN)
        self.hist_aero = RingBuffer(_HIST_LEN)
        self.hist_accel = RingBuffer(_HIST_LEN)
        self.hist_grade = RingBuffer(_HIST_LEN)
        self.hist_residual_balance_j = RingBuffer(_HIST_LEN)

        self.bsfc_trace_rpm = RingBuffer(_HIST_LEN)
        self.bsfc_trace_load = RingBuffer(_HIST_LEN)

        self.power_graph_scale_w = 800.0
        self.net_energy_balance_scale_j = 5000.0

        # ------------------------------------------------------------------
        # Aggregate / cumulative session values
        # ------------------------------------------------------------------
        self.session_elapsed_time = 0.0
        self.session_restart_count = 0
        self.session_engine_on_time = 0.0
        self.session_dist_m = 0.0

        self.measurement_start_mode = "first_cross_sf"
        self.measurement_active = False
        self.measurement_finished = False
        self.measurement_armed = False
        self.measurement_elapsed_time_s = 0.0
        self.measurement_engine_on_time_s = 0.0
        self.measurement_dist_m = 0.0
        self.measurement_fuel_start_ml = 0.0
        self.measurement_fuel_used_ml = 0.0
        self.measurement_start_session_time_s = 0.0
        self.measurement_start_abs_dist_m = 0.0
        self.measurement_started_at_sf = False
        self.measurement_started_by_gate = False
        self.measurement_start_sim_time = 0.0
        self.measurement_stop_sim_time = 0.0

        self.avg_fuel_econ_km_per_l = None
        self.avg_speed_kmh = None
        self.time_remaining_s = None
        self.pace_delta_s = None
        self.cumul_fuel_ml = 0.0

        self.estimated_km_per_l = 0.0

        # ------------------------------------------------------------------
        # Estimate / projection values
        # ------------------------------------------------------------------
        self.est_8lap_fuel_ml_completed_only = None
        self.est_8lap_fuel_ml_dynamic = None
        self.est_8lap_fuel_ml_display = None
        self.est_8lap_econ_km_per_l_completed_only = None
        self.est_8lap_econ_km_per_l_dynamic = None
        self.est_8lap_econ_km_per_l_display = None
        self.est_8lap_source = "inactive"

        # Backwards-compatible aliases
        self.est_8lap_fuel_ml = 0.0
        self.est_8lap_econ_km_per_l = 0.0

        # ------------------------------------------------------------------
        # Engine state
        # ------------------------------------------------------------------
        self.observed_engine_on = False
        self.engine_on = False
        self.prev_engine_on = False

        # ------------------------------------------------------------------
        # Measurement lap tracking
        # ------------------------------------------------------------------
        self.laps_completed = 0
        self.lap_fuel_history = []
        self.current_lap_fuel_ml = 0.0
        self.current_lap_dist_m = 0.0
        self.current_lap_progress = 0.0
        self.current_lap_is_provisional = False

        self.lap_rows = []
        self.current_lap_E_engine_j = 0.0
        self.current_lap_E_roll_j = 0.0
        self.current_lap_E_aero_j = 0.0
        self.current_lap_E_accel_j = 0.0
        self.current_lap_E_grade_j = 0.0
        self.current_lap_restart_count = 0
        self.current_lap_engine_on_time = 0.0
        self.current_lap_time_s = 0.0
        self.gate_based_lap_count = 0

        # ------------------------------------------------------------------
        # Previous samples for derivatives
        # ------------------------------------------------------------------
        self.prev_dist_traveled = 0.0
        self.prev_coords = [0.0, 0.0, 0.0]
        self.prev_height = 0.0
        self.prev_speed_ms = 0.0
        self.prev_session_dist_m = 0.0
        self.prev_gate_position = None

        # ------------------------------------------------------------------
        # Update accumulator
        # ------------------------------------------------------------------
        self.accum_t = 0.0
        self.first_update = True

        # ------------------------------------------------------------------
        # UI state
        # ------------------------------------------------------------------
        self.labels = {}
        self.ui_windows = {}
        self.ui_window_positions = {}
        self.ui_window_sizes = {}
        self.ui_last_layout_save_s = 0.0
        self.ui_visibility_dirty = False

        self.ui_preset = "overview"
        self.ui_show_main_window = True
        self.ui_show_power_window = False
        self.ui_show_lap_window = False
        self.ui_show_bsfc_window = False
        self.ui_show_debug_window = False

        # ------------------------------------------------------------------
        # Loaded config references
        # ------------------------------------------------------------------
        self.vehicle = {}
        self.strategy = {}

        # ------------------------------------------------------------------
        # Shared memory availability
        # ------------------------------------------------------------------
        self.sim_info_ok = False

        # ------------------------------------------------------------------
        # Track / gate control
        # ------------------------------------------------------------------
        self.track_name = ""
        self.track_layout = ""
        self.track_key = ""
        self.track_key_loaded = ""
        self.gates = {
            "start": None,
            "lap": None,
            "finish": None,
        }
        self.selected_gate_kind = "lap"
        self.record_mode = "manual"
        self.record_state = "idle"
        self.record_control_enabled = False
        self.pending_record_command = ""
        self.gate_last_trigger_time = {
            "start": -1e9,
            "lap": -1e9,
            "finish": -1e9,
        }
        self.gate_last_trigger_name = ""
        self.gate_last_trigger_sim_time = None
        self.gate_last_status = ""
        self.gate_info_visible = True
        self.gate_storage_path = ""
        self.gate_debug_last_s0_s1 = "---"
        self.gate_debug_last_u = None
        self.gate_debug_last_speed = None
        self.gate_debug_last_reason_rejected = ""
        self.last_forward_world = [1.0, 0.0, 0.0]
        self.bsfc_gear_candidates = []


state = AppState()
