# modules/history_buffers.py
# Fixed-size ring buffer for time-series history (10 s power graph, BSFC trace).


class RingBuffer(object):
    """Fixed-size circular buffer of floats. Thread-unsafe; AC is single-threaded."""

    def __init__(self, maxlen):
        self._buf    = [0.0] * int(maxlen)
        self._maxlen = int(maxlen)
        self._head   = 0    # next write position
        self._size   = 0    # number of valid entries

    def append(self, value):
        self._buf[self._head] = float(value)
        self._head = (self._head + 1) % self._maxlen
        if self._size < self._maxlen:
            self._size += 1

    def to_list(self):
        """Return contents in chronological order (oldest first)."""
        if self._size == 0:
            return []
        if self._size < self._maxlen:
            return list(self._buf[:self._size])
        # Full: read starting from head (oldest entry)
        idx = self._head
        return self._buf[idx:] + self._buf[:idx]

    def clear(self):
        self._buf  = [0.0] * self._maxlen
        self._head = 0
        self._size = 0

    def __len__(self):
        return self._size

    @property
    def full(self):
        return self._size == self._maxlen

    @property
    def maxlen(self):
        return self._maxlen
