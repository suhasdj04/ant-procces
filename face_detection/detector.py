"""
Face Detector
Uses OpenCV Haar Cascades to detect faces and determine if user is present/focused.
"""

import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

CASCADE_DIR = cv2.data.haarcascades

FACE_CASCADE_PATH  = os.path.join(CASCADE_DIR, "haarcascade_frontalface_default.xml")
PROFILE_CASCADE_PATH = os.path.join(CASCADE_DIR, "haarcascade_profileface.xml")


class FaceDetector:
    """Detects faces in a frame and determines presence/focus state."""

    def __init__(self,
                 scale_factor: float = 1.1,
                 min_neighbors: int = 5,
                 min_size: tuple = (80, 80)):
        self.face_cascade    = cv2.CascadeClassifier(FACE_CASCADE_PATH)
        self.profile_cascade = cv2.CascadeClassifier(PROFILE_CASCADE_PATH)
        if self.face_cascade.empty():
            logger.error("Failed to load face cascade: %s", FACE_CASCADE_PATH)
        if self.profile_cascade.empty():
            logger.error("Failed to load profile cascade: %s", PROFILE_CASCADE_PATH)
        self.scale_factor  = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size      = min_size
        self._no_face_count = 0
        # ~1.5 s without a face (15 fps worker) → distraction
        self._distraction_threshold = 22

    def detect(self, frame: np.ndarray) -> dict:
        """
        Analyse a BGR frame.
        Returns a dict:
            faces       – list of (x,y,w,h) tuples
            face_count  – int
            is_present  – bool  (at least one face visible)
            is_distracted – bool
            annotated_frame – frame with drawn boxes
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size
        )

        if len(faces) == 0:
            profiles = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=self.min_size
            )
            face_list = list(profiles)
        else:
            face_list = list(faces)

        is_present = len(face_list) > 0

        if is_present:
            self._no_face_count = 0
        else:
            self._no_face_count += 1

        is_distracted = self._no_face_count >= self._distraction_threshold

        annotated = frame.copy()
        for (x, y, w, h) in face_list:
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 100), 2)
            cv2.putText(annotated, "Focused", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 100), 2)

        # Status overlay
        status_colour = (0, 220, 80) if is_present else (0, 80, 255)
        status_text   = "✓ Present" if is_present else "✗ Away"
        cv2.putText(annotated, status_text, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_colour, 2)

        if is_distracted:
            cv2.putText(annotated, "⚠ DISTRACTED – look at the screen", (10, 58),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 80, 255), 2)

        return {
            "faces": face_list,
            "face_count": len(face_list),
            "is_present": is_present,
            "is_distracted": is_distracted,
            "annotated_frame": annotated,
        }

    def reset(self):
        self._no_face_count = 0
