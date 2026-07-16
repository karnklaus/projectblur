"""Detect on reduced frames while anonymizing the full-resolution source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import cv2
import numpy as np
from numpy.typing import NDArray

from projectblur.anonymization import gaussian_blur_faces
from projectblur.detection.schema import Detection


class FaceDetector(Protocol):
    """Detector contract required by the high-resolution frame processor."""

    def detect(self, image: NDArray[Any]) -> list[Detection]:
        """Return detections in the supplied image coordinate space."""


@dataclass(frozen=True)
class HighResolutionResult:
    """Full-resolution anonymized frame and its scaled detections."""

    frame: NDArray[Any]
    detections: list[Detection]
    detection_width: int
    detection_height: int


def anonymize_high_resolution_frame(
    frame: NDArray[Any],
    detector: FaceDetector,
    *,
    detection_max_edge: int = 640,
    blur_strength: int = 45,
    padding_ratio: float = 0.15,
) -> HighResolutionResult:
    """Detect on a reduced copy and blur matching regions on ``frame``.

    The detector never receives an upscaled image. Detection boxes and
    landmarks are mapped back into the original coordinate space before the
    anonymizer runs, so pixels outside anonymized regions retain their source
    resolution and are not JPEG re-encoded by this operation.
    """
    _validate_frame(frame)
    if isinstance(detection_max_edge, bool) or not isinstance(detection_max_edge, int):
        raise TypeError("detection_max_edge must be an integer")
    if detection_max_edge <= 0:
        raise ValueError("detection_max_edge must be greater than zero")

    source_height, source_width = frame.shape[:2]
    scale = min(1.0, detection_max_edge / max(source_width, source_height))
    detection_width = max(1, round(source_width * scale))
    detection_height = max(1, round(source_height * scale))
    detection_frame = (
        frame
        if (detection_width, detection_height) == (source_width, source_height)
        else cv2.resize(
            frame,
            (detection_width, detection_height),
            interpolation=cv2.INTER_AREA,
        )
    )

    reduced_detections = detector.detect(detection_frame)
    detections = _scale_detections(
        reduced_detections,
        source_width=source_width,
        source_height=source_height,
        detection_width=detection_width,
        detection_height=detection_height,
    )
    anonymized = gaussian_blur_faces(
        frame,
        detections,
        blur_strength=blur_strength,
        padding_ratio=padding_ratio,
    )
    return HighResolutionResult(
        frame=anonymized,
        detections=detections,
        detection_width=detection_width,
        detection_height=detection_height,
    )


def _scale_detections(
    detections: list[Detection],
    *,
    source_width: int,
    source_height: int,
    detection_width: int,
    detection_height: int,
) -> list[Detection]:
    scale_x = source_width / detection_width
    scale_y = source_height / detection_height
    scaled: list[Detection] = []
    for detection in detections:
        bbox = detection["bbox"]
        scaled.append(
            {
                "confidence": detection["confidence"],
                "bbox": {
                    "x1": _clip(round(bbox["x1"] * scale_x), source_width),
                    "y1": _clip(round(bbox["y1"] * scale_y), source_height),
                    "x2": _clip(round(bbox["x2"] * scale_x), source_width),
                    "y2": _clip(round(bbox["y2"] * scale_y), source_height),
                },
                "landmarks": {
                    name: [point[0] * scale_x, point[1] * scale_y]
                    for name, point in detection["landmarks"].items()
                },
            }
        )
    return scaled


def _clip(value: int, limit: int) -> int:
    return min(max(value, 0), limit)


def _validate_frame(frame: NDArray[Any]) -> None:
    if not isinstance(frame, np.ndarray):
        raise TypeError("frame must be a NumPy array")
    if frame.size == 0 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must be a non-empty HxWx3 BGR array")
