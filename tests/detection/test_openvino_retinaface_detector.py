"""Unit tests for OpenVINO RetinaFace preprocessing and postprocessing."""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from projectblur.detection.openvino_retinaface_detector import (
    EXPECTED_OUTPUTS,
    OpenVinoRetinaFaceDetector,
    _decode_outputs,
    _generate_priors,
    _nms,
    _prepare_input,
)


class OpenVinoRetinaFaceDetectorTests(unittest.TestCase):
    def test_prepares_fixed_nchw_float_input(self) -> None:
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        tensor = _prepare_input(image)
        self.assertEqual(tensor.shape, (1, 3, 640, 640))
        self.assertEqual(tensor.dtype, np.float32)

    def test_generates_verified_prior_count(self) -> None:
        self.assertEqual(_generate_priors().shape, (16800, 4))

    def test_decodes_one_face_and_landmarks(self) -> None:
        count = len(_generate_priors())
        boxes = np.zeros((1, count, 4), dtype=np.float32)
        scores = np.zeros((1, count, 2), dtype=np.float32)
        landmarks = np.zeros((1, count, 10), dtype=np.float32)
        scores[0, 0, 1] = 0.95

        result = _decode_outputs(
            {
                "face_rpn_bbox_pred": boxes,
                "face_rpn_cls_prob": scores,
                "face_rpn_landmark_pred": landmarks,
            },
            original_shape=(640, 640),
            confidence_threshold=0.5,
            nms_threshold=0.5,
        )

        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["confidence"], 0.95, places=5)
        self.assertEqual(set(result[0]["landmarks"]), {
            "left_eye", "right_eye", "nose", "mouth_left", "mouth_right"
        })

    def test_returns_empty_list_below_threshold(self) -> None:
        count = len(_generate_priors())
        outputs = {
            "face_rpn_bbox_pred": np.zeros((1, count, 4), dtype=np.float32),
            "face_rpn_cls_prob": np.zeros((1, count, 2), dtype=np.float32),
            "face_rpn_landmark_pred": np.zeros((1, count, 10), dtype=np.float32),
        }
        self.assertEqual(
            _decode_outputs(
                outputs,
                original_shape=(100, 100),
                confidence_threshold=0.5,
                nms_threshold=0.5,
            ),
            [],
        )

    def test_rejects_unverified_output_schema(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "schema"):
            _decode_outputs(
                {name: np.zeros((1, 1)) for name in EXPECTED_OUTPUTS - {"face_rpn_bbox_pred"}},
                original_shape=(100, 100),
                confidence_threshold=0.5,
                nms_threshold=0.5,
            )

    def test_nms_suppresses_overlapping_lower_score(self) -> None:
        boxes = np.asarray([[0, 0, 1, 1], [0.05, 0.05, 1, 1]], dtype=np.float32)
        scores = np.asarray([0.9, 0.8], dtype=np.float32)
        self.assertEqual(_nms(boxes, scores, 0.5).tolist(), [0])

    def test_reports_missing_model_before_loading_runtime(self) -> None:
        detector = OpenVinoRetinaFaceDetector(Path("missing-model.xml"))
        with self.assertRaisesRegex(RuntimeError, "model is missing"):
            detector.detect(np.zeros((10, 10, 3), dtype=np.uint8))

    def test_validates_thresholds_and_device(self) -> None:
        with self.assertRaises(ValueError):
            OpenVinoRetinaFaceDetector(confidence_threshold=1.1)
        with self.assertRaises(ValueError):
            OpenVinoRetinaFaceDetector(nms_threshold=-0.1)
        with self.assertRaises(ValueError):
            OpenVinoRetinaFaceDetector(device="")


if __name__ == "__main__":
    unittest.main()
