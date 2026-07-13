"""Gaussian face anonymization for ProjectBlur detection results."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from projectblur.detection.schema import Detection

MIN_BLUR_STRENGTH = 3
MAX_BLUR_STRENGTH = 99
MAX_PADDING_RATIO = 0.5


def gaussian_blur_faces(
    image: NDArray[Any],
    detections: Iterable[Detection],
    *,
    blur_strength: int = 45,
    padding_ratio: float = 0.15,
) -> NDArray[Any]:
    """Return a copy of ``image`` with every detected face blurred.

    Bounding boxes are padded and clipped to the image. Invalid or empty boxes
    are skipped because a malformed detection must not corrupt other regions.
    """
    _validate_image(image)
    _validate_settings(blur_strength, padding_ratio)

    output = image.copy()
    image_height, image_width = output.shape[:2]

    for detection in detections:
        bbox = detection["bbox"]
        x1, y1 = int(bbox["x1"]), int(bbox["y1"])
        x2, y2 = int(bbox["x2"]), int(bbox["y2"])
        box_width, box_height = x2 - x1, y2 - y1
        if box_width <= 0 or box_height <= 0:
            continue

        padding = round(max(box_width, box_height) * padding_ratio)
        left = max(0, x1 - padding)
        top = max(0, y1 - padding)
        right = min(image_width, x2 + padding)
        bottom = min(image_height, y2 + padding)
        if left >= right or top >= bottom:
            continue

        region = output[top:bottom, left:right]
        kernel_size = _fit_kernel(blur_strength, region.shape[0], region.shape[1])
        if kernel_size is None:
            continue
        output[top:bottom, left:right] = cv2.GaussianBlur(
            region,
            (kernel_size, kernel_size),
            sigmaX=0,
        )

    return output


def _validate_image(image: NDArray[Any]) -> None:
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a NumPy array")
    if image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("image must be a non-empty HxWx3 BGR array")


def _validate_settings(blur_strength: int, padding_ratio: float) -> None:
    if isinstance(blur_strength, bool) or not isinstance(blur_strength, int):
        raise TypeError("blur_strength must be an odd integer")
    if not MIN_BLUR_STRENGTH <= blur_strength <= MAX_BLUR_STRENGTH:
        raise ValueError(
            f"blur_strength must be between {MIN_BLUR_STRENGTH} and "
            f"{MAX_BLUR_STRENGTH}"
        )
    if blur_strength % 2 == 0:
        raise ValueError("blur_strength must be odd")
    if isinstance(padding_ratio, bool) or not isinstance(padding_ratio, (int, float)):
        raise TypeError("padding_ratio must be a number")
    if not 0 <= padding_ratio <= MAX_PADDING_RATIO:
        raise ValueError(f"padding_ratio must be between 0 and {MAX_PADDING_RATIO}")


def _fit_kernel(requested: int, height: int, width: int) -> int | None:
    largest = min(requested, height, width)
    if largest % 2 == 0:
        largest -= 1
    return largest if largest >= MIN_BLUR_STRENGTH else None
