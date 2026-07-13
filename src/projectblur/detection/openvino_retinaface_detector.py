"""OpenVINO adapter for the Open Model Zoo RetinaFace ResNet50 model."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray

from .schema import Detection

MODEL_WIDTH = 640
MODEL_HEIGHT = 640
LANDMARK_NAMES = ("left_eye", "right_eye", "nose", "mouth_left", "mouth_right")
EXPECTED_OUTPUTS = {
    "face_rpn_bbox_pred",
    "face_rpn_cls_prob",
    "face_rpn_landmark_pred",
}
DEFAULT_MODEL_RELATIVE_PATH = Path(
    "models/openvino/ir/public/retinaface-resnet50-pytorch/FP16/"
    "retinaface-resnet50-pytorch.xml"
)


def default_model_path() -> Path:
    """Return the repository-local, git-ignored OpenVINO model path."""
    return Path(__file__).resolve().parents[3] / DEFAULT_MODEL_RELATIVE_PATH


class OpenVinoRetinaFaceDetector:
    """Detect faces with Open Model Zoo RetinaFace through OpenVINO Runtime."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.5,
        device: str = "AUTO",
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
        if not isinstance(device, str) or not device.strip():
            raise ValueError("device must be a non-empty OpenVINO device name")

        self.model_path = Path(model_path) if model_path is not None else default_model_path()
        self.confidence_threshold = float(confidence_threshold)
        self.nms_threshold = float(nms_threshold)
        self.device = device.strip().upper()
        self._compiled_model: Any | None = None
        self._input_name = ""
        self._output_ports: dict[str, Any] = {}

    def detect(self, image: str | NDArray[Any]) -> list[Detection]:
        """Detect faces in an image path or OpenCV BGR array."""
        validated = self._validate_image(image)
        self._ensure_loaded()
        tensor = _prepare_input(validated)
        raw_result = self._compiled_model({self._input_name: tensor})
        outputs = {
            name: np.asarray(raw_result[port]) for name, port in self._output_ports.items()
        }
        return _decode_outputs(
            outputs,
            original_shape=validated.shape[:2],
            confidence_threshold=self.confidence_threshold,
            nms_threshold=self.nms_threshold,
        )

    def _ensure_loaded(self) -> None:
        if self._compiled_model is not None:
            return
        if not self.model_path.is_file():
            raise RuntimeError(
                "OpenVINO RetinaFace model is missing. Prepare the official Open Model "
                f"Zoo model at: {self.model_path}"
            )
        try:
            import openvino as ov
        except ImportError as error:
            raise RuntimeError(
                "OpenVINO Runtime is unavailable. Install the project's OpenVINO dependency."
            ) from error

        core = ov.Core()
        model = core.read_model(str(self.model_path))
        if len(model.inputs) != 1:
            raise RuntimeError("OpenVINO RetinaFace model must have exactly one input")
        input_port = model.inputs[0]
        if list(input_port.shape) != [1, 3, MODEL_HEIGHT, MODEL_WIDTH]:
            raise RuntimeError(
                "OpenVINO RetinaFace model input must have shape [1, 3, 640, 640]"
            )
        output_ports = {port.any_name: port for port in model.outputs}
        if set(output_ports) != EXPECTED_OUTPUTS:
            raise RuntimeError(
                "OpenVINO RetinaFace output names do not match the verified model schema"
            )

        compiled = core.compile_model(
            model,
            self.device,
            {"PERFORMANCE_HINT": "LATENCY"},
        )
        self._compiled_model = compiled
        self._input_name = compiled.input(0).any_name
        self._output_ports = {
            name: compiled.output(name) for name in sorted(EXPECTED_OUTPUTS)
        }

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


def _prepare_input(image: NDArray[Any]) -> NDArray[np.float32]:
    resized = cv2.resize(image, (MODEL_WIDTH, MODEL_HEIGHT), interpolation=cv2.INTER_LINEAR)
    return np.transpose(resized.astype(np.float32), (2, 0, 1))[np.newaxis, ...]


@lru_cache(maxsize=1)
def _generate_priors() -> NDArray[np.float32]:
    min_sizes = ((16, 32), (64, 128), (256, 512))
    steps = (8, 16, 32)
    priors: list[list[float]] = []
    for sizes, step in zip(min_sizes, steps):
        feature_height = round(MODEL_HEIGHT / step)
        feature_width = round(MODEL_WIDTH / step)
        for row in range(feature_height):
            for column in range(feature_width):
                center_x = (column + 0.5) * step / MODEL_WIDTH
                center_y = (row + 0.5) * step / MODEL_HEIGHT
                for size in sizes:
                    priors.append(
                        [center_x, center_y, size / MODEL_WIDTH, size / MODEL_HEIGHT]
                    )
    return np.asarray(priors, dtype=np.float32)


