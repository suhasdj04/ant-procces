"""
Mouse Tracker
Tracks mouse movement distance and click rate.
"""

import logging
import math
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

try:
    from pynput import mouse as ms
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not available – mouse tracking disabled")


class MouseTracker:
    """Measures mouse movement and click frequency."""

    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self._click_times: deque = deque()
        self._move_distance = 0.0
        self._last_pos = None
        self._lock = threading.Lock()
        self._listener = None
        self._running   = False

    # ------------------------------------------------------------------ #

    def start(self):
        if not PYNPUT_AVAILABLE or self._running:
            return
        self._running = True
        with self._lock:
            # Forget the last position so the first move after a restart
            # can't measure a huge jump from a previous session.
            self._last_pos = None
        self._listener = ms.Listener(
            on_move=self._on_move,
            on_click=self._on_click
        )
        self._listener.start()
        logger.info("MouseTracker started")

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("MouseTracker stopped")

    def get_click_rate(self) -> float:
        """Clicks per minute over rolling window."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            while self._click_times and self._click_times[0] < cutoff:
                self._click_times.popleft()
            count = len(self._click_times)
        return (count / self.window_seconds) * 60

    def get_move_distance(self) -> float:
        """Cumulative pixel distance moved since start/reset."""
        with self._lock:
            return self._move_distance

    def reset_distance(self):
        with self._lock:
            self._move_distance = 0.0

    # ------------------------------------------------------------------ #

    def _on_move(self, x, y):
        if not self._running:
            return
        with self._lock:
            if self._last_pos:
                dx = x - self._last_pos[0]
                dy = y - self._last_pos[1]
                self._move_distance += math.hypot(dx, dy)
            self._last_pos = (x, y)

    def _on_click(self, x, y, button, pressed):
        if self._running and pressed:
            with self._lock:
                self._click_times.append(time.time())
