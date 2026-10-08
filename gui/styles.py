"""
Shared GUI Styles
Dark, premium APC theme applied across all windows.
"""

# ── Colour tokens ────────────────────────────────────────────────────────
PURPLE      = "#7C3AED"
PURPLE_DARK = "#5B21B6"
PURPLE_GLOW = "#A855F7"
VIOLET      = "#6D28D9"
TEAL        = "#14B8A6"
TEAL_DARK   = "#0D9488"
AMBER       = "#F59E0B"
ROSE        = "#F43F5E"
BG_DARK     = "#0F0F1A"
BG_SURFACE  = "#1A1A2E"
BG_CARD     = "#16213E"
BORDER      = "#2A2A4A"
TEXT_PRI    = "#E2E8F0"
TEXT_SEC    = "#94A3B8"
TEXT_MUTED  = "#64748B"
SUCCESS     = "#10B981"
WARNING     = "#F59E0B"
DANGER      = "#EF4444"

MAIN_STYLESHEET = f"""
/* ── Global ───────────────────────────────────────────────────────── */
* {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    color: {TEXT_PRI};
}}

QMainWindow, QDialog, QWidget {{
    background-color: {BG_DARK};
}}

/* ── Scroll bars ──────────────────────────────────────────────────── */
QScrollBar:vertical {{
    width: 8px;
    background: {BG_SURFACE};
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {PURPLE};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ── Push buttons ─────────────────────────────────────────────────── */
QPushButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {PURPLE}, stop:1 {VIOLET});
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {PURPLE_GLOW}, stop:1 {PURPLE});
}}
QPushButton:pressed {{
    background: {PURPLE_DARK};
}}
QPushButton:disabled {{
    background: {BG_SURFACE};
    color: {TEXT_MUTED};
}}

/* ── Danger button variant ────────────────────────────────────────── */
QPushButton#dangerBtn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {ROSE}, stop:1 #C2185B);
}}
QPushButton#dangerBtn:hover {{
    background: {ROSE};
}}

/* ── Success button variant ───────────────────────────────────────── */
QPushButton#successBtn {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {TEAL}, stop:1 {TEAL_DARK});
}}
QPushButton#successBtn:hover {{
    background: {TEAL};
}}

/* ── Line edits ───────────────────────────────────────────────────── */
QLineEdit {{
    background: {BG_SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: {TEXT_PRI};
    selection-background-color: {PURPLE};
}}
QLineEdit:focus {{
    border: 1.5px solid {PURPLE};
    background: {BG_CARD};
}}

/* ── Labels ───────────────────────────────────────────────────────── */
QLabel {{
    color: {TEXT_PRI};
    background: transparent;
}}
QLabel#title {{
    font-size: 26px;
    font-weight: 800;
    color: {PURPLE_GLOW};
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {TEXT_SEC};
}}
QLabel#sectionHeader {{
    font-size: 16px;
    font-weight: 700;
    color: {TEXT_PRI};
    padding: 4px 0;
}}

/* ── Tab widget ───────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    background: {BG_SURFACE};
    margin-top: -1px;
}}
QTabBar::tab {{
    background: {BG_SURFACE};
    color: {TEXT_SEC};
    padding: 10px 22px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    color: {PURPLE_GLOW};
    border-bottom: 2px solid {PURPLE_GLOW};
    background: {BG_CARD};
}}
QTabBar::tab:hover {{
    color: {TEXT_PRI};
    background: {BG_CARD};
}}

/* ── Frames / cards ───────────────────────────────────────────────── */
QFrame#card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}

/* ── Progress bar ─────────────────────────────────────────────────── */
QProgressBar {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    text-align: center;
    color: {TEXT_PRI};
    font-weight: 600;
    font-size: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {PURPLE}, stop:1 {TEAL});
    border-radius: 8px;
}}

/* ── Table widget ─────────────────────────────────────────────────── */
QTableWidget {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    gridline-color: {BORDER};
    font-size: 12px;
    alternate-background-color: {BG_CARD};
}}
QTableWidget::item:selected {{
    background: {PURPLE};
    color: white;
}}
QHeaderView::section {{
    background: {BG_CARD};
    color: {PURPLE_GLOW};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px;
    font-weight: 700;
    font-size: 12px;
}}

/* ── Combo box ────────────────────────────────────────────────────── */
QComboBox {{
    background: {BG_SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    color: {TEXT_PRI};
}}
QComboBox:focus {{ border: 1.5px solid {PURPLE}; }}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    selection-background-color: {PURPLE};
    color: {TEXT_PRI};
}}

/* ── Spin box ─────────────────────────────────────────────────────── */
QSpinBox {{
    background: {BG_SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    padding: 8px;
    color: {TEXT_PRI};
    font-size: 13px;
}}
QSpinBox:focus {{ border: 1.5px solid {PURPLE}; }}

/* ── Tool tips ────────────────────────────────────────────────────── */
QToolTip {{
    background: {BG_CARD};
    color: {TEXT_PRI};
    border: 1px solid {PURPLE};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
}}
"""
