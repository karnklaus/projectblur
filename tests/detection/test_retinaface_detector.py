"""Unit tests for the RetinaFace adapter (no model or network required)."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import numpy as np

from projectblur.detection import RetinaFaceDetector
from projectblur.detection import retinaface_detector as module


class RetinaFaceDetectorTests(unittest.TestCase):
    def test_accepts_valid_threshold(self) -> None:
        self.assertEqual(RetinaFaceDetector(0.5).confidence_threshold, 0.5)

    def test_rejects_threshold_below_zero(self) -> None:
        with self.assertRaises(ValueError):
            RetinaFaceDetector(-0.1)

    def test_rejects_threshold_above_one(self) -> None:
        with self.assertRaises(ValueError):
            RetinaFaceDetector(1.1)

    def test_rejects_missing_path(self) -> None:
        with self.assertRaises(FileNotFoundError):
            RetinaFaceDetector().detect("missing-image.jpg")

    def test_rejects_invalid_arrays(self) -> None:
        detector = RetinaFaceDetector()
        for image in (np.array([]), np.zeros((10, 10)), np.zeros((10, 10, 4))):
            with self.subTest(shape=image.shape), self.assertRaises(ValueError):
                detector.detect(image)

    def test_normalizes_bbox_landmarks_and_filters_confidence(self) -> None:
        response = {
            "face_1": {
                "score": 0.99,
                "facial_area": [100, 80, 220, 240],
                "landmarks": {
                    "right_eye": [130, 120], "left_eye": [185, 119],
                    "nose": [160, 150], "mouth_right": [138, 190],
                    "mouth_left": [181, 190],
                },
            },
            "face_2": {"score": 0.2, "facial_area": [0, 0, 1, 1]},
        }
        backend = Mock()
        backend.detect_faces.return_value = response
        with patch.object(module, "_RetinaFace", backend):
            result = RetinaFaceDetector(0.9).detect(np.zeros((2, 2, 3)))
        self.assertEqual(result[0]["bbox"], {"x1": 100, "y1": 80, "x2": 220, "y2": 240})
        self.assertEqual(result[0]["landmarks"]["nose"], [160.0, 150.0])
        self.assertEqual(len(result), 1)

    def test_returns_empty_list_when_no_faces_are_found(self) -> None:
        backend = Mock()
        backend.detect_faces.return_value = {}
        with patch.object(module, "_RetinaFace", backend):
            self.assertEqual(RetinaFaceDetector().detect(np.zeros((1, 1, 3))), [])

    def test_skips_malformed_results_without_crashing(self) -> None:
        backend = Mock()
        backend.detect_faces.return_value = {
            "missing": {"score": 0.99},
            "partial": {"score": 0.99, "facial_area": [1, 2, 3, 4], "landmarks": {"nose": [2, 3]}},
        }
        with patch.object(module, "_RetinaFace", backend):
            result = RetinaFaceDetector().detect(np.zeros((1, 1, 3)))
        self.assertEqual(result, [{"confidence": 0.99, "bbox": {"x1": 1, "y1": 2, "x2": 3, "y2": 4}, "landmarks": {"nose": [2.0, 3.0]}}])

    def test_reports_missing_dependency(self) -> None:
        with (
            patch.object(module.Path, "is_file", return_value=True),
            patch.object(module, "_RetinaFace", None),
            self.assertRaisesRegex(RuntimeError, "retina-face"),
        ):
            RetinaFaceDetector().detect("image.jpg")


if __name__ == "__main__":
    unittest.main()
