"""
Settings Window
User preferences: profile, password, Pomodoro durations, voice toggle.
"""

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from database.user_model import get_user_by_id, update_user_name, update_user_password, verify_password
from gui import preferences as prefs
from gui.styles import BORDER, MAIN_STYLESHEET, TEAL, TEXT_SEC

logger = logging.getLogger(__name__)


class SettingsWindow(QMainWindow):
    def __init__(self, user: dict, on_saved=None):
        super().__init__()
        self.user = user
        self._on_saved = on_saved
        self.setWindowTitle("APC – Settings")
        self.setFixedSize(620, 540)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()

    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("⚙️  Settings")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_profile_tab(), "👤  Profile")
        tabs.addTab(self._build_pomodoro_tab(), "🍅  Pomodoro")
        tabs.addTab(self._build_voice_tab(), "🔊  Voice & Alerts")
        tabs.addTab(self._build_about_tab(), "ℹ️  About")
        root.addWidget(tabs)

    # ------------------------------------------------------------------ #
    #  Profile Tab                                                         #
    # ------------------------------------------------------------------ #

    def _build_profile_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self._name_edit = QLineEdit(self.user.get("name", ""))
        self._name_edit.setFixedHeight(40)
        self._email_edit = QLineEdit(self.user.get("email", ""))
        self._email_edit.setReadOnly(True)
        self._email_edit.setStyleSheet(f"color: {TEXT_SEC};")
        form.addRow("Full Name:", self._name_edit)
        form.addRow("Email:", self._email_edit)
        lay.addLayout(form)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        lay.addWidget(sep)

        pwd_lbl = QLabel("Change Password")
        pwd_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lay.addWidget(pwd_lbl)

        pwd_form = QFormLayout()
        pwd_form.setSpacing(12)
        self._cur_pwd = QLineEdit()
        self._cur_pwd.setEchoMode(QLineEdit.Password)
        self._cur_pwd.setPlaceholderText("Current password")
        self._cur_pwd.setFixedHeight(40)
        self._new_pwd = QLineEdit()
        self._new_pwd.setEchoMode(QLineEdit.Password)
        self._new_pwd.setPlaceholderText("New password")
        self._new_pwd.setFixedHeight(40)
        pwd_form.addRow("Current:", self._cur_pwd)
        pwd_form.addRow("New:", self._new_pwd)
        lay.addLayout(pwd_form)

        self._profile_msg = QLabel("")
        self._profile_msg.setStyleSheet(f"color: {TEAL}; font-size: 11px;")
        lay.addWidget(self._profile_msg)

        save_btn = QPushButton("💾  Save Changes")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_profile)
        lay.addWidget(save_btn)
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ #
    #  Pomodoro Tab                                                        #
    # ------------------------------------------------------------------ #

    def _build_pomodoro_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        note = QLabel("Pomodoro settings take effect the next time you open the Dashboard.")
        note.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px;")
        note.setWordWrap(True)
        lay.addWidget(note)

        form = QFormLayout()
        form.setSpacing(14)

        self._work_spin = QSpinBox()
        self._work_spin.setRange(5, 90)
        self._work_spin.setValue(prefs.work_minutes())
        self._work_spin.setSuffix(" min")
        self._work_spin.setFixedHeight(40)

        self._break_spin = QSpinBox()
        self._break_spin.setRange(1, 30)
        self._break_spin.setValue(prefs.break_minutes())
        self._break_spin.setSuffix(" min")
        self._break_spin.setFixedHeight(40)

        self._long_break_spin = QSpinBox()
        self._long_break_spin.setRange(10, 60)
        self._long_break_spin.setValue(prefs.long_break_minutes())
        self._long_break_spin.setSuffix(" min")
        self._long_break_spin.setFixedHeight(40)

        form.addRow("Work duration:", self._work_spin)
        form.addRow("Short break:", self._break_spin)
        form.addRow("Long break:", self._long_break_spin)
        lay.addLayout(form)

        save_btn = QPushButton("💾  Save Pomodoro Settings")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_pomodoro)
        lay.addWidget(save_btn)
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ #
    #  Voice Tab                                                           #
    # ------------------------------------------------------------------ #

    def _build_voice_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(14)

        self._voice_chk = QCheckBox("Enable voice reminders")
        self._voice_chk.setChecked(prefs.voice_enabled())
        self._notif_chk = QCheckBox("Enable desktop notifications")
        self._notif_chk.setChecked(prefs.notifications_enabled())

        self._voice_rate = QSpinBox()
        self._voice_rate.setRange(100, 250)
        self._voice_rate.setValue(prefs.speech_rate())
        self._voice_rate.setSuffix(" wpm")
        self._voice_rate.setFixedHeight(40)

        form.addRow("Voice reminders:", self._voice_chk)
        form.addRow("Notifications:", self._notif_chk)
        form.addRow("Speech rate:", self._voice_rate)
        lay.addLayout(form)

        test_btn = QPushButton("🔊  Test Voice")
        test_btn.setFixedHeight(40)
        test_btn.setObjectName("successBtn")
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(self._test_voice)
        lay.addWidget(test_btn)

        save_btn = QPushButton("💾  Save Voice Settings")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_voice)
        lay.addWidget(save_btn)
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ #
    #  About Tab                                                           #
    # ------------------------------------------------------------------ #

    def _build_about_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(10)

        logo = QLabel("🎯")
        logo.setFont(QFont("Segoe UI Emoji", 48))
        logo.setAlignment(Qt.AlignCenter)
        lay.addWidget(logo)

        name = QLabel("Anti-Procrastination Coach")
        name.setFont(QFont("Segoe UI", 18, QFont.Bold))
        name.setAlignment(Qt.AlignCenter)
        lay.addWidget(name)

        version = QLabel("Version 1.0.0")
        version.setStyleSheet(f"color: {TEXT_SEC};")
        version.setAlignment(Qt.AlignCenter)
        lay.addWidget(version)

        desc = QLabel(
            "APC helps you stay focused using face detection, activity monitoring,\n"
            "Pomodoro timers, voice reminders, and detailed productivity analytics.\n\n"
            "Built with Python • PyQt5 • OpenCV • SQLite"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        lay.addWidget(desc)
        lay.addStretch()
        return w

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    def _save_profile(self):
        new_name = self._name_edit.text().strip()
        cur_pwd  = self._cur_pwd.text()
        new_pwd  = self._new_pwd.text()

        if new_name and new_name != self.user.get("name"):
            update_user_name(self.user["user_id"], new_name)
            self.user["name"] = new_name
            self._profile_msg.setText("✅ Name updated.")

        if cur_pwd or new_pwd:
            if not verify_password(cur_pwd, self.user.get("password", "")):
                self._profile_msg.setText("❌ Current password incorrect.")
                return
            if len(new_pwd) < 6:
                self._profile_msg.setText("❌ New password too short (min 6 chars).")
                return
            update_user_password(self.user["user_id"], new_pwd)
            # update cached hash
            updated = get_user_by_id(self.user["user_id"])
            if updated:
                self.user["password"] = updated["password"]
            self._profile_msg.setText("✅ Password changed successfully.")

    def _save_pomodoro(self):
        prefs.save_pomodoro(
            self._work_spin.value(),
            self._break_spin.value(),
            self._long_break_spin.value(),
        )
        logger.info("Pomodoro settings saved: work=%d, break=%d, long=%d",
                    self._work_spin.value(), self._break_spin.value(),
                    self._long_break_spin.value())
        QMessageBox.information(
            self, "Saved",
            "Pomodoro settings saved!\nThey apply the next time you open the Dashboard."
        )

    def _save_voice(self):
        prefs.save_voice(
            self._voice_chk.isChecked(),
            self._voice_rate.value(),
            self._notif_chk.isChecked(),
        )
        logger.info("Voice settings saved: enabled=%s, rate=%d, notifications=%s",
                    self._voice_chk.isChecked(), self._voice_rate.value(),
                    self._notif_chk.isChecked())
        if self._on_saved:
            self._on_saved()
        QMessageBox.information(self, "Saved", "Voice settings saved!")

    def _test_voice(self):
        try:
            from reminders.voice_reminder import VoiceReminder
            vr = VoiceReminder(rate=self._voice_rate.value())
            vr.custom("Anti-Procrastination Coach is ready to keep you focused!")
        except Exception as e:
            QMessageBox.warning(self, "Voice Error", f"Voice test failed:\n{e}")
