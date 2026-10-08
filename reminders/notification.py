"""
Notification
Desktop toast notifications (Windows) with a PyQt5 fallback.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from win10toast import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False


class Notifier:
    """Send desktop notifications. Falls back to a no-op if win10toast missing."""

    def __init__(self, app_name: str = "Anti-Procrastination Coach"):
        self.app_name = app_name
        self._toast = ToastNotifier() if TOAST_AVAILABLE else None

    def send(self, title: str, message: str, duration: int = 5):
        if self._toast:
            try:
                self._toast.show_toast(
                    title,
                    message,
                    duration=duration,
                    threaded=True
                )
                return
            except Exception as e:
                logger.error("Toast notification error: %s", e)
        # Fallback — just log
        logger.info("[NOTIFICATION] %s: %s", title, message)
