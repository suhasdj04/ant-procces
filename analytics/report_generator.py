"""
Report Generator
Builds daily/weekly report data and exports to PDF.
"""

import logging
import os
from datetime import date

from database import report_model
from database.db_connection import fetch_all

logger = logging.getLogger(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def generate_daily_report(user_id: int, for_date: date | None = None) -> dict:
    """Aggregate a day's sessions into a daily report dict and upsert to DB."""
    target = for_date or date.today()
    date_str = target.strftime("%Y-%m-%d")

    sessions = fetch_all(
        "SELECT * FROM focus_sessions WHERE user_id=? AND date(start_time)=?",
        (user_id, date_str)
    )

    total_minutes    = sum(s.get("duration_minutes", 0) for s in sessions)
    total_distractions = sum(s.get("distractions", 0) for s in sessions)
    avg_score        = (
        sum(s.get("productivity_score", 0) for s in sessions) / len(sessions)
        if sessions else 0.0
    )
    focus_hours = round(total_minutes / 60, 2)

    report_model.upsert_daily_report(
        user_id, date_str, focus_hours, total_distractions, round(avg_score, 2)
    )

    return {
        "date":         date_str,
        "sessions":     len(sessions),
        "focus_hours":  focus_hours,
        "distractions": total_distractions,
        "score":        round(avg_score, 2),
    }


def generate_weekly_report(user_id: int) -> dict:
    """Aggregate last 7 days of daily reports and persist a weekly row."""
    daily_reports = report_model.get_daily_reports(user_id, days=7)
    total_focus   = sum(r.get("focus_hours", 0) for r in daily_reports)
    total_dist    = sum(r.get("distractions", 0) for r in daily_reports)
    avg_score     = (
        sum(r.get("score", 0) for r in daily_reports) / len(daily_reports)
        if daily_reports else 0.0
    )
    week_ending = date.today().strftime("%Y-%m-%d")

    report_model.upsert_weekly_report(
        user_id, week_ending, round(total_focus, 2), total_dist, round(avg_score, 2)
    )

    return {
        "week_ending":   week_ending,
        "days":          len(daily_reports),
        "total_focus_hours": round(total_focus, 2),
        "total_distractions": total_dist,
        "avg_score":     round(avg_score, 2),
        "daily_breakdown": daily_reports,
    }


def export_report_pdf(report_data: dict, user_name: str, report_type: str = "daily"):
    """Export report to PDF using reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        sub_dir = "daily_reports" if report_type == "daily" else "weekly_reports"
        _ensure_dir(os.path.join(REPORTS_DIR, sub_dir))
        # Daily rows carry 'date'; weekly rows carry 'week_ending' so
        # reports from different weeks never overwrite each other.
        stamp = report_data.get("week_ending") or report_data.get("date") or date.today()
        filename = f"{report_type}_report_{stamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, sub_dir, filename)

        doc  = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Anti-Procrastination Coach – {report_type.title()} Report", styles["Title"]))
        story.append(Paragraph(f"User: {user_name}", styles["Normal"]))
        story.append(Spacer(1, 12))

        data = [["Metric", "Value"]]
        for k, v in report_data.items():
            if k != "daily_breakdown":
                data.append([k.replace("_", " ").title(), str(v)])

        t = Table(data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7C3AED")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(t)
        doc.build(story)
        logger.info("PDF exported: %s", filepath)
        return filepath
    except Exception as e:
        logger.error("PDF export failed: %s", e)
        return None
