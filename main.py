"""
Anti-Procrastination Coach – main.py
Application entry point. Bootstraps the database, sets up logging,
and launches the PyQt5 application flow.
"""

import logging
import sys
from pathlib import Path

# ── Ensure project root is on PYTHONPATH ─────────────────────────────── #
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtGui import QFont  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from database.db_connection import initialize_database  # noqa: E402
from gui.login_window import LoginWindow  # noqa: E402

logger = logging.getLogger("APC")


def configure_logging():
    """Attach file + stdout handlers. Safe to call more than once."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "apc.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def prepare_environment():
    """Create the database and runtime directories."""
    initialize_database()
    logger.info("Database ready")
    for sub in ["resources/images", "resources/icons", "resources/sounds",
                "reports/daily_reports", "reports/weekly_reports"]:
        (PROJECT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def main():
    configure_logging()
    prepare_environment()

    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Anti-Procrastination Coach")
    app.setOrganizationName("APC")
    app.setFont(QFont("Segoe UI", 10))

    # ── State machine: login → dashboard ─────────────────────────────── #
    _active_windows = {}   # keep references alive

    def show_login():
        win = LoginWindow(on_login_success=on_login)
        win.show()
        _active_windows["login"] = win

    def on_login(user: dict):
        """Called when login succeeds."""
        login_win = _active_windows.pop("login", None)
        if login_win:
            login_win.close()

        from gui.dashboard import Dashboard
        dash = Dashboard(user)
        dash.logout_signal.connect(show_login)
        dash.show()
        _active_windows["dashboard"] = dash
        logger.info("Opened dashboard for user: %s", user["name"])

    show_login()
    exit_code = app.exec_()
    logger.info("Application exited with code %d", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
