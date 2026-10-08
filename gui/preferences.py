"""
User Preferences
QSettings-backed persistence for Pomodoro and voice/alert preferences.
Stored in an INI file at the project root so it stays easy to inspect.
"""

from pathlib import Path

from PyQt5.QtCore import QSettings

CONFIG_PATH = str(Path(__file__).resolve().parent.parent / "apc_settings.ini")

_DEFAULTS = {
    "pomodoro/work_minutes": 25,
    "pomodoro/break_minutes": 5,
    "pomodoro/long_break_minutes": 15,
    "voice/enabled": True,
    "voice/rate": 175,
    "notifications/enabled": True,
}


def _settings() -> QSettings:
    return QSettings(CONFIG_PATH, QSettings.IniFormat)


def get(key: str):
    s = _settings()
    default = _DEFAULTS[key]
    return s.value(key, default, type=type(default))


def set_value(key: str, value) -> None:
    s = _settings()
    s.setValue(key, value)
    s.sync()


# ── Convenience accessors ─────────────────────────────────────────────── #

def work_minutes() -> int:
    return get("pomodoro/work_minutes")


def break_minutes() -> int:
    return get("pomodoro/break_minutes")


def long_break_minutes() -> int:
    return get("pomodoro/long_break_minutes")


def voice_enabled() -> bool:
    return get("voice/enabled")


def notifications_enabled() -> bool:
    return get("notifications/enabled")


def speech_rate() -> int:
    return get("voice/rate")


# ── Batch writers ─────────────────────────────────────────────────────── #

def save_pomodoro(work: int, short_break: int, long_break: int) -> None:
    set_value("pomodoro/work_minutes", int(work))
    set_value("pomodoro/break_minutes", int(short_break))
    set_value("pomodoro/long_break_minutes", int(long_break))


def save_voice(enabled: bool, rate: int, notifications: bool) -> None:
    set_value("voice/enabled", bool(enabled))
    set_value("voice/rate", int(rate))
    set_value("notifications/enabled", bool(notifications))
