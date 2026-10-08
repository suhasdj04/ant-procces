"""
Login / Registration Window
Premium dark-themed PyQt5 login screen with animated gradient header.
"""

import logging
import math
import time

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.user_model import authenticate_user, create_user, email_exists
from gui.styles import BG_CARD, BORDER, MAIN_STYLESHEET, ROSE, TEXT_SEC

logger = logging.getLogger(__name__)

# ── Failed-login throttling ───────────────────────────────────────────── #
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


class GradientHeader(QWidget):
    """Animated gradient banner at the top of the login card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(130)
        self._offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def _animate(self):
        self._offset = (self._offset + 1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        t = self._offset / 360.0
        r1 = int(80  + 40  * math.sin(2 * math.pi * t))
        g1 = int(30  + 20  * math.sin(2 * math.pi * t + 1))
        b1 = int(180 + 50  * math.cos(2 * math.pi * t))

        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0,   QColor(r1, g1, b1, 255))
        grad.setColorAt(0.5, QColor(20,  180, 160, 255))
        grad.setColorAt(1.0, QColor(60,  20,  140, 255))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 16, 16)

        # Title text
        painter.setPen(QColor(255, 255, 255, 240))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(0, 0, w, h - 18, Qt.AlignCenter, "Anti-Procrastination Coach")

        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(200, 220, 255, 180))
        painter.drawText(0, 30, w, h, Qt.AlignCenter, "Your AI-powered focus companion 🚀")


class LoginWindow(QWidget):
    """Login + Registration stacked widget."""

    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self._failed_attempts = 0
        self._lockout_until = 0.0
        self.setWindowTitle("APC – Login")
        self.setFixedSize(480, 620)
        self.setStyleSheet(MAIN_STYLESHEET)
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI Construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Center card
        outer = QHBoxLayout()
        outer.setContentsMargins(30, 30, 30, 30)
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 20px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 20)

        # Gradient header
        card_layout.addWidget(GradientHeader())

        # Stacked pages: login / register
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self.stack.addWidget(self._build_login_page())
        self.stack.addWidget(self._build_register_page())
        card_layout.addWidget(self.stack)

        outer.addWidget(card)
        root.addLayout(outer)

    # ------------------------------------------------------------------ #
    #  Login Page                                                          #
    # ------------------------------------------------------------------ #

    def _build_login_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(36, 24, 36, 10)
        lay.setSpacing(14)

        lbl = QLabel("Welcome Back")
        lbl.setFont(QFont("Segoe UI", 17, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        sub = QLabel("Sign in to track your focus sessions")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setStyleSheet(f"color: {TEXT_SEC};")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(10)

        self.login_email = self._input("📧  Email address")
        self.login_pass  = self._input("🔒  Password", password=True)
        lay.addWidget(QLabel("Email"))
        lay.addWidget(self.login_email)
        lay.addWidget(QLabel("Password"))
        lay.addWidget(self.login_pass)

        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"color: {ROSE}; font-size: 11px;")
        self.login_error.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.login_error)

        btn_login = QPushButton("Sign In  →")
        btn_login.setFixedHeight(44)
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.clicked.connect(self._do_login)
        lay.addWidget(btn_login)

        # Press Enter to login
        self.login_pass.returnPressed.connect(self._do_login)

        sep = QLabel("Don't have an account?")
        sep.setAlignment(Qt.AlignCenter)
        sep.setStyleSheet(f"color: {TEXT_SEC}; margin-top: 6px;")
        lay.addWidget(sep)

        btn_go_reg = QPushButton("Create Account")
        btn_go_reg.setFixedHeight(40)
        btn_go_reg.setObjectName("successBtn")
        btn_go_reg.setCursor(Qt.PointingHandCursor)
        btn_go_reg.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        lay.addWidget(btn_go_reg)

        return page

    # ------------------------------------------------------------------ #
    #  Register Page                                                       #
    # ------------------------------------------------------------------ #

    def _build_register_page(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(36, 18, 36, 10)
        lay.setSpacing(10)

        lbl = QLabel("Create Account")
        lbl.setFont(QFont("Segoe UI", 17, QFont.Bold))
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)

        self.reg_name  = self._input("👤  Full Name")
        self.reg_email = self._input("📧  Email address")
        self.reg_pass  = self._input("🔒  Password", password=True)
        self.reg_pass2 = self._input("🔒  Confirm Password", password=True)

        for lbl_text, widget in [
            ("Name",             self.reg_name),
            ("Email",            self.reg_email),
            ("Password",         self.reg_pass),
            ("Confirm Password", self.reg_pass2),
        ]:
            lay.addWidget(QLabel(lbl_text))
            lay.addWidget(widget)

        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet(f"color: {ROSE}; font-size: 11px;")
        self.reg_error.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.reg_error)

        btn_reg = QPushButton("Register  →")
        btn_reg.setFixedHeight(44)
        btn_reg.setCursor(Qt.PointingHandCursor)
        btn_reg.clicked.connect(self._do_register)
        lay.addWidget(btn_reg)

        btn_back = QPushButton("← Back to Sign In")
        btn_back.setFixedHeight(38)
        btn_back.setObjectName("successBtn")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lay.addWidget(btn_back)

        return page

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _input(placeholder: str, password: bool = False) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setFixedHeight(42)
        if password:
            w.setEchoMode(QLineEdit.Password)
        return w

    def _do_login(self):
        now = time.monotonic()
        if now < self._lockout_until:
            remaining = int(self._lockout_until - now) + 1
            self.login_error.setText(
                f"Too many failed attempts. Try again in {remaining}s."
            )
            return

        email = self.login_email.text().strip()
        pwd   = self.login_pass.text()
        if not email or not pwd:
            self.login_error.setText("Please fill in all fields.")
            return
        user = authenticate_user(email, pwd)
        if user:
            logger.info("Login success: %s", email)
            self._failed_attempts = 0
            self.on_login_success(user)
        else:
            self._failed_attempts += 1
            if self._failed_attempts >= MAX_FAILED_ATTEMPTS:
                self._failed_attempts = 0
                self._lockout_until = now + LOCKOUT_SECONDS
                self.login_error.setText(
                    f"Too many failed attempts. Locked for {LOCKOUT_SECONDS}s."
                )
            else:
                left = MAX_FAILED_ATTEMPTS - self._failed_attempts
                self.login_error.setText(
                    f"Invalid email or password. ({left} attempt{'s' if left != 1 else ''} left)"
                )
            logger.warning("Failed login attempt for %s", email)
            self._shake(self.login_email)
            self._shake(self.login_pass)

    def _do_register(self):
        name  = self.reg_name.text().strip()
        email = self.reg_email.text().strip()
        pwd   = self.reg_pass.text()
        pwd2  = self.reg_pass2.text()

        if not all([name, email, pwd, pwd2]):
            self.reg_error.setText("Please fill in all fields.")
            return
        if pwd != pwd2:
            self.reg_error.setText("Passwords do not match.")
            return
        if len(pwd) < 6:
            self.reg_error.setText("Password must be at least 6 characters.")
            return
        if email_exists(email):
            self.reg_error.setText("An account with this email already exists.")
            return

        uid = create_user(name, email, pwd)
        if uid > 0:
            QMessageBox.information(self, "Success",
                                    "Account created! Please sign in.")
            self.stack.setCurrentIndex(0)
            self.login_email.setText(email)
        else:
            self.reg_error.setText("Registration failed. Try again.")

    def _shake(self, widget: QWidget):
        """Quick horizontal shake animation for invalid inputs."""
        anim = QPropertyAnimation(widget, b"geometry")
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutSine)
        geo = widget.geometry()
        anim.setKeyValueAt(0,    geo)
        anim.setKeyValueAt(0.25, geo.adjusted(-8, 0, -8, 0))
        anim.setKeyValueAt(0.50, geo.adjusted(8, 0, 8, 0))
        anim.setKeyValueAt(0.75, geo.adjusted(-4, 0, -4, 0))
        anim.setKeyValueAt(1,    geo)
        anim.start()
        self._anim = anim   # keep reference
