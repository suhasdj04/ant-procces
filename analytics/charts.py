"""
Charts
Matplotlib chart builders that return QPixmap-compatible images for embedding in PyQt5 widgets.
"""

import io
import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")        # Off-screen rendering – MUST be before pyplot import
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False
    logger.warning("matplotlib not available – charts disabled")

try:
    from PyQt5.QtGui import QImage, QPixmap
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

# ── Colour palette matching the dark APC theme ─────────────────────────── #
PALETTE = {
    "purple":    "#7C3AED",
    "violet":    "#A855F7",
    "teal":      "#14B8A6",
    "amber":     "#F59E0B",
    "rose":      "#F43F5E",
    "bg":        "#0F0F1A",
    "surface":   "#1A1A2E",
    "text":      "#E2E8F0",
    "grid":      "#2A2A3E",
}

def _apply_dark_theme(fig, ax):
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["surface"])
    ax.tick_params(colors=PALETTE["text"])
    ax.xaxis.label.set_color(PALETTE["text"])
    ax.yaxis.label.set_color(PALETTE["text"])
    ax.title.set_color(PALETTE["text"])
    ax.spines["bottom"].set_color(PALETTE["grid"])
    ax.spines["top"].set_color(PALETTE["grid"])
    ax.spines["left"].set_color(PALETTE["grid"])
    ax.spines["right"].set_color(PALETTE["grid"])
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(True, color=PALETTE["grid"], linestyle="--", alpha=0.6)


def _fig_to_pixmap(fig) -> "QPixmap | None":
    try:
        if not QT_AVAILABLE:
            return None
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
        buf.seek(0)
        img = QImage()
        img.loadFromData(buf.read())
        return QPixmap.fromImage(img)
    finally:
        # Always release the figure so refreshes can't leak matplotlib state
        plt.close(fig)


# ── Public chart builders ──────────────────────────────────────────────── #

def productivity_line_chart(sessions: list) -> "QPixmap | None":
    """Line chart of productivity score over recent sessions."""
    if not MPL_AVAILABLE or not sessions:
        return None

    scores = [s.get("productivity_score", 0) for s in sessions[-20:]]
    labels = [f"#{i+1}" for i in range(len(scores))]

    fig, ax = plt.subplots(figsize=(7, 3))
    _apply_dark_theme(fig, ax)

    ax.plot(labels, scores, color=PALETTE["violet"], linewidth=2.5, marker="o",
            markersize=5, markerfacecolor=PALETTE["teal"])
    ax.fill_between(labels, scores, alpha=0.15, color=PALETTE["violet"])
    ax.set_ylim(0, 100)
    ax.set_title("Productivity Score – Recent Sessions", pad=10)
    ax.set_xlabel("Session")
    ax.set_ylabel("Score")

    return _fig_to_pixmap(fig)


def focus_hours_bar_chart(daily_reports: list) -> "QPixmap | None":
    """Bar chart of focus hours per day."""
    if not MPL_AVAILABLE or not daily_reports:
        return None

    dates  = [r.get("report_date", "")[-5:] for r in daily_reports]  # MM-DD
    hours  = [r.get("focus_hours", 0) for r in daily_reports]

    fig, ax = plt.subplots(figsize=(7, 3))
    _apply_dark_theme(fig, ax)

    bars = ax.bar(dates, hours, color=PALETTE["purple"], width=0.6, edgecolor=PALETTE["violet"],
                  linewidth=0.8, zorder=3)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 0.05,
                f"{h:.1f}h", ha="center", va="bottom",
                fontsize=8, color=PALETTE["teal"])

    ax.set_title("Daily Focus Hours", pad=10)
    ax.set_xlabel("Date")
    ax.set_ylabel("Hours")

    return _fig_to_pixmap(fig)


def distraction_bar_chart(daily_reports: list) -> "QPixmap | None":
    """Bar chart of distractions per day."""
    if not MPL_AVAILABLE or not daily_reports:
        return None

    dates  = [r.get("report_date", "")[-5:] for r in daily_reports]
    dists  = [r.get("distractions", 0) for r in daily_reports]

    fig, ax = plt.subplots(figsize=(7, 3))
    _apply_dark_theme(fig, ax)

    bars = ax.bar(dates, dists, color=PALETTE["rose"], width=0.6,
                  edgecolor=PALETTE["amber"], linewidth=0.8, zorder=3)
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.2,
                    str(int(h)), ha="center", va="bottom",
                    fontsize=8, color=PALETTE["amber"])

    ax.set_title("Daily Distractions", pad=10)
    ax.set_xlabel("Date")
    ax.set_ylabel("Count")

    return _fig_to_pixmap(fig)


def score_gauge(score: float) -> "QPixmap | None":
    """Semi-circle gauge showing a single productivity score."""
    if not MPL_AVAILABLE:
        return None

    fig, ax = plt.subplots(figsize=(4, 2.5), subplot_kw={"aspect": "equal"})
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])
    ax.axis("off")

    # Background arc
    theta = np.linspace(np.pi, 0, 200)
    r = 0.8
    ax.plot(r * np.cos(theta), r * np.sin(theta),
            color=PALETTE["grid"], linewidth=18, solid_capstyle="round")

    # Fill arc
    fill_theta = np.linspace(np.pi, np.pi - (score / 100) * np.pi, 200)
    colour = (PALETTE["rose"] if score < 40 else
              PALETTE["amber"] if score < 70 else
              PALETTE["teal"])
    ax.plot(r * np.cos(fill_theta), r * np.sin(fill_theta),
            color=colour, linewidth=18, solid_capstyle="round")

    ax.text(0, -0.15, f"{score:.0f}", ha="center", va="center",
            fontsize=32, fontweight="bold", color=PALETTE["text"])
    ax.text(0, -0.4, "Productivity", ha="center", va="center",
            fontsize=9, color=PALETTE["text"])

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.6, 1.1)

    return _fig_to_pixmap(fig)
