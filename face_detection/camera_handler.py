"""
Camera Handler
Manages webcam capture in a background thread and emits frames via a callback.
"""

import logging
import platform
import threading
import time

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraHandler:
    """Thread-safe webcam capture that calls frame_callback(frame) on each new frame."""

    def __init__(self, camera_index: int = 0, fps: int = 15):
        self.camera_index  = camera_index
        self.fps           = fps
        self._cap: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._running      = False
        self._frame_callback = None
        self._lock         = threading.Lock()
        self._latest_frame: np.ndarray | None = None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def start(self, frame_callback=None):
        """Open camera and start capture thread."""
        if self._running:
            return True
        self._frame_callback = frame_callback

        # DirectShow avoids device locking issues on Windows; other
        # platforms use the default backend.
        if platform.system() == "Windows":
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            # Retry with the default backend before giving up
            self._cap.release()
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            logger.error("Cannot open camera index %s", self.camera_index)
            return False
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info("Camera %s started", self.camera_index)
        return True

    def stop(self):
        """Stop capture thread and release camera."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
            self._cap = None
        logger.info("Camera stopped")

    def get_latest_frame(self) -> np.ndarray | None:
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _capture_loop(self):
        interval = 1.0 / self.fps
        while self._running:
            if self._cap and self._cap.isOpened():
                ret, frame = self._cap.read()
                if ret:
                    with self._lock:
                        self._latest_frame = frame
                    if self._frame_callback:
                        self._frame_callback(frame)
                else:
                    logger.warning("Frame read failed – retrying")
                    time.sleep(0.1)
            time.sleep(interval)
