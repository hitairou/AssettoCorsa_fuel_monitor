# modules/smoothing.py
# Simple moving-average and derivative helpers.
# All pure Python, no external deps.

class MovingAverage(object):
    """Fixed-window moving average using a circular buffer."""

    def __init__(self, window=5):
        self._window = max(1, window)
        self._buf    = []
        self._sum    = 0.0

    def update(self, value):
        self._buf.append(float(value))
        self._sum += float(value)
        if len(self._buf) > self._window:
            self._sum -= self._buf.pop(0)
        return self.value

    @property
    def value(self):
        if not self._buf:
            return 0.0
        return self._sum / len(self._buf)

    def reset(self):
        self._buf = []
        self._sum = 0.0


class BoundedDerivative(object):
    """
    Computes dy/dt from successive (t, y) samples.
    Clips the result to [-max_abs, +max_abs] to suppress spikes.
    """

    def __init__(self, max_abs=50.0):
        self._max_abs  = max_abs
        self._prev_y   = None
        self._prev_t   = None
        self.value     = 0.0

    def update(self, t, y):
        if self._prev_t is None or (t - self._prev_t) < 1e-9:
            self._prev_y = y
            self._prev_t = t
            return self.value

        dt  = t - self._prev_t
        dy  = y - self._prev_y
        raw = dy / dt

        # Clamp to suppress sensors spikes
        if raw >  self._max_abs:
            raw =  self._max_abs
        elif raw < -self._max_abs:
            raw = -self._max_abs

        self.value     = raw
        self._prev_y   = y
        self._prev_t   = t
        return self.value

    def reset(self):
        self._prev_y = None
        self._prev_t = None
        self.value   = 0.0
