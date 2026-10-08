"""
User Model
CRUD operations for the users table.
"""

import logging

import bcrypt

from database.db_connection import execute_query, fetch_one

logger = logging.getLogger(__name__)


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its hash."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_user(name: str, email: str, password: str) -> int:
    """Create a new user. Returns user_id or -1 on failure."""
    try:
        hashed = hash_password(password)
        uid = execute_query(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed)
        )
        logger.info("Created user %s (id=%s)", email, uid)
        return uid
    except Exception as e:
        logger.error("create_user error: %s", e)
        return -1


def get_user_by_email(email: str) -> dict | None:
    """Fetch a user row by email."""
    return fetch_one("SELECT * FROM users WHERE email = ?", (email,))


def get_user_by_id(user_id: int) -> dict | None:
    """Fetch a user row by primary key."""
    return fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,))


def authenticate_user(email: str, password: str) -> dict | None:
    """Return user dict if credentials are valid, else None."""
    user = get_user_by_email(email)
    if user and verify_password(password, user["password"]):
        return user
    return None


def update_user_name(user_id: int, name: str):
    execute_query("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))


def update_user_password(user_id: int, new_password: str):
    hashed = hash_password(new_password)
    execute_query("UPDATE users SET password = ? WHERE user_id = ?", (hashed, user_id))


def email_exists(email: str) -> bool:
    row = fetch_one("SELECT user_id FROM users WHERE email = ?", (email,))
    return row is not None
