"""
Analytics Window
Interactive charts: productivity trends, focus hours, distraction history, score gauge.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget

from analytics import charts
from database.report_model import get_daily_reports
from database.session_model import get_session_stats, get_user_sessions
from gui.styles import BG_CARD, BORDER, MAIN_STYLESHEET, PURPLE, TEAL, TEXT_SEC

logger = logging.getLogger(__name__)


class ChartCard(QFrame):
    """A card that displays a single QPixmap chart."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        self._title_lbl = QLabel(title)
        self._title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lay.addWidget(self._title_lbl)

        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignCenter)
        self._img_lbl.setMinimumHeight(200)
        self._img_lbl.setStyleSheet("background: transparent;")
        lay.addWidget(self._img_lbl)

        self._placeholder = QLabel("No data yet – start a focus session!")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        lay.addWidget(self._placeholder)

    def set_pixmap(self, pix: QPixmap | None):
        if pix:
            self._img_lbl.setPixmap(
                pix.scaled(self._img_lbl.size().expandedTo(pix.size()),
                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self._placeholder.hide()
            self._img_lbl.show()
        else:
            self._img_lbl.hide()
            self._placeholder.show()


class AnalyticsWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("APC – Analytics")
        self.setMinimumSize(950, 700)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()
        self._load_charts()

    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊  Productivity Analytics")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setFixedHeight(36)
        refresh_btn.setFixedWidth(110)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_charts)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Summary strip
        root.addWidget(self._build_summary_strip())

        # Scroll area for charts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_lay = QVBoxLayout(inner)
        inner_lay.setSpacing(16)
        inner_lay.setContentsMargins(0, 0, 0, 0)

        # Row 1: gauge + productivity line
        row1 = QHBoxLayout()
        self._gauge_card = ChartCard("🎯  Session Score Gauge")
        self._gauge_card.setFixedWidth(300)
        self._score_card = ChartCard("📈  Productivity Score Trend")
        row1.addWidget(self._gauge_card)
        row1.addWidget(self._score_card)
        inner_lay.addLayout(row1)

        # Row 2: focus hours bar
        self._focus_card = ChartCard("⏱️  Daily Focus Hours (Last 7 Days)")
        inner_lay.addWidget(self._focus_card)

        # Row 3: distractions
        self._dist_card = ChartCard("⚠️  Daily Distractions (Last 7 Days)")
        inner_lay.addWidget(self._dist_card)

        inner_lay.addStretch()
        scroll.setWidget(inner)
        root.addWidget(scroll)

    def _build_summary_strip(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        stats = get_session_stats(self.user["user_id"])
        items = [
            ("Total Sessions",  str(stats.get("total_sessions", 0)),         "📅", PURPLE),
            ("Hours Focused",   f"{stats.get('total_minutes', 0)/60:.1f} hr","⏱️", TEAL),
            ("Avg Score",       f"{stats.get('avg_score', 0):.1f} / 100",    "⭐", "#F59E0B"),
            ("Distractions",    str(stats.get("total_distractions", 0)),      "⚠️", "#F43F5E"),
        ]
        for label, value, icon, colour in items:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {BG_CARD};
                    border: 1px solid {colour}44;
                    border-radius: 12px;
                    padding: 6px;
                }}
            """)
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(14, 10, 14, 10)
            icon_lbl = QLabel(f"{icon}  {label}")
            icon_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px;")
            val_lbl = QLabel(value)
            val_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
            val_lbl.setStyleSheet(f"color: {colour};")
            c_lay.addWidget(icon_lbl)
            c_lay.addWidget(val_lbl)
            lay.addWidget(card)
        return w

    # ------------------------------------------------------------------ #

    def _load_charts(self):
        sessions = get_user_sessions(self.user["user_id"], limit=30)
        daily    = get_daily_reports(self.user["user_id"], days=7)
        stats    = get_session_stats(self.user["user_id"])

        avg_score = stats.get("avg_score", 0)
        self._gauge_card.set_pixmap(charts.score_gauge(avg_score))
        self._score_card.set_pixmap(charts.productivity_line_chart(sessions))
        self._focus_card.set_pixmap(charts.focus_hours_bar_chart(daily))
        self._dist_card.set_pixmap(charts.distraction_bar_chart(daily))
