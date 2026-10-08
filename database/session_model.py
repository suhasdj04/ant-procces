"""
Session Model
CRUD operations for focus_sessions and activity_log.
"""

import logging
from datetime import datetime

from database.db_connection import execute_query, fetch_all, fetch_one

logger = logging.getLogger(__name__)


def start_session(user_id: int) -> int:
    """Insert a new session row and return session_id."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sid = execute_query(
        "INSERT INTO focus_sessions (user_id, start_time) VALUES (?, ?)",
        (user_id, now)
    )
    logger.info("Session %s started for user %s", sid, user_id)
    return sid


def end_session(session_id: int, distractions: int, score: float):
    """Update a session row when it ends."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = fetch_one(
        "SELECT start_time FROM focus_sessions WHERE session_id = ?",
        (session_id,)
    )
    duration = 0.0
    if session and session.get("start_time"):
        try:
            start = datetime.strptime(session["start_time"], "%Y-%m-%d %H:%M:%S")
            duration = (datetime.now() - start).total_seconds() / 60
        except Exception as e:
            logger.debug("Could not parse start_time %r: %s",
                         session.get("start_time"), e)

    execute_query("""
        UPDATE focus_sessions
        SET end_time = ?, duration_minutes = ?, distractions = ?, productivity_score = ?
        WHERE session_id = ?
    """, (now, duration, distractions, score, session_id))
    logger.info("Session %s ended. Duration=%.1f min, Score=%.1f", session_id, duration, score)
    return duration


def get_user_sessions(user_id: int, limit: int = 50) -> list:
    return fetch_all(
        "SELECT * FROM focus_sessions WHERE user_id = ? ORDER BY start_time DESC LIMIT ?",
        (user_id, limit)
    )


def get_today_sessions(user_id: int) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    return fetch_all(
        "SELECT * FROM focus_sessions WHERE user_id = ? AND date(start_time) = ?",
        (user_id, today)
    )


def get_week_sessions(user_id: int) -> list:
    return fetch_all("""
        SELECT * FROM focus_sessions
        WHERE user_id = ?
          AND date(start_time) >= date('now', '-7 days')
        ORDER BY start_time DESC
    """, (user_id,))


def log_activity(user_id: int, session_id: int, event_type: str, details: str = ""):
    execute_query(
        "INSERT INTO activity_log (user_id, session_id, event_type, details) VALUES (?,?,?,?)",
        (user_id, session_id, event_type, details)
    )


def get_session_stats(user_id: int) -> dict:
    """Return aggregated stats for the user."""
    row = fetch_one("""
        SELECT
            COUNT(*)                    AS total_sessions,
            COALESCE(SUM(duration_minutes), 0)  AS total_minutes,
            COALESCE(AVG(productivity_score), 0) AS avg_score,
            COALESCE(SUM(distractions), 0)       AS total_distractions
        FROM focus_sessions
        WHERE user_id = ?
    """, (user_id,))
    return row or {}
