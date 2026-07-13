"""ProjectBlur adapter for the external ``retina-face`` package."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from numpy.typing import NDArray

LOGGER = logging.getLogger(__name__)
LANDMARK_NAMES = ("right_eye", "left_eye", "nose", "mouth_right", "mouth_left")

try:
    from retinaface import RetinaFace as _RetinaFace
except ImportError:  # Keep this module importable so callers get a useful error.
    _RetinaFace = None


class BoundingBox(TypedDict):
    """Integer pixel coordinates for a detected face."""

    x1: int
    y1: int
    x2: int
    y2: int


class Detection(TypedDict):
    """Normalized ProjectBlur face detection."""

    confidence: float
    bbox: BoundingBox
    landmarks: dict[str, list[float]]


class RetinaFaceDetector:
    """Detect faces with RetinaFace and normalize its response."""

    def __init__(self, confidence_threshold: float = 0.9) -> None:
        """Create a detector filtering scores below ``confidence_threshold``."""
        if isinstance(confidence_threshold, bool) or not isinstance(
            confidence_threshold, (int, float)
        ):
            raise TypeError("confidence_threshold must be a number between 0 and 1")
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self.confidence_threshold = float(confidence_threshold)

    def detect(self, image: str | NDArray[Any]) -> list[Detection]:
        """Detect faces in an existing image path or non-empty OpenCV BGR image."""
        validated_image = self._validate_image(image)
        if _RetinaFace is None:
            raise RuntimeError(
                "RetinaFace is unavailable. Install the 'retina-face' dependency "
                "in the ProjectBlur virtual environment."
            )

        response = _RetinaFace.detect_faces(validated_image)
        if not isinstance(response, Mapping):
            LOGGER.warning("RetinaFace returned an unexpected response type")
            return []

        detections: list[Detection] = []
        for raw_detection in response.values():
            detection = self._normalize_detection(raw_detection)
            if detection is not None:
                detections.append(detection)
        return detections

    @staticmethod
    def _validate_image(image: str | NDArray[Any]) -> str | NDArray[Any]:
        if isinstance(image, str):
            if not Path(image).is_file():
                raise FileNotFoundError(f"Image file does not exist: {image}")
            return image
        if isinstance(image, np.ndarray):
            if image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("NumPy image must be a non-empty HxWx3 BGR array")
            return image
        raise TypeError("image must be a file path string or NumPy array")

    def _normalize_detection(self, raw: Any) -> Detection | None:
        if not isinstance(raw, Mapping):
            return None
        try:
            confidence = float(raw["score"])
            area = raw["facial_area"]
            if not self._is_coordinate_pair_sequence(area, length=4):
                return None
            if confidence < self.confidence_threshold:
                return None
            bbox: BoundingBox = {
                "x1": int(area[0]), "y1": int(area[1]),
                "x2": int(area[2]), "y2": int(area[3]),
            }
        except (KeyError, TypeError, ValueError, OverflowError):
            return None

        normalized_landmarks: dict[str, list[float]] = {}
        landmarks = raw.get("landmarks")
        if isinstance(landmarks, Mapping):
            for name in LANDMARK_NAMES:
                point = landmarks.get(name)
                if self._is_coordinate_pair_sequence(point, length=2):
                    try:
                        normalized_landmarks[name] = [float(point[0]), float(point[1])]
                    except (TypeError, ValueError, OverflowError):
                        continue
        return {"confidence": confidence, "bbox": bbox, "landmarks": normalized_landmarks}

    @staticmethod
    def _is_coordinate_pair_sequence(value: Any, *, length: int) -> bool:
        return (
            isinstance(value, Sequence)
            and not isinstance(value, (str, bytes))
            and len(value) == length
        )
