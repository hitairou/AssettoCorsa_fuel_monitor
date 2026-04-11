# modules/bsfc_interp.py
# Bilinear interpolation for BSFC map and 1-D Tmax lookup.
# Pure Python, no scipy/numpy.

_EPSILON = 1e-9


# ---------------------------------------------------------------------------
# 1-D linear interpolation helper
# ---------------------------------------------------------------------------

def _lerp1d(xs, ys, x):
    """Linear interpolation / extrapolation clamped to table boundary."""
    if not xs:
        return 0.0
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    # Binary search
    lo, hi = 0, len(xs) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    t = (x - xs[lo]) / max(xs[hi] - xs[lo], _EPSILON)
    return ys[lo] + t * (ys[hi] - ys[lo])


# ---------------------------------------------------------------------------
# BSFCInterpolator
# ---------------------------------------------------------------------------

class BSFCInterpolator(object):
    """
    Bilinear interpolation over a 2-D BSFC map.
    Axes: rpm (rows), load (columns).
    """

    def __init__(self, rpm_axis, load_axis, table):
        """
        Parameters
        ----------
        rpm_axis  : list of float, ascending
        load_axis : list of float, ascending (0.0 .. 1.0)
        table     : list of list of float [rpm_idx][load_idx]
        """
        self.rpm_axis  = rpm_axis
        self.load_axis = load_axis
        self.table     = table
        self._valid    = (
            len(rpm_axis) > 0
            and len(load_axis) > 0
            and len(table) == len(rpm_axis)
        )

    def query(self, rpm, load):
        """
        Returns BSFC [g/kWh] for given rpm and load.
        Falls back to 400 g/kWh if table is empty.
        """
        if not self._valid:
            return 400.0

        # Clamp inputs
        rpm  = max(self.rpm_axis[0],  min(self.rpm_axis[-1],  float(rpm)))
        load = max(self.load_axis[0], min(self.load_axis[-1], float(load)))

        # Find surrounding rpm indices
        r_lo, r_hi = self._bracket(self.rpm_axis, rpm)
        l_lo, l_hi = self._bracket(self.load_axis, load)

        # Bilinear weights
        r_range = self.rpm_axis[r_hi]  - self.rpm_axis[r_lo]
        l_range = self.load_axis[l_hi] - self.load_axis[l_lo]

        tr = ((rpm  - self.rpm_axis[r_lo])  / max(r_range, _EPSILON)) if r_lo != r_hi else 0.0
        tl = ((load - self.load_axis[l_lo]) / max(l_range, _EPSILON)) if l_lo != l_hi else 0.0

        v00 = self.table[r_lo][l_lo]
        v01 = self.table[r_lo][l_hi]
        v10 = self.table[r_hi][l_lo]
        v11 = self.table[r_hi][l_hi]

        bsfc = (
            v00 * (1 - tr) * (1 - tl)
            + v01 * (1 - tr) * tl
            + v10 * tr * (1 - tl)
            + v11 * tr * tl
        )
        return bsfc

    @staticmethod
    def _bracket(axis, val):
        lo, hi = 0, len(axis) - 1
        if val <= axis[lo]:
            return lo, lo
        if val >= axis[hi]:
            return hi, hi
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if axis[mid] <= val:
                lo = mid
            else:
                hi = mid
        return lo, hi


# ---------------------------------------------------------------------------
# Tmax lookup (1-D)
# ---------------------------------------------------------------------------

class TmaxLookup(object):
    def __init__(self, rpm_axis, tmax_axis):
        self._rpm  = rpm_axis
        self._tmax = tmax_axis

    def query(self, rpm):
        if not self._rpm:
            return 6.0   # Fallback: 6 Nm
        return _lerp1d(self._rpm, self._tmax, float(rpm))


# ---------------------------------------------------------------------------
# Low-load BSFC correction
# ---------------------------------------------------------------------------

def low_load_correction(bsfc, load, threshold=0.2, max_penalty=1.5):
    """
    Worsen BSFC below low-load threshold.
    Below threshold=0.2, linearly increase BSFC up to max_penalty * bsfc at load=0.
    """
    if load >= threshold:
        return bsfc
    # Linear penalty: 1.0 at load=threshold, max_penalty at load=0
    t = 1.0 - (load / max(threshold, _EPSILON))
    factor = 1.0 + (max_penalty - 1.0) * t
    return bsfc * factor


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def build_bsfc_interpolator():
    from modules.data_loader import load_csv_2d
    rpm_axis, load_axis, table = load_csv_2d("bsfc_map.csv")
    return BSFCInterpolator(rpm_axis, load_axis, table)


def build_tmax_lookup():
    from modules.data_loader import load_csv_1d
    xs, ys = load_csv_1d("tmax_map.csv")
    return TmaxLookup(xs, ys)
