"""ProjectBlur-owned face detection result schema."""

from __future__ import annotations

from typing import TypedDict


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
