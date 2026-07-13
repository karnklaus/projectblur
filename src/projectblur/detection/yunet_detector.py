"""OpenCV YuNet adapter for ProjectBlur's face-detection schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from .schema import Detection

DEFAULT_MODEL_RELATIVE_PATH = Path(
    "models/opencv/yunet/face_detection_yunet_2026may.onnx"
)


def default_model_path() -> Path:
    """Return the repository-local, git-ignored YuNet model path."""
    return Path(__file__).resolve().parents[3] / DEFAULT_MODEL_RELATIVE_PATH


class YuNetDetector:
    """Detect faces with OpenCV's ``FaceDetectorYN`` interface."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        confidence_threshold: float = 0.6,
        nms_threshold: float = 0.3,
        top_k: int = 5000,
    ) -> None:
        if isinstance(confidence_threshold, bool) or not isinstance(
            confidence_threshold, (int, float)
        ):
            raise TypeError("confidence_threshold must be a number between 0 and 1")
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        if isinstance(nms_threshold, bool) or not isinstance(nms_threshold, (int, float)):
            raise TypeError("nms_threshold must be a number between 0 and 1")
        if not 0 <= nms_threshold <= 1:
            raise ValueError("nms_threshold must be between 0 and 1")
        if isinstance(top_k, bool) or not isinstance(top_k, int):
            raise TypeError("top_k must be a positive integer")
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")

        self.model_path = Path(model_path) if model_path is not None else default_model_path()
        self.confidence_threshold = float(confidence_threshold)
        self.nms_threshold = float(nms_threshold)
        self.top_k = top_k
        self._detector: Any | None = None

    def detect(self, image: str | NDArray[Any]) -> list[Detection]:
        """Detect faces in an image path or OpenCV BGR array."""
        validated = self._validate_image(image)
        self._ensure_loaded(validated.shape[1], validated.shape[0])
        self._detector.setInputSize((validated.shape[1], validated.shape[0]))
        _, raw_faces = self._detector.detect(validated)
        if raw_faces is None:
            return []
        return _normalize_faces(
            np.asarray(raw_faces),
            image_shape=validated.shape[:2],
            confidence_threshold=self.confidence_threshold,
        )

    def _ensure_loaded(self, width: int, height: int) -> None:
        if self._detector is not None:
            return
        if not self.model_path.is_file():
            raise RuntimeError(
                "YuNet model is missing. Prepare the official OpenCV Zoo model at: "
                f"{self.model_path}"
            )
        if not hasattr(cv2, "FaceDetectorYN"):
            raise RuntimeError(
                "This OpenCV build does not provide FaceDetectorYN. Install the "
                "project's compatible OpenCV dependency."
            )
        try:
            self._detector = cv2.FaceDetectorYN.create(
                str(self.model_path),
                "",
                (width, height),
                self.confidence_threshold,
                self.nms_threshold,
                self.top_k,
            )
        except cv2.error as error:
            raise RuntimeError(
                f"Unable to load the YuNet model at: {self.model_path}"
            ) from error

    @staticmethod
    def _validate_image(image: str | NDArray[Any]) -> NDArray[Any]:
        if isinstance(image, str):
            path = Path(image)
            if not path.is_file():
                raise FileNotFoundError(f"Image file does not exist: {image}")
            decoded = cv2.imread(str(path), cv2.IMREAD_COLOR)
            if decoded is None or decoded.size == 0:
                raise ValueError(f"Unable to decode image: {image}")
            return decoded
        if isinstance(image, np.ndarray):
            if image.size == 0 or image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("NumPy image must be a non-empty HxWx3 BGR array")
            return image
        raise TypeError("image must be a file path string or NumPy array")


def _normalize_faces(
    raw_faces: NDArray[Any],
    *,
    image_shape: tuple[int, int],
    confidence_threshold: float,
) -> list[Detection]:
    """Map FaceDetectorYN rows into ProjectBlur detections."""
    if raw_faces.ndim != 2 or raw_faces.shape[1] < 15:
        raise RuntimeError("YuNet returned an unexpected detection schema")

    image_height, image_width = image_shape
    detections: list[Detection] = []
    for face in raw_faces:
        confidence = float(face[14])
        if confidence < confidence_threshold:
            continue

        x, y, width, height = (float(value) for value in face[:4])
        x1 = int(np.clip(x, 0, image_width - 1))
        y1 = int(np.clip(y, 0, image_height - 1))
        x2 = int(np.clip(x + width, 0, image_width))
        y2 = int(np.clip(y + height, 0, image_height))
        if x2 <= x1 or y2 <= y1:
            continue

        def point(index: int) -> list[float]:
            return [
                float(np.clip(face[index], 0, image_width - 1)),
                float(np.clip(face[index + 1], 0, image_height - 1)),
            ]

        detections.append(
            {
                "confidence": confidence,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "landmarks": {
                    "right_eye": point(4),
                    "left_eye": point(6),
                    "nose": point(8),
                    "mouth_right": point(10),
                    "mouth_left": point(12),
                },
            }
        )
    return detections
