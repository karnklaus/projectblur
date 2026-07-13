"""Face detection adapters with lazy backend imports."""

from __future__ import annotations

from typing import Any

from .schema import BoundingBox, Detection

__all__ = [
    "BoundingBox",
    "Detection",
    "OpenVinoRetinaFaceDetector",
    "RetinaFaceDetector",
    "YuNetDetector",
]


def __getattr__(name: str) -> Any:
    """Load only the selected inference backend and its heavy dependencies."""
    if name == "OpenVinoRetinaFaceDetector":
        from .openvino_retinaface_detector import OpenVinoRetinaFaceDetector

        return OpenVinoRetinaFaceDetector
    if name == "RetinaFaceDetector":
        from .retinaface_detector import RetinaFaceDetector

        return RetinaFaceDetector
    if name == "YuNetDetector":
        from .yunet_detector import YuNetDetector

        return YuNetDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
