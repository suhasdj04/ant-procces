"""
Reports Window
Displays daily and weekly reports with table view and PDF export.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from analytics.productivity_score import ProductivityScorer
from analytics.report_generator import export_report_pdf, generate_daily_report, generate_weekly_report
from database.report_model import get_all_reports, get_daily_reports
from gui.styles import BG_CARD, BORDER, MAIN_STYLESHEET, TEXT_SEC

logger = logging.getLogger(__name__)


class ReportsWindow(QMainWindow):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle("APC – Reports")
        self.setMinimumSize(860, 600)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()

    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("📋  Reports")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        gen_daily_btn = QPushButton("📄 Generate Daily")
        gen_daily_btn.setFixedHeight(36)
        gen_daily_btn.setCursor(Qt.PointingHandCursor)
        gen_daily_btn.clicked.connect(self._generate_daily)
        header.addWidget(gen_daily_btn)

        gen_weekly_btn = QPushButton("📊 Generate Weekly")
        gen_weekly_btn.setFixedHeight(36)
        gen_weekly_btn.setObjectName("successBtn")
        gen_weekly_btn.setCursor(Qt.PointingHandCursor)
        gen_weekly_btn.clicked.connect(self._generate_weekly)
        header.addWidget(gen_weekly_btn)

        export_btn = QPushButton("⬇  Export PDF")
        export_btn.setFixedHeight(36)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_pdf)
        header.addWidget(export_btn)
        root.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_daily_tab(), "📅  Daily Reports")
        self.tabs.addTab(self._build_weekly_tab(), "📆  Weekly Summary")
        self.tabs.addTab(self._build_all_tab(), "🗂️  All Records")
        root.addWidget(self.tabs)

    # ------------------------------------------------------------------ #
    #  Tab builders                                                        #
    # ------------------------------------------------------------------ #

    def _build_daily_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        self._daily_table = self._make_table(
            ["Date", "Focus Hours", "Distractions", "Score", "Grade"]
        )
        lay.addWidget(self._daily_table)
        self._populate_daily()
        return w

    def _build_weekly_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)

        self._weekly_summary = QFrame()
        self._weekly_summary.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
        """)
        s_lay = QVBoxLayout(self._weekly_summary)
        s_lay.setContentsMargins(24, 20, 24, 20)
        self._weekly_lbl = QLabel("Click 'Generate Weekly' to compute the weekly summary.")
        self._weekly_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        self._weekly_lbl.setAlignment(Qt.AlignCenter)
        s_lay.addWidget(self._weekly_lbl)
        lay.addWidget(self._weekly_summary)
        lay.addStretch()
        return w

    def _build_all_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        self._all_table = self._make_table(
            ["Date", "Type", "Focus Hours", "Distractions", "Score"]
        )
        lay.addWidget(self._all_table)
        self._populate_all()
        return w

    # ------------------------------------------------------------------ #
    #  Table helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_table(headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        return t

    def _populate_daily(self):
        reports = get_daily_reports(self.user["user_id"], days=30)
        self._daily_table.setRowCount(len(reports))
        for row, r in enumerate(reports):
            score = r.get("score", 0)
            grade = ProductivityScorer.grade(score)
            items = [
                r.get("report_date", ""),
                f"{r.get('focus_hours', 0):.2f} hr",
                str(r.get("distractions", 0)),
                f"{score:.1f}",
                grade,
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                # colour score cell
                if col == 3:
                    if score >= 70:
                        colour = QColor("#10B981")
                    elif score >= 40:
                        colour = QColor("#F59E0B")
                    else:
                        colour = QColor("#EF4444")
                    item.setForeground(colour)
                self._daily_table.setItem(row, col, item)

    def _populate_all(self):
        reports = get_all_reports(self.user["user_id"])
        self._all_table.setRowCount(len(reports))
        for row, r in enumerate(reports):
            items = [
                r.get("report_date", ""),
                r.get("report_type", "daily").title(),
                f"{r.get('focus_hours', 0):.2f} hr",
                str(r.get("distractions", 0)),
                f"{r.get('score', 0):.1f}",
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                self._all_table.setItem(row, col, item)

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def _generate_daily(self):
        rpt = generate_daily_report(self.user["user_id"])
        self._populate_daily()
        QMessageBox.information(self, "Daily Report",
            f"Report for {rpt['date']} generated!\n"
            f"Focus: {rpt['focus_hours']:.2f} hr | Score: {rpt['score']:.1f} | "
            f"Distractions: {rpt['distractions']}")

    def _generate_weekly(self):
        rpt = generate_weekly_report(self.user["user_id"])
        text = (
            f"<b>Weekly Summary</b><br><br>"
            f"📅 Days tracked: <b>{rpt['days']}</b><br>"
            f"⏱️ Total focus: <b>{rpt['total_focus_hours']:.2f} hr</b><br>"
            f"⚠️ Total distractions: <b>{rpt['total_distractions']}</b><br>"
            f"⭐ Average score: <b>{rpt['avg_score']:.1f} / 100</b>"
        )
        self._weekly_lbl.setText(text)

    def _export_pdf(self):
        # Export whatever tab the user is looking at
        if self.tabs.currentIndex() == 1:
            rpt = generate_weekly_report(self.user["user_id"])
            path = export_report_pdf(rpt, self.user["name"], "weekly")
        else:
            rpt = generate_daily_report(self.user["user_id"])
            path = export_report_pdf(rpt, self.user["name"], "daily")
            self._populate_daily()

        if path:
            QMessageBox.information(self, "PDF Exported",
                                    f"Report saved to:\n{path}")
        else:
            QMessageBox.warning(self, "Export Failed",
                                "PDF export failed. Make sure reportlab is installed.")
