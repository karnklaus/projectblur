"""Offline unit tests for the OpenCV YuNet adapter."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import numpy as np

from projectblur.detection.yunet_detector import YuNetDetector, _normalize_faces


class YuNetDetectorTests(unittest.TestCase):
    def test_normalizes_box_landmarks_and_confidence(self) -> None:
        raw = np.asarray(
            [[10, 20, 30, 40, 15, 30, 30, 30, 22, 40, 17, 50, 28, 50, 0.95]],
            dtype=np.float32,
        )

        result = _normalize_faces(
            raw,
            image_shape=(100, 100),
            confidence_threshold=0.6,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0]["bbox"], {"x1": 10, "y1": 20, "x2": 40, "y2": 60}
        )
        self.assertAlmostEqual(result[0]["confidence"], 0.95, places=5)
        self.assertEqual(result[0]["landmarks"]["right_eye"], [15.0, 30.0])
        self.assertEqual(result[0]["landmarks"]["left_eye"], [30.0, 30.0])

    def test_filters_low_confidence_and_invalid_boxes(self) -> None:
        raw = np.asarray(
            [
                [10, 10, 20, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.5],
                [10, 10, -2, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.9],
            ],
            dtype=np.float32,
        )
        self.assertEqual(
            _normalize_faces(
                raw,
                image_shape=(100, 100),
                confidence_threshold=0.6,
            ),
            [],
        )

    def test_rejects_unexpected_output_schema(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "schema"):
            _normalize_faces(
                np.zeros((1, 14), dtype=np.float32),
                image_shape=(100, 100),
                confidence_threshold=0.6,
            )

    def test_detect_sets_exact_input_size_and_returns_empty(self) -> None:
        model_path = Path("models/yunet-test.onnx")
        backend = Mock()
        backend.detect.return_value = (1, None)
        with (
            patch.object(Path, "is_file", return_value=True),
            patch(
                "projectblur.detection.yunet_detector.cv2.FaceDetectorYN.create",
                return_value=backend,
            ) as create,
        ):
            detector = YuNetDetector(model_path)
            result = detector.detect(np.zeros((270, 480, 3), dtype=np.uint8))

        self.assertEqual(result, [])
        create.assert_called_once_with(str(model_path), "", (480, 270), 0.6, 0.3, 5000)
        backend.setInputSize.assert_called_once_with((480, 270))

    def test_reports_missing_model_before_backend_creation(self) -> None:
        detector = YuNetDetector(Path("missing-yunet.onnx"))
        with self.assertRaisesRegex(RuntimeError, "model is missing"):
            detector.detect(np.zeros((10, 10, 3), dtype=np.uint8))

    def test_validates_settings(self) -> None:
        with self.assertRaises(ValueError):
            YuNetDetector(confidence_threshold=1.1)
        with self.assertRaises(ValueError):
            YuNetDetector(nms_threshold=-0.1)
        with self.assertRaises(ValueError):
            YuNetDetector(top_k=0)
        with self.assertRaises(TypeError):
            YuNetDetector(top_k=True)


if __name__ == "__main__":
    unittest.main()
