"""
Screen Monitor
Captures screenshots periodically and computes an activity score based on pixel changes.
"""

import logging
import threading

import numpy as np

logger = logging.getLogger(__name__)

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not available – screen monitoring disabled")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ScreenMonitor:
    """
    Compares successive screenshots to detect on-screen changes.
    High change → active work; low change → possible idle/distraction.
    """

    def __init__(self, interval_seconds: float = 5.0, thumb_size: tuple = (320, 180)):
        self.interval = interval_seconds
        self.thumb_size = thumb_size
        self._prev_arr: np.ndarray | None = None
        self._change_score: float = 0.0
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------ #

    def start(self):
        if not PYAUTOGUI_AVAILABLE or not PIL_AVAILABLE or self._running:
            return
        self._running = True
        self._stop_event.clear()
        with self._lock:
            self._prev_arr = None
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("ScreenMonitor started (interval=%.1fs)", self.interval)

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval + 1)
            self._thread = None
        logger.info("ScreenMonitor stopped")

    def get_change_score(self) -> float:
        """0.0 (no change) – 1.0 (completely different screen)."""
        with self._lock:
            return self._change_score

    # ------------------------------------------------------------------ #

    def _capture_thumb(self) -> np.ndarray | None:
        try:
            screenshot = pyautogui.screenshot()
            thumb = screenshot.resize(self.thumb_size, Image.LANCZOS)
            return np.array(thumb.convert("L"), dtype=np.float32)
        except Exception as e:
            logger.error("Screenshot error: %s", e)
            return None

    def _monitor_loop(self):
        while self._running:
            arr = self._capture_thumb()
            if arr is not None:
                with self._lock:
                    if self._prev_arr is not None:
                        diff = np.abs(arr - self._prev_arr)
                        self._change_score = float(np.mean(diff) / 255.0)
                    self._prev_arr = arr
            # Interruptible sleep so stop() doesn't wait for the full interval
            if self._stop_event.wait(self.interval):
                break
