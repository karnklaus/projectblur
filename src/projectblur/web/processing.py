"""In-memory image processing for the prototype web application."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

import cv2
import numpy as np

from projectblur.anonymization import gaussian_blur_faces
from projectblur.detection.schema import Detection

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class FaceDetector(Protocol):
    """Detector interface required by the web image processor."""

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Return normalized face detections for an OpenCV BGR image."""


@dataclass(frozen=True)
class ProcessingTimings:
    """Measured server-side processing stages in seconds."""

    decode_seconds: float
    detection_seconds: float
    blur_seconds: float
    encode_seconds: float
    total_seconds: float


@dataclass(frozen=True)
class ProcessedImage:
    """Encoded anonymized image and its detection count."""

    content: bytes
    faces_detected: int
    timings: ProcessingTimings


@dataclass(frozen=True)
class DetectionTimings:
    """Measured server stages for detection-only browser requests."""

    decode_seconds: float
    detection_seconds: float
    total_seconds: float


@dataclass(frozen=True)
class DetectedImage:
    """Detections and source dimensions for a decoded browser frame."""

    detections: list[Detection]
    width: int
    height: int
    timings: DetectionTimings


def detect_image_bytes(content: bytes, detector: FaceDetector) -> DetectedImage:
    """Decode a reduced browser frame and return detections without rendering."""
    total_started = perf_counter()
    stage_started = perf_counter()
    image = decode_image(content)
    decode_seconds = perf_counter() - stage_started

    stage_started = perf_counter()
    detections = detector.detect(image)
    detection_seconds = perf_counter() - stage_started
    height, width = image.shape[:2]
    return DetectedImage(
        detections=detections,
        width=width,
        height=height,
        timings=DetectionTimings(
            decode_seconds=decode_seconds,
            detection_seconds=detection_seconds,
            total_seconds=perf_counter() - total_started,
        ),
    )


def anonymize_image_bytes(
    content: bytes,
    detector: FaceDetector,
    *,
    blur_strength: int = 45,
    padding_ratio: float = 0.15,
) -> ProcessedImage:
    """Decode, detect, blur, and JPEG-encode an uploaded image in memory."""
    total_started = perf_counter()
    stage_started = perf_counter()
    image = decode_image(content)
    decode_seconds = perf_counter() - stage_started

    stage_started = perf_counter()
    detections = detector.detect(image)
    detection_seconds = perf_counter() - stage_started

    stage_started = perf_counter()
    blurred = gaussian_blur_faces(
        image,
        detections,
        blur_strength=blur_strength,
        padding_ratio=padding_ratio,
    )
    blur_seconds = perf_counter() - stage_started

    stage_started = perf_counter()
    encoded, buffer = cv2.imencode(".jpg", blurred, [cv2.IMWRITE_JPEG_QUALITY, 92])
    encode_seconds = perf_counter() - stage_started
    if not encoded:
        raise RuntimeError("Unable to encode the anonymized image")
    return ProcessedImage(
        content=buffer.tobytes(),
        faces_detected=len(detections),
        timings=ProcessingTimings(
            decode_seconds=decode_seconds,
            detection_seconds=detection_seconds,
            blur_seconds=blur_seconds,
            encode_seconds=encode_seconds,
            total_seconds=perf_counter() - total_started,
        ),
    )


def decode_image(content: bytes) -> np.ndarray:
    """Decode a bounded upload into an OpenCV BGR image."""
    if not content:
        raise ValueError("The uploaded image is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("The uploaded image exceeds the 10 MB limit")
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError("The uploaded file is not a supported image")
    return image
