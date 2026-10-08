"""
Keyboard Tracker
Tracks keyboard activity to infer user engagement.
"""

import logging
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

try:
    from pynput import keyboard as kb
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput not available – keyboard tracking disabled")


class KeyboardTracker:
    """Counts keystrokes in a rolling window to detect activity bursts."""

    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        self._listener = None
        self._running   = False

    # ------------------------------------------------------------------ #

    def start(self):
        if not PYNPUT_AVAILABLE or self._running:
            return
        self._running = True
        self._listener = kb.Listener(on_press=self._on_press)
        self._listener.start()
        logger.info("KeyboardTracker started")

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        logger.info("KeyboardTracker stopped")

    def get_keystroke_rate(self) -> float:
        """Return keystrokes per minute over the rolling window."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            count = len(self._timestamps)
        return (count / self.window_seconds) * 60

    def get_total_keystrokes(self) -> int:
        with self._lock:
            return len(self._timestamps)

    # ------------------------------------------------------------------ #

    def _on_press(self, key):
        if self._running:
            with self._lock:
                self._timestamps.append(time.time())