def _decode_outputs(
    outputs: dict[str, NDArray[Any]],
    *,
    original_shape: tuple[int, int],
    confidence_threshold: float,
    nms_threshold: float,
) -> list[Detection]:
    if set(outputs) != EXPECTED_OUTPUTS:
        raise RuntimeError("OpenVINO RetinaFace inference returned an unexpected output schema")

    raw_boxes = np.asarray(outputs["face_rpn_bbox_pred"])[0]
    raw_scores = np.asarray(outputs["face_rpn_cls_prob"])[0]
    raw_landmarks = np.asarray(outputs["face_rpn_landmark_pred"])[0]
    priors = _generate_priors()
    if (
        raw_boxes.shape != (len(priors), 4)
        or raw_scores.shape != (len(priors), 2)
        or raw_landmarks.shape != (len(priors), 10)
    ):
        raise RuntimeError("OpenVINO RetinaFace output shapes do not match the verified schema")

    scores = raw_scores[:, 1]
    selected = np.flatnonzero(scores > confidence_threshold)
    if selected.size == 0:
        return []

    boxes = _decode_boxes(raw_boxes, priors)[selected]
    landmarks = _decode_landmarks(raw_landmarks, priors)[selected]
    selected_scores = scores[selected]
    keep = _nms(boxes, selected_scores, nms_threshold)

    original_height, original_width = original_shape
    pixel_scale = np.asarray(
        [original_width, original_height, original_width, original_height],
        dtype=np.float32,
    )
    boxes = boxes[keep] * pixel_scale
    landmarks = landmarks[keep]
    selected_scores = selected_scores[keep]

    detections: list[Detection] = []
    for box, points, score in zip(boxes, landmarks, selected_scores):
        x1 = int(np.clip(box[0], 0, original_width - 1))
        y1 = int(np.clip(box[1], 0, original_height - 1))
        x2 = int(np.clip(box[2], 0, original_width))
        y2 = int(np.clip(box[3], 0, original_height))
        if x2 <= x1 or y2 <= y1:
            continue
        normalized_landmarks: dict[str, list[float]] = {}
        for name, point in zip(LANDMARK_NAMES, points):
            normalized_landmarks[name] = [
                float(np.clip(point[0] * original_width, 0, original_width - 1)),
                float(np.clip(point[1] * original_height, 0, original_height - 1)),
            ]
        detections.append(
            {
                "confidence": float(score),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "landmarks": normalized_landmarks,
            }
        )
    return detections


def _decode_boxes(
    raw_boxes: NDArray[Any], priors: NDArray[np.float32]
) -> NDArray[np.float32]:
    centers = priors[:, :2] + raw_boxes[:, :2] * 0.1 * priors[:, 2:]
    sizes = priors[:, 2:] * np.exp(raw_boxes[:, 2:] * 0.2)
    return np.concatenate((centers - sizes / 2, centers + sizes / 2), axis=1)


def _decode_landmarks(
    raw_landmarks: NDArray[Any], priors: NDArray[np.float32]
) -> NDArray[np.float32]:
    deltas = raw_landmarks.reshape((-1, 5, 2))
    return priors[:, np.newaxis, :2] + deltas * 0.1 * priors[:, np.newaxis, 2:]


def _nms(
    boxes: NDArray[np.float32], scores: NDArray[Any], threshold: float
) -> NDArray[np.int64]:
    order = np.argsort(scores)[::-1]
    keep: list[int] = []
    while order.size:
        current = int(order[0])
        keep.append(current)
        if order.size == 1:
            break
        remaining = order[1:]
        x1 = np.maximum(boxes[current, 0], boxes[remaining, 0])
        y1 = np.maximum(boxes[current, 1], boxes[remaining, 1])
        x2 = np.minimum(boxes[current, 2], boxes[remaining, 2])
        y2 = np.minimum(boxes[current, 3], boxes[remaining, 3])
        intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        current_area = (boxes[current, 2] - boxes[current, 0]) * (
            boxes[current, 3] - boxes[current, 1]
        )
        remaining_area = (boxes[remaining, 2] - boxes[remaining, 0]) * (
            boxes[remaining, 3] - boxes[remaining, 1]
        )
        union = current_area + remaining_area - intersection
        overlap = np.divide(
            intersection,
            union,
            out=np.zeros_like(intersection),
            where=union > 0,
        )
        order = remaining[overlap <= threshold]
    return np.asarray(keep, dtype=np.int64)
