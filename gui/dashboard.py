"""
Main Dashboard Window
Hub window containing: Focus session control, live camera feed, Pomodoro timer,
activity stats, and quick navigation to Analytics, Reports, and Settings.
"""

import logging
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from analytics.report_generator import generate_daily_report
from database.session_model import end_session, get_session_stats, log_activity, start_session
from gui import preferences as prefs
from gui.styles import (
    AMBER,
    BG_CARD,
    BG_SURFACE,
    BORDER,
    DANGER,
    MAIN_STYLESHEET,
    PURPLE,
    PURPLE_GLOW,
    ROSE,
    SUCCESS,
    TEAL,
    TEXT_PRI,
    TEXT_SEC,
)

logger = logging.getLogger(__name__)


# ── Worker thread for camera + detection ──────────────────────────────── #

class DetectionWorker(QThread):
    """Runs camera capture + face detection off the main thread."""
    frame_ready      = pyqtSignal(object)   # annotated QImage
    status_update    = pyqtSignal(dict)     # detection result dict
    distraction_detected = pyqtSignal()
    error            = pyqtSignal(str)      # fatal worker error (e.g. camera)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._distraction_cooldown = 0

    def run(self):
        import cv2

        from face_detection.camera_handler import CameraHandler
        from face_detection.detector import FaceDetector
        from face_detection.eye_tracking import EyeTracker

        cam  = CameraHandler()
        det  = FaceDetector()
        eyes = EyeTracker()

        if not cam.start():
            logger.error("Cannot open camera in worker")
            self.error.emit(
                "Could not open the webcam.\n\n"
                "Check that a camera is connected and not being used by another app."
            )
            return

        self._running = True
        while self._running:
            frame = cam.get_latest_frame()
            if frame is None:
                self.msleep(50)
                continue

            result = det.detect(frame)
            eye_result = eyes.analyse_frame(
                result["annotated_frame"], result["faces"]
            )
            annotated = eye_result["annotated_frame"]

            # Convert to QImage for the GUI
            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)
            self.status_update.emit({
                "is_present":   result["is_present"],
                "is_distracted": result["is_distracted"],
                "is_drowsy":    eye_result["is_drowsy"],
                "face_count":   result["face_count"],
            })

            # Cooldown ticks down every frame so it always expires,
            # even while the user stays distracted.
            if self._distraction_cooldown > 0:
                self._distraction_cooldown -= 1
            if (result["is_distracted"] or eye_result["is_drowsy"]) \
                    and self._distraction_cooldown <= 0:
                self.distraction_detected.emit()
                self._distraction_cooldown = 45   # ~3 s between reminders

            self.msleep(66)   # ~15 fps

        cam.stop()
        det.reset()
        eyes.reset()

    def stop(self):
        self._running = False
        if not self.wait(5000):
            logger.warning("DetectionWorker did not finish within 5 s")


# ── Stat card widget ───────────────────────────────────────────────────── #

class StatCard(QFrame):
    def __init__(self, title: str, value: str, unit: str = "", icon: str = "", colour: str = PURPLE):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {colour}44;
                border-radius: 14px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(2)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 18))
        top.addWidget(icon_lbl)
        top.addStretch()
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 9))
        title_lbl.setStyleSheet(f"color: {TEXT_SEC};")
        lay.addLayout(top)
        lay.addWidget(title_lbl)

        self._val_lbl = QLabel(f"{value} {unit}")
        self._val_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self._val_lbl.setStyleSheet(f"color: {colour};")
        lay.addWidget(self._val_lbl)

    def update_value(self, value: str, unit: str = ""):
        self._val_lbl.setText(f"{value} {unit}".strip())


# ── Pomodoro timer widget ──────────────────────────────────────────────── #

