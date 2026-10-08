"""
Database Connection Module
Handles SQLite database initialization and connection management.
"""

import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apc_data.db")


def get_connection():
    """Return a new SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            email     TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            avatar    BLOB,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Focus sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            session_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER NOT NULL,
            start_time        DATETIME,
            end_time          DATETIME,
            duration_minutes  REAL    DEFAULT 0,
            distractions      INTEGER DEFAULT 0,
            productivity_score REAL   DEFAULT 0,
            notes             TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            report_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            report_date  DATE,
            focus_hours  REAL    DEFAULT 0,
            distractions INTEGER DEFAULT 0,
            score        REAL    DEFAULT 0,
            report_type  TEXT    DEFAULT 'daily',
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Activity log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            session_id  INTEGER,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type  TEXT,
            details     TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)


def execute_query(query: str, params: tuple = ()):
    """Execute a write query (INSERT, UPDATE, DELETE)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error("DB write error: %s", e)
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params: tuple = ()):
    """Fetch all rows for a SELECT query."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error("DB read error: %s", e)
        return []
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()):
    """Fetch a single row for a SELECT query."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error("DB read error: %s", e)
        return None
    finally:
        conn.close()
