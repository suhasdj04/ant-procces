"""
Productivity Score Calculator
Combines face presence, keyboard/mouse activity, and screen change
into a single 0-100 productivity score.
"""

from collections import deque
from typing import ClassVar


class ProductivityScorer:
    """
    Weighted scoring model:
        Face presence    – 50 %
        Keyboard activity – 25 %
        Mouse activity    – 15 %
        Screen change     – 10 %
    """

    WEIGHTS: ClassVar[dict] = {
        "face":     0.50,
        "keyboard": 0.25,
        "mouse":    0.15,
        "screen":   0.10,
    }

    # Keyboard strokes/min considered "fully active"
    KBD_MAX_RATE: ClassVar[float] = 120.0
    # Mouse clicks/min considered "fully active"
    MOUSE_MAX_RATE: ClassVar[float] = 30.0
    # Mean pixel diff (0–1) that counts as "fully active" on screen:
    # any diff >= 0.2/255 saturates the screen component.
    SCREEN_SCORE_GAIN: ClassVar[float] = 5.0
    # Cap history so very long sessions can't grow it without bound
    # (5 s samples → ~5 hours of a single session).
    MAX_HISTORY: ClassVar[int] = 3600

    def __init__(self):
        self._history: deque = deque(maxlen=self.MAX_HISTORY)

    # ------------------------------------------------------------------ #

    def compute(
        self,
        is_face_present: bool,
        keystroke_rate: float,
        click_rate: float,
        screen_change_score: float,
    ) -> float:
        """
        Compute an instantaneous productivity score (0-100).
        """
        face_score = 100.0 if is_face_present else 0.0
        kbd_score  = min(keystroke_rate / self.KBD_MAX_RATE, 1.0) * 100.0
        mouse_score = min(click_rate / self.MOUSE_MAX_RATE, 1.0) * 100.0
        screen_score = min(screen_change_score * self.SCREEN_SCORE_GAIN, 1.0) * 100.0

        score = (
            face_score   * self.WEIGHTS["face"]     +
            kbd_score    * self.WEIGHTS["keyboard"]  +
            mouse_score  * self.WEIGHTS["mouse"]     +
            screen_score * self.WEIGHTS["screen"]
        )
        self._history.append(score)
        return round(score, 2)

    def session_average(self) -> float:
        if not self._history:
            return 0.0
        return round(sum(self._history) / len(self._history), 2)

    def reset(self):
        self._history.clear()

    # ------------------------------------------------------------------ #

    @staticmethod
    def grade(score: float) -> str:
        if score >= 85:
            return "Excellent 🔥"
        elif score >= 70:
            return "Good 👍"
        elif score >= 50:
            return "Average 😐"
        elif score >= 30:
            return "Low ⚠️"
        else:
            return "Very Low 🚨"
