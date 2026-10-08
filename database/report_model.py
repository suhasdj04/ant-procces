"""
Report Model
CRUD for the reports table and helpers for generating daily/weekly report data.
"""

import logging

from database.db_connection import execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


def _upsert_report(user_id: int, report_date: str, report_type: str,
                   focus_hours: float, distractions: int, score: float):
    existing = fetch_one(
        "SELECT report_id FROM reports WHERE user_id=? AND report_date=? AND report_type=?",
        (user_id, report_date, report_type)
    )
    if existing:
        execute_query("""
            UPDATE reports
            SET focus_hours=?, distractions=?, score=?
            WHERE report_id=?
        """, (focus_hours, distractions, score, existing["report_id"]))
    else:
        execute_query("""
            INSERT INTO reports (user_id, report_date, focus_hours, distractions, score, report_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, report_date, focus_hours, distractions, score, report_type))


def upsert_daily_report(user_id: int, report_date: str,
                        focus_hours: float, distractions: int, score: float):
    _upsert_report(user_id, report_date, "daily", focus_hours, distractions, score)


def upsert_weekly_report(user_id: int, report_date: str,
                         focus_hours: float, distractions: int, score: float):
    _upsert_report(user_id, report_date, "weekly", focus_hours, distractions, score)


def get_daily_reports(user_id: int, days: int = 7) -> list:
    return fetch_all("""
        SELECT * FROM reports
        WHERE user_id = ? AND report_type = 'daily'
          AND report_date >= date('now', ?)
        ORDER BY report_date ASC
    """, (user_id, f"-{days} days"))


def get_weekly_reports(user_id: int, weeks: int = 4) -> list:
    return fetch_all("""
        SELECT * FROM reports
        WHERE user_id = ? AND report_type = 'weekly'
          AND report_date >= date('now', ?)
        ORDER BY report_date ASC
    """, (user_id, f"-{weeks * 7} days"))


def get_report_by_date(user_id: int, date: str) -> dict | None:
    return fetch_one(
        "SELECT * FROM reports WHERE user_id=? AND report_date=? AND report_type='daily'",
        (user_id, date)
    )


def get_all_reports(user_id: int) -> list:
    return fetch_all(
        "SELECT * FROM reports WHERE user_id=? ORDER BY report_date DESC",
        (user_id,)
    )
