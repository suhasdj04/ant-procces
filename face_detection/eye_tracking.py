"""
Eye Tracking
Basic eye-detection using OpenCV to detect drowsiness / inattention.
"""

import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

EYE_CASCADE_PATH = os.path.join(cv2.data.haarcascades, "haarcascade_eye.xml")


class EyeTracker:
    """Detect eyes within a face ROI to infer attention level."""

    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)
        if self.eye_cascade.empty():
            logger.error("Failed to load eye cascade: %s", EYE_CASCADE_PATH)
        self._closed_count = 0
        self._drowsy_threshold = 10  # frames with eyes closed

    def detect_eyes(self, face_roi_gray: np.ndarray) -> list:
        """Return list of (x,y,w,h) for detected eyes in the face ROI."""
        eyes = self.eye_cascade.detectMultiScale(
            face_roi_gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(20, 20)
        )
        return list(eyes)

    def analyse_frame(self, frame: np.ndarray, faces: list) -> dict:
        """
        Given a BGR frame and face bounding boxes, detect eyes.
        Returns:
            eyes_detected  – bool
            is_drowsy      – bool
            annotated_frame
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        annotated = frame.copy()
        eyes_found = False

        for (fx, fy, fw, fh) in faces:
            roi_gray = gray[fy:fy + fh, fx:fx + fw]
            roi_col  = annotated[fy:fy + fh, fx:fx + fw]
            eyes = self.detect_eyes(roi_gray)
            if len(eyes) >= 1:
                eyes_found = True
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_col, (ex, ey), (ex + ew, ey + eh), (255, 180, 0), 1)

        if not eyes_found:
            self._closed_count += 1
        else:
            self._closed_count = 0

        is_drowsy = self._closed_count >= self._drowsy_threshold

        if is_drowsy:
            cv2.putText(annotated, "DROWSY!", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 60, 255), 2)

        return {
            "eyes_detected": eyes_found,
            "is_drowsy": is_drowsy,
            "annotated_frame": annotated,
        }

    def reset(self):
        self._closed_count = 0
