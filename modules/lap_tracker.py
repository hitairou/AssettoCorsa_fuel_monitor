# modules/lap_tracker.py
# Tracks raw session laps and measurement-session laps separately.


class LapTracker(object):
    def __init__(self, lap_distance_m=2202.0):
        self.lap_distance_m = float(lap_distance_m)
        self.reset()

    def reset(self):
        self._prev_norm_pos = 0.0
        self._prev_lap_count = 0
        self._raw_laps_seen = 0
        self._session_dist_m = 0.0
        self._last_cumul_fuel_ml = 0.0

        self.measurement_active = False
        self.measurement_start_abs_dist_m = 0.0
        self._measurement_lap_start_abs_dist_m = 0.0
        self._measurement_lap_start_fuel_ml = 0.0
        self._measurement_full_lap_started = False
        self.lap_fuel_history = []
        self.laps_completed = 0

    def start_measurement(self, abs_dist_m, cumul_fuel_ml,
                          at_sf=False, ignore_initial_partial=True,
                          count_first_lap=False):
        self.measurement_active = True
        self.measurement_start_abs_dist_m = float(abs_dist_m)
        self._measurement_lap_start_abs_dist_m = float(abs_dist_m)
        self._measurement_lap_start_fuel_ml = float(cumul_fuel_ml)
        self._measurement_full_lap_started = bool(
            at_sf or not ignore_initial_partial or count_first_lap
        )
        self.lap_fuel_history = []
        self.laps_completed = 0

    def stop_measurement(self):
        self.measurement_active = False
        self.measurement_start_abs_dist_m = self._session_dist_m
        self._measurement_lap_start_abs_dist_m = self._session_dist_m
        self._measurement_lap_start_fuel_ml = 0.0
        self._measurement_full_lap_started = False
        self.lap_fuel_history = []
        self.laps_completed = 0

    def update(self, norm_pos, lap_count, cumul_fuel_ml):
        self._last_cumul_fuel_ml = float(cumul_fuel_ml)
        event = {
            "sf_crossed": False,
            "cross_abs_dist_m": None,
            "measurement_lap_completed": False,
            "completed_lap_fuel_ml": None,
            "measurement_reference_reset": False,
            "session_dist_m": self._session_dist_m,
        }

        lap_count = int(lap_count)
        norm_pos = float(norm_pos)

        if lap_count > self._prev_lap_count:
            laps_done = lap_count - self._prev_lap_count
            for _idx in range(laps_done):
                self._raw_laps_seen += 1
                cross_abs_dist_m = self._raw_laps_seen * self.lap_distance_m
                self._on_sf_cross(cross_abs_dist_m, cumul_fuel_ml, event)
            self._prev_lap_count = lap_count

        elif self._prev_norm_pos > 0.9 and norm_pos < 0.1 and lap_count == self._prev_lap_count:
            self._raw_laps_seen += 1
            self._prev_lap_count = max(self._prev_lap_count, self._raw_laps_seen)
            cross_abs_dist_m = self._raw_laps_seen * self.lap_distance_m
            self._on_sf_cross(cross_abs_dist_m, cumul_fuel_ml, event)

        else:
            self._raw_laps_seen = max(self._raw_laps_seen, lap_count)

        self._session_dist_m = self._raw_laps_seen * self.lap_distance_m + norm_pos * self.lap_distance_m
        self._prev_norm_pos = norm_pos
        event["session_dist_m"] = self._session_dist_m
        return event

    def _on_sf_cross(self, cross_abs_dist_m, cumul_fuel_ml, event):
        event["sf_crossed"] = True
        event["cross_abs_dist_m"] = cross_abs_dist_m

        if not self.measurement_active:
            return

        if self._measurement_full_lap_started:
            lap_fuel = max(float(cumul_fuel_ml) - self._measurement_lap_start_fuel_ml, 0.0)
            self.lap_fuel_history.append(lap_fuel)
            self.laps_completed += 1
            event["measurement_lap_completed"] = True
            event["completed_lap_fuel_ml"] = lap_fuel
        else:
            self._measurement_full_lap_started = True
            event["measurement_reference_reset"] = True

        self._measurement_lap_start_fuel_ml = float(cumul_fuel_ml)
        self._measurement_lap_start_abs_dist_m = float(cross_abs_dist_m)

    @property
    def session_dist_m(self):
        return self._session_dist_m

    @property
    def current_lap_fuel_ml(self):
        if not self.measurement_active:
            return 0.0
        return max(self._last_cumul_fuel_ml - self._measurement_lap_start_fuel_ml, 0.0)

    def current_lap_fuel(self, cumul_fuel_ml):
        if not self.measurement_active:
            return 0.0
        return max(float(cumul_fuel_ml) - self._measurement_lap_start_fuel_ml, 0.0)

    @property
    def current_lap_dist_m(self):
        if not self.measurement_active:
            return 0.0
        return max(self._session_dist_m - self._measurement_lap_start_abs_dist_m, 0.0)

    @property
    def measurement_dist_m(self):
        if not self.measurement_active:
            return 0.0
        return max(self._session_dist_m - self.measurement_start_abs_dist_m, 0.0)

    @property
    def measurement_lap_start_abs_dist_m(self):
        return self._measurement_lap_start_abs_dist_m

    @property
    def current_lap_progress(self):
        if self.lap_distance_m <= 0.0:
            return 0.0
        progress = self.current_lap_dist_m / self.lap_distance_m
        if progress < 0.0:
            return 0.0
        if progress > 1.5:
            return 1.5
        return progress


tracker = LapTracker()


def init_tracker(vehicle, strategy):
    global tracker
    lap_d = float(strategy.get("lap_distance_m", vehicle.get("lap_distance_m", 2202.0)))
    tracker = LapTracker(lap_distance_m=lap_d)