class PomodoroWidget(QFrame):
    break_signal  = pyqtSignal()
    resume_signal = pyqtSignal()

    CYCLE_LENGTH = 4   # work sessions before a long break

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(170)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {TEAL}55;
                border-radius: 14px;
            }}
        """)
        self._work_min   = prefs.work_minutes()
        self._break_min  = prefs.break_minutes()
        self._long_break_min = prefs.long_break_minutes()
        self._cycle      = 0
        self._seconds_left = self._work_min * 60
        self._is_work = True
        self._running = False
        self._timer = QTimer()
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 12, 20, 12)
        lay.setSpacing(6)

        header = QHBoxLayout()
        phase_label = QLabel("🍅  Pomodoro Timer")
        phase_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._phase_lbl = QLabel("Work Session")
        self._phase_lbl.setStyleSheet(f"color: {TEAL}; font-size: 11px; font-weight: 600;")
        header.addWidget(phase_label)
        header.addStretch()
        header.addWidget(self._phase_lbl)
        lay.addLayout(header)

        self._time_lbl = QLabel(f"{self._work_min:02d}:00")
        self._time_lbl.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self._time_lbl.setAlignment(Qt.AlignCenter)
        self._time_lbl.setStyleSheet(f"color: {TEAL};")
        lay.addWidget(self._time_lbl)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(6)
        self._progress.setRange(0, self._work_min * 60)
        self._progress.setValue(self._work_min * 60)
        self._progress.setTextVisible(False)
        lay.addWidget(self._progress)

        btns = QHBoxLayout()
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setFixedHeight(34)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._toggle)
        self._reset_btn = QPushButton("↺  Reset")
        self._reset_btn.setFixedHeight(34)
        self._reset_btn.setObjectName("successBtn")
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset)
        btns.addWidget(self._start_btn)
        btns.addWidget(self._reset_btn)
        lay.addLayout(btns)

    def _toggle(self):
        if self._running:
            self._timer.stop()
            self._running = False
            self._start_btn.setText("▶  Resume")
        else:
            self._timer.start()
            self._running = True
            self._start_btn.setText("⏸  Pause")

    def _reset(self):
        self._timer.stop()
        self._running = False
        self._is_work = True
        self._cycle = 0
        self._seconds_left = self._work_min * 60
        self._progress.setRange(0, self._work_min * 60)
        self._progress.setValue(self._work_min * 60)
        self._start_btn.setText("▶  Start")
        self._phase_lbl.setText("Work Session")
        self._time_lbl.setStyleSheet(f"color: {TEAL};")
        self._update_display()

    def _tick(self):
        self._seconds_left -= 1
        if self._seconds_left <= 0:
            if self._is_work:
                self._is_work = False
                self._cycle += 1
                long_break = self._cycle % self.CYCLE_LENGTH == 0
                break_min = self._long_break_min if long_break else self._break_min
                self._seconds_left = break_min * 60
                self._progress.setRange(0, break_min * 60)
                self._progress.setValue(break_min * 60)
                if long_break:
                    self._phase_lbl.setText("Long Break 🌴")
                else:
                    self._phase_lbl.setText("Break Time ☕")
                self._time_lbl.setStyleSheet(f"color: {AMBER};")
                self.break_signal.emit()
            else:
                self._is_work = True
                self._seconds_left = self._work_min * 60
                self._progress.setRange(0, self._work_min * 60)
                self._progress.setValue(self._work_min * 60)
                self._phase_lbl.setText("Work Session")
                self._time_lbl.setStyleSheet(f"color: {TEAL};")
                self.resume_signal.emit()
        self._progress.setValue(self._seconds_left)
        self._update_display()

    def _update_display(self):
        m, s = divmod(self._seconds_left, 60)
        self._time_lbl.setText(f"{m:02d}:{s:02d}")


# ── Main Dashboard ─────────────────────────────────────────────────────── #

class Dashboard(QMainWindow):
    logout_signal = pyqtSignal()

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.session_id: int | None = None
        self._distraction_count = 0
        self._session_seconds   = 0
        self._session_active    = False
        self._worker: DetectionWorker | None = None
        self._retired_workers: list[DetectionWorker] = []
        self._face_present = False

        self.setWindowTitle(f"APC Dashboard – {user['name']}")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()
        self._session_clock = QTimer()
        self._session_clock.setInterval(1000)
        self._session_clock.timeout.connect(self._tick_session)

        # Import deferred to avoid circular imports
        self._voice = None
        self._scorer = None
        self._kbd    = None
        self._mouse  = None
        self._screen = None
        self._notifier = None
        self._init_subsystems()

    # ------------------------------------------------------------------ #
    #  UI Construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        root.addWidget(self._build_sidebar())

        # Main area
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Top bar
        main_layout.addLayout(self._build_topbar())

        # Content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left column: camera + pomodoro
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(14)
        left_lay.addWidget(self._build_camera_widget())
        self.pomodoro = PomodoroWidget()
        self.pomodoro.break_signal.connect(self._on_break)
        self.pomodoro.resume_signal.connect(self._on_resume)
        left_lay.addWidget(self.pomodoro)
        left_lay.addStretch()
        splitter.addWidget(left)

        # Right column: stats + controls
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(14)
        right_lay.addWidget(self._build_stat_cards())
        right_lay.addWidget(self._build_session_controls())
        right_lay.addWidget(self._build_status_panel())
        right_lay.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([520, 620])
        main_layout.addWidget(splitter)
        root.addWidget(main_area)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SURFACE};
                border-right: 1px solid {BORDER};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 20)
        lay.setSpacing(4)

        logo_area = QWidget()
        logo_area.setFixedHeight(80)
        logo_area.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {PURPLE}, stop:1 {TEAL});
        """)
        logo_lay = QVBoxLayout(logo_area)
        logo_lbl = QLabel("🎯 APC")
        logo_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setStyleSheet("color: white; background: transparent;")
        logo_lay.addWidget(logo_lbl)
        lay.addWidget(logo_area)
        lay.addSpacing(16)

        nav_items = [
            ("🏠", "Dashboard",  self._noop),
            ("📊", "Analytics",  self._open_analytics),
            ("📋", "Reports",    self._open_reports),
            ("⚙️", "Settings",   self._open_settings),
        ]
        for icon, label, slot in nav_items:
            btn = self._nav_btn(icon, label)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        lay.addStretch()

        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border-radius: 10px;
                margin: 8px;
            }}
        """)
        u_lay = QVBoxLayout(user_frame)
        u_lay.setContentsMargins(12, 10, 12, 10)
        name_lbl = QLabel(f"👤 {self.user['name']}")
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setStyleSheet("background: transparent;")
        email_lbl = QLabel(self.user["email"])
        email_lbl.setFont(QFont("Segoe UI", 8))
        email_lbl.setStyleSheet(f"color: {TEXT_SEC}; background: transparent;")
        u_lay.addWidget(name_lbl)
        u_lay.addWidget(email_lbl)
        lay.addWidget(user_frame)

        logout_btn = QPushButton("← Logout")
        logout_btn.setObjectName("dangerBtn")
        logout_btn.setFixedHeight(36)
        logout_btn.setStyleSheet(logout_btn.styleSheet() + "margin: 0 10px;")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        lay.addWidget(logout_btn)

        return sidebar

    @staticmethod
    def _nav_btn(icon: str, label: str) -> QPushButton:
        btn = QPushButton(f"  {icon}  {label}")
        btn.setFixedHeight(46)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SEC};
                border: none;
                border-radius: 0;
                text-align: left;
                padding-left: 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BG_CARD};
                color: {TEXT_PRI};
            }}
        """)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def _build_topbar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        greeting_lbl = QLabel(self._greeting())
        greeting_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))

        self._date_lbl = QLabel(datetime.now().strftime("%A, %d %B %Y"))
        self._date_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        self._date_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        bar.addWidget(greeting_lbl)
        bar.addStretch()
        bar.addWidget(self._date_lbl)
        return bar

    def _build_camera_widget(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFixedHeight(300)
        frame.setStyleSheet(f"""
            QFrame {{
                background: #050510;
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)

        self._cam_label = QLabel("Camera feed will appear here when session starts")
        self._cam_label.setAlignment(Qt.AlignCenter)
        self._cam_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        self._cam_label.setScaledContents(True)
        lay.addWidget(self._cam_label)
        return frame

    def _build_stat_cards(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        stats = get_session_stats(self.user["user_id"])

        self._card_sessions = StatCard(
            "Total Sessions", str(stats.get("total_sessions", 0)), "", "📅", PURPLE)
        self._card_focus = StatCard(
            "Focus Hours", f"{stats.get('total_minutes', 0)/60:.1f}", "hr", "⏱️", TEAL)
        self._card_score = StatCard(
            "Avg Score", f"{stats.get('avg_score', 0):.0f}", "/100", "⭐", AMBER)
        self._card_distractions = StatCard(
            "Distractions", str(stats.get("total_distractions", 0)), "", "⚠️", ROSE)

        grid.addWidget(self._card_sessions,     0, 0)
        grid.addWidget(self._card_focus,        0, 1)
        grid.addWidget(self._card_score,        1, 0)
        grid.addWidget(self._card_distractions, 1, 1)
        return w

    def _build_session_controls(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 4px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        lbl = QLabel("🎯  Focus Session")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lay.addWidget(lbl)

        self._session_timer_lbl = QLabel("00:00:00")
        self._session_timer_lbl.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self._session_timer_lbl.setAlignment(Qt.AlignCenter)
        self._session_timer_lbl.setStyleSheet(f"color: {PURPLE_GLOW};")
        lay.addWidget(self._session_timer_lbl)

        self._start_btn = QPushButton("▶  Start Focus Session")
        self._start_btn.setFixedHeight(44)
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.clicked.connect(self._toggle_session)
        lay.addWidget(self._start_btn)
        return frame

    def _build_status_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(8)

        lbl = QLabel("📡  Live Status")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lay.addWidget(lbl)

        self._status_face  = self._status_row("👤 Face detected",       "Waiting…")
        self._status_focus = self._status_row("🎯 Attention state",     "Waiting…")
        self._status_score = self._status_row("📈 Current score",       "—")
        self._status_dist  = self._status_row("⚠️  Session distractions","0")
        lay.addWidget(self._status_face[0])
        lay.addWidget(self._status_focus[0])
        lay.addWidget(self._status_score[0])
        lay.addWidget(self._status_dist[0])
        return frame

    @staticmethod
    def _status_row(title: str, value: str):
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 6, 10, 6)
        t_lbl = QLabel(title)
        t_lbl.setFont(QFont("Segoe UI", 10))
        t_lbl.setStyleSheet("background: transparent;")
        v_lbl = QLabel(value)
        v_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        v_lbl.setStyleSheet(f"color: {PURPLE_GLOW}; background: transparent;")
        v_lbl.setAlignment(Qt.AlignRight)
        lay.addWidget(t_lbl)
        lay.addStretch()
        lay.addWidget(v_lbl)
        return row, v_lbl

    # ------------------------------------------------------------------ #
    #  Subsystem Init                                                      #
    # ------------------------------------------------------------------ #

    def _init_subsystems(self):
        try:
            from reminders.voice_reminder import VoiceReminder
            self._voice = VoiceReminder(rate=prefs.speech_rate())
        except Exception as e:
            logger.warning("VoiceReminder unavailable: %s", e)

        try:
            from analytics.productivity_score import ProductivityScorer
            self._scorer = ProductivityScorer()
        except Exception as e:
            logger.warning("Scorer unavailable: %s", e)

        try:
            from activity_monitor.keyboard_tracker import KeyboardTracker
            self._kbd = KeyboardTracker()
        except Exception as e:
            logger.warning("KBD tracker unavailable: %s", e)

        try:
            from activity_monitor.mouse_tracker import MouseTracker
            self._mouse = MouseTracker()
        except Exception as e:
            logger.warning("Mouse tracker unavailable: %s", e)

        try:
            from activity_monitor.screen_monitor import ScreenMonitor
            self._screen = ScreenMonitor()
        except Exception as e:
            logger.warning("Screen monitor unavailable: %s", e)

        try:
            from reminders.notification import Notifier
            self._notifier = Notifier()
        except Exception as e:
            logger.warning("Notifier unavailable: %s", e)

    # ------------------------------------------------------------------ #
    #  Session Control                                                     #
    # ------------------------------------------------------------------ #

    def _toggle_session(self):
        if not self._session_active:
            self._start_session()
        else:
            self._stop_session()

    def _start_session(self):
        self._session_active = True
        self._distraction_count = 0
        self._session_seconds = 0
        self.session_id = start_session(self.user["user_id"])

        if self._scorer:
            self._scorer.reset()
        if self._kbd:
            self._kbd.start()
        if self._mouse:
            self._mouse.start()
        if self._screen:
            self._screen.start()

        # Start camera worker
        self._worker = DetectionWorker()
        self._worker.frame_ready.connect(self._update_camera)
        self._worker.status_update.connect(self._update_status)
        self._worker.distraction_detected.connect(self._on_distraction)
        self._worker.error.connect(self._on_camera_error)
        self._worker.start()

        self._session_clock.start()
        self._start_btn.setText("⏹  Stop Session")
        self._apply_btn_style(self._start_btn, "dangerBtn")

        if self._voice and prefs.voice_enabled():
            self._voice.custom("Focus session started. Good luck!")

        log_activity(self.user["user_id"], self.session_id, "SESSION_START")
        logger.info("Session %s started", self.session_id)

    def _stop_session(self):
        self._session_active = False
        self._session_clock.stop()

        if self._worker:
            worker = self._worker
            self._worker = None
            worker.stop()
            if worker.isRunning():
                # Never drop the last reference to a live QThread.
                self._retired_workers.append(worker)
            else:
                worker.deleteLater()

        if self._kbd:
            self._kbd.stop()
        if self._mouse:
            self._mouse.stop()
        if self._screen:
            self._screen.stop()

        score = self._scorer.session_average() if self._scorer else 0.0
        duration = end_session(self.session_id, self._distraction_count, score)
        if self.session_id:
            log_activity(self.user["user_id"], self.session_id, "SESSION_END",
                         f"score={score:.1f}, distractions={self._distraction_count}")

        # Persist today's report so Reports/Analytics stay up to date
        try:
            generate_daily_report(self.user["user_id"])
        except Exception as e:
            logger.warning("Daily report refresh failed: %s", e)

        # Refresh stat cards
        self._refresh_stats()

        self._cam_label.clear()
        self._cam_label.setText("Camera feed will appear here when session starts")
        self._start_btn.setText("▶  Start Focus Session")
        self._apply_btn_style(self._start_btn, "")

        if self._voice and prefs.voice_enabled() and duration:
            self._voice.custom(
                f"Session complete! You focused for {duration:.0f} minutes "
                f"with a score of {score:.0f}."
            )
        logger.info("Session ended. Duration=%.1f, Score=%.1f", duration, score)

    @staticmethod
    def _apply_btn_style(btn: QPushButton, object_name: str):
        """Change a stylesheet selector on a live widget (unpolish → polish)."""
        btn.setObjectName(object_name)
        style = btn.style()
        if style:
            style.unpolish(btn)
            style.polish(btn)
        btn.update()

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #

    def _tick_session(self):
        self._session_seconds += 1
        h, rem = divmod(self._session_seconds, 3600)
        m, s   = divmod(rem, 60)
        self._session_timer_lbl.setText(f"{h:02d}:{m:02d}:{s:02d}")

        # Update score every 5 s
        if self._session_seconds % 5 == 0 and self._scorer:
            kbd_rate   = self._kbd.get_keystroke_rate()   if self._kbd   else 0
            click_rate = self._mouse.get_click_rate()     if self._mouse else 0
            scr_score  = self._screen.get_change_score()  if self._screen else 0
            score = self._scorer.compute(
                self._face_present, kbd_rate, click_rate, scr_score
            )
            self._status_score[1].setText(f"{score:.0f} / 100")

    def _update_camera(self, qimg: QImage):
        pix = QPixmap.fromImage(qimg)
        self._cam_label.setPixmap(
            pix.scaled(self._cam_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    def _update_status(self, result: dict):
        present = result.get("is_present", False)
        distracted = result.get("is_distracted", False)
        drowsy = result.get("is_drowsy", False)
        face_count = result.get("face_count", 0)

        self._face_present = present

        if present:
            self._status_face[1].setText(
                f"✅ Yes ({face_count})" if face_count > 1 else "✅ Yes"
            )
        else:
            self._status_face[1].setText("❌ No")
        self._status_face[1].setStyleSheet(
            f"color: {SUCCESS if present else DANGER}; background: transparent; font-weight: 700;"
        )

        if distracted:
            attention = "Distracted ⚠️"
        elif drowsy:
            attention = "Drowsy 😴"
        else:
            attention = "Focused"
        self._status_focus[1].setText(attention)
        self._status_focus[1].setStyleSheet(
            f"color: {SUCCESS if attention == 'Focused' else DANGER}; "
            "background: transparent; font-weight: 700;"
        )
        self._status_dist[1].setText(str(self._distraction_count))

    def _on_camera_error(self, message: str):
        logger.error("Camera error: %s", message.replace("\n", " "))
        QMessageBox.critical(self, "Camera Error", message)
        if self._session_active:
            self._stop_session()

    def _on_distraction(self):
        self._distraction_count += 1
        if self._voice and prefs.voice_enabled():
            self._voice.remind_distraction()
        if self._notifier and prefs.notifications_enabled():
            self._notifier.send("Stay Focused!", "Distraction detected – get back to work!")
        if self.session_id:
            log_activity(self.user["user_id"], self.session_id, "DISTRACTION")
        self._status_dist[1].setText(str(self._distraction_count))

    def _on_break(self):
        if self._voice and prefs.voice_enabled():
            self._voice.remind_break()

    def _on_resume(self):
        if self._voice and prefs.voice_enabled():
            self._voice.remind_resume()

    def _on_prefs_saved(self):
        """Re-apply voice preferences that can change while running."""
        if self._voice:
            self._voice.set_rate(prefs.speech_rate())

    # ------------------------------------------------------------------ #
    #  Navigation                                                          #
    # ------------------------------------------------------------------ #

    def _open_analytics(self):
        from gui.analytics_window import AnalyticsWindow
        self._analytics_win = AnalyticsWindow(self.user)
        self._analytics_win.show()

    def _open_reports(self):
        from gui.reports_window import ReportsWindow
        self._reports_win = ReportsWindow(self.user)
        self._reports_win.show()

    def _open_settings(self):
        from gui.settings_window import SettingsWindow
        self._settings_win = SettingsWindow(self.user, on_saved=self._on_prefs_saved)
        self._settings_win.show()

    def _logout(self):
        if self._session_active:
            self._stop_session()
        self.close()
        self.logout_signal.emit()

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _refresh_stats(self):
        stats = get_session_stats(self.user["user_id"])
        self._card_sessions.update_value(str(stats.get("total_sessions", 0)))
        self._card_focus.update_value(f"{stats.get('total_minutes', 0)/60:.1f}", "hr")
        self._card_score.update_value(f"{stats.get('avg_score', 0):.0f}", "/100")
        self._card_distractions.update_value(str(stats.get("total_distractions", 0)))

    @staticmethod
    def _greeting() -> str:
        h = datetime.now().hour
        if h < 12:
            return "Good Morning ☀️"
        elif h < 17:
            return "Good Afternoon 🌤️"
        else:
            return "Good Evening 🌙"

    def _noop(self):
        pass

    def closeEvent(self, event):
        if self._session_active:
            self._stop_session()
        if self._worker:
            worker = self._worker
            self._worker = None
            worker.stop()
            if not worker.isRunning():
                worker.deleteLater()
            else:
                self._retired_workers.append(worker)
        super().closeEvent(event)
