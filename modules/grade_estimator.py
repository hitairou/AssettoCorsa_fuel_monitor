# modules/grade_estimator.py
# Dynamic road grade estimation from distanceTraveled + carCoordinates.
# Falls back to pitch -> CSV -> zero when data is unavailable.

import math
from modules.smoothing import MovingAverage
from modules.app_state  import state

# ---------------------------------------------------------------------------
# Fallback CSV lookup (loaded lazily)
# ---------------------------------------------------------------------------
_csv_dist  = None
_csv_grade = None

def _load_csv_fallback():
    global _csv_dist, _csv_grade
    if _csv_dist is not None:
        return
    try:
        from modules.data_loader import load_csv_1d
        xs, ys = load_csv_1d("suzuka_east_grade.csv")
        _csv_dist  = xs
        _csv_grade = ys
    except Exception:
        _csv_dist  = []
        _csv_grade = []


def _csv_lookup(dist_m):
    """Linear interpolation in the fallback CSV."""
    _load_csv_fallback()
    if not _csv_dist:
        return 0.0
    lap_dist = state.vehicle.get("lap_distance_m", 2202.0)
    d = dist_m % max(lap_dist, 1.0)
    xs = _csv_dist
    ys = _csv_grade
    if d <= xs[0]:
        return ys[0]
    if d >= xs[-1]:
        return ys[-1]
    # Binary search
    lo, hi = 0, len(xs) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= d:
            lo = mid
        else:
            hi = mid
    t = (d - xs[lo]) / (xs[hi] - xs[lo])
    return ys[lo] + t * (ys[hi] - ys[lo])


# ---------------------------------------------------------------------------
# GradeEstimator
# ---------------------------------------------------------------------------

class GradeEstimator(object):

    def __init__(self, vertical_axis=1, grade_window=5,
                 grade_min_ds=0.05, grade_max_abs=0.5,
                 fallback_mode="pitch"):
        self.vertical_axis  = int(vertical_axis)   # 0=X, 1=Y, 2=Z
        self.grade_min_ds   = float(grade_min_ds)
        self.grade_max_abs  = float(grade_max_abs)
        self.fallback_mode  = str(fallback_mode)

        self._ma = MovingAverage(window=grade_window)

        self._prev_dist   = None
        self._prev_height = None
        self._last_grade  = 0.0

    def reset(self):
        self._ma.reset()
        self._prev_dist   = None
        self._prev_height = None
        self._last_grade  = 0.0

    def update(self, dist_m, coords, pitch_rad, session_dist_m=None):
        """
        Estimate road grade.

        Parameters
        ----------
        dist_m       : distanceTraveled from shared memory
        coords       : carCoordinates list [x, y, z]
        pitch_rad    : vehicle pitch angle [rad] (fallback only)
        session_dist_m : monotonic session distance (used for CSV lookup)

        Returns
        -------
        grade_smooth : smoothed dh/ds estimate
        source       : "dynamic" | "pitch" | "csv" | "zero"
        """

        # Validate coords
        coords_ok = (
            coords is not None
            and len(coords) == 3
            and not all(c == 0.0 for c in coords)
        )

        if coords_ok:
            result = self._dynamic_update(dist_m, coords)
            if result is not None:
                state.grade_source = "dynamic"
                return result, "dynamic"

        # Fallback chain
        return self._fallback(pitch_rad, session_dist_m)

    def _dynamic_update(self, dist_m, coords):
        """
        Returns smoothed grade or None if update is skipped.
        """
        try:
            h = float(coords[self.vertical_axis])
        except (IndexError, TypeError, ValueError):
            return None

        if self._prev_dist is None:
            self._prev_dist   = dist_m
            self._prev_height = h
            return None

        ds = dist_m - self._prev_dist
        dh = h - self._prev_height

        # Update prev values regardless of ds magnitude
        self._prev_dist   = dist_m
        self._prev_height = h

        if abs(ds) < self.grade_min_ds:
            # Reuse last grade, still pass through MA
            grade_raw = self._last_grade
        else:
            grade_raw = dh / ds
            # Clamp noise
            if grade_raw >  self.grade_max_abs:
                grade_raw =  self.grade_max_abs
            elif grade_raw < -self.grade_max_abs:
                grade_raw = -self.grade_max_abs
            self._last_grade = grade_raw

        smoothed = self._ma.update(grade_raw)
        return smoothed

    def _fallback(self, pitch_rad, session_dist_m):
        mode = self.fallback_mode

        if mode == "pitch":
            # pitch is vehicle body angle; use as approximate grade
            g = math.tan(float(pitch_rad)) if pitch_rad else 0.0
            if abs(g) > self.grade_max_abs:
                g = math.copysign(self.grade_max_abs, g)
            smoothed = self._ma.update(g)
            return smoothed, "pitch"

        if mode == "csv":
            d = session_dist_m if session_dist_m is not None else 0.0
            g = _csv_lookup(d)
            smoothed = self._ma.update(g)
            return smoothed, "csv"

        # Final fallback
        smoothed = self._ma.update(0.0)
        return smoothed, "zero"


# Module-level singleton (initialised in acMain with config values)
estimator = GradeEstimator()


def init_estimator(strategy):
    """Call once from acMain after config is loaded."""
    global estimator
    vi = int(strategy.get("vertical_axis_index", 1))
    gw = int(strategy.get("grade_window", 5))
    gds = float(strategy.get("grade_min_ds", 0.05))
    gma = float(strategy.get("grade_max_abs", 0.5))
    fm  = str(strategy.get("grade_fallback_mode", "pitch"))
    estimator = GradeEstimator(
        vertical_axis=vi, grade_window=gw,
        grade_min_ds=gds, grade_max_abs=gma,
        fallback_mode=fm
    )
