"""
Voice Reminder
Text-to-speech reminders using pyttsx3 (offline, no API needed).
"""

import logging
import random
import threading

logger = logging.getLogger(__name__)

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not available – voice reminders disabled")

# ── reminder message pools ────────────────────────────────────────────── #

DISTRACTION_MESSAGES = [
    "Hey! Stay focused. You can do this!",
    "Get back on track — your goals are waiting!",
    "Distraction detected. Let's refocus now.",
    "Remember why you started. Keep going!",
    "Eyes on the screen. You're almost there!",
    "Don't let distractions steal your time.",
    "Refocus! Every minute counts.",
]

BREAK_MESSAGES = [
    "Great work! Take a short break — you've earned it.",
    "Break time! Stretch, hydrate, and recharge.",
    "You finished a Pomodoro. Rest for a few minutes.",
]

RESUME_MESSAGES = [
    "Break over. Let's get back to crushing it!",
    "Welcome back! Time to focus again.",
    "Ready? Let's hit those goals!",
]


class VoiceReminder:
    """Speaks reminders asynchronously using pyttsx3."""

    def __init__(self, rate: int = 175, volume: float = 0.9):
        self._rate   = rate
        self._volume = volume
        self._lock   = threading.Lock()
        self._engine = None
        self._thread: threading.Thread | None = None
        self._init_engine()

    # ------------------------------------------------------------------ #

    def _init_engine(self):
        if not TTS_AVAILABLE:
            return
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate",   self._rate)
            self._engine.setProperty("volume", self._volume)
            voices = self._engine.getProperty("voices")
            if voices:
                self._engine.setProperty("voice", voices[0].id)
        except Exception as e:
            logger.error("TTS engine init failed: %s", e)
            self._engine = None

    def set_rate(self, rate: int):
        """Update the speech rate (applies to the next utterance)."""
        self._rate = rate
        with self._lock:
            if self._engine:
                try:
                    self._engine.setProperty("rate", rate)
                except Exception as e:
                    logger.error("TTS rate update failed: %s", e)

    def speak(self, text: str):
        """Speak text in a background thread (non-blocking)."""
        if not TTS_AVAILABLE:
            logger.info("[TTS-DISABLED] %s", text)
            return
        t = threading.Thread(target=self._speak_sync, args=(text,), daemon=True)
        t.start()

    def _speak_sync(self, text: str):
        with self._lock:
            if not self._engine:
                self._init_engine()
                if not self._engine:
                    logger.info("[TTS-DISABLED] %s", text)
                    return
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                logger.error("TTS speak error: %s", e)
                # Engine is in an unknown state – drop it, next speak() re-inits
                self._engine = None

    # ------------------------------------------------------------------ #

    def remind_distraction(self):
        self.speak(random.choice(DISTRACTION_MESSAGES))

    def remind_break(self):
        self.speak(random.choice(BREAK_MESSAGES))

    def remind_resume(self):
        self.speak(random.choice(RESUME_MESSAGES))

    def custom(self, message: str):
        self.speak(message)
