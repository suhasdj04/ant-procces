"""
Scheduler
Periodic reminder scheduler using the `schedule` library + background thread.
"""

import logging
import threading
import time

import schedule as sched

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """
    Runs scheduled jobs (e.g. hourly reminders, daily report generation).
    Jobs are added with add_job() and the scheduler runs in a daemon thread.
    """

    def __init__(self):
        self._thread: threading.Thread | None = None
        self._running = False
        self._scheduler = sched.Scheduler()

    def add_job(self, interval_minutes: int, func, *args, **kwargs):
        """Schedule func to run every interval_minutes."""
        self._scheduler.every(interval_minutes).minutes.do(func, *args, **kwargs)
        logger.info("Scheduled job %s every %d min", func.__name__, interval_minutes)

    def add_daily_job(self, time_str: str, func, *args, **kwargs):
        """Schedule func to run daily at time_str (HH:MM)."""
        self._scheduler.every().day.at(time_str).do(func, *args, **kwargs)
        logger.info("Scheduled daily job %s at %s", func.__name__, time_str)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("ReminderScheduler started")

    def stop(self):
        self._running = False
        self._scheduler.clear()
        logger.info("ReminderScheduler stopped")

    def _run_loop(self):
        while self._running:
            self._scheduler.run_pending()
            time.sleep(1)
