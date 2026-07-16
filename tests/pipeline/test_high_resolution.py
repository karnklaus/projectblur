"""Tests for reduced-resolution detection on full-resolution frames."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

import numpy as np

from projectblur.pipeline import anonymize_high_resolution_frame


class HighResolutionFrameTests(unittest.TestCase):
    def test_maps_reduced_detections_to_full_resolution(self) -> None:
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        checker = np.indices((300, 600)).sum(axis=0) % 2
        frame[300:600, 600:1200] = np.repeat(
            (checker * 255).astype(np.uint8)[:, :, None],
            3,
            axis=2,
        )
        detector = Mock()
        detector.detect.return_value = [
            {
                "confidence": 0.9,
                "bbox": {"x1": 200, "y1": 100, "x2": 400, "y2": 200},
                "landmarks": {"nose": [300.0, 150.0]},
            }
        ]

        result = anonymize_high_resolution_frame(
            frame,
            detector,
            detection_max_edge=640,
            blur_strength=9,
            padding_ratio=0,
        )

        self.assertEqual((result.detection_width, result.detection_height), (640, 360))
        self.assertEqual(
            result.detections[0]["bbox"],
            {"x1": 600, "y1": 300, "x2": 1200, "y2": 600},
        )
        self.assertEqual(result.detections[0]["landmarks"]["nose"], [900.0, 450.0])
        self.assertEqual(detector.detect.call_args.args[0].shape, (360, 640, 3))
        np.testing.assert_array_equal(result.frame[:250], frame[:250])
        self.assertFalse(np.array_equal(result.frame[300:600, 600:1200], frame[300:600, 600:1200]))

    def test_does_not_upscale_small_frames(self) -> None:
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        detector = Mock()
        detector.detect.return_value = []

        result = anonymize_high_resolution_frame(frame, detector, detection_max_edge=640)

        self.assertEqual((result.detection_width, result.detection_height), (320, 240))
        self.assertIs(detector.detect.call_args.args[0], frame)
        np.testing.assert_array_equal(result.frame, frame)

    def test_rejects_invalid_detection_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            anonymize_high_resolution_frame(
                np.zeros((2, 2, 3), dtype=np.uint8),
                Mock(),
                detection_max_edge=0,
            )


if __name__ == "__main__":
    unittest.main()
