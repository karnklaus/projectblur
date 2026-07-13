"""Offline tests for the web image-processing service."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

import cv2
import numpy as np

from projectblur.web.processing import MAX_UPLOAD_BYTES, anonymize_image_bytes, decode_image


class WebProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        checker = np.indices((40, 40)).sum(axis=0) % 2
        self.image = np.repeat((checker * 255).astype(np.uint8)[:, :, None], 3, axis=2)
        encoded, buffer = cv2.imencode(".png", self.image)
        self.assertTrue(encoded)
        self.content = buffer.tobytes()

    def test_processes_upload_with_mocked_detector(self) -> None:
        detector = Mock()
        detector.detect.return_value = [
            {
                "confidence": 0.99,
                "bbox": {"x1": 10, "y1": 10, "x2": 30, "y2": 30},
                "landmarks": {},
            }
        ]
        result = anonymize_image_bytes(
            self.content,
            detector,
            blur_strength=9,
            padding_ratio=0,
        )
        decoded = cv2.imdecode(np.frombuffer(result.content, np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual(result.faces_detected, 1)
        self.assertIsNotNone(decoded)
        self.assertGreaterEqual(result.timings.decode_seconds, 0)
        self.assertGreaterEqual(result.timings.detection_seconds, 0)
        self.assertGreaterEqual(result.timings.blur_seconds, 0)
        self.assertGreaterEqual(result.timings.encode_seconds, 0)
        self.assertGreaterEqual(result.timings.total_seconds, 0)
        detector.detect.assert_called_once()

    def test_rejects_non_image_content(self) -> None:
        with self.assertRaisesRegex(ValueError, "supported image"):
            decode_image(b"not an image")

    def test_rejects_empty_upload(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            decode_image(b"")

    def test_rejects_oversized_upload(self) -> None:
        with self.assertRaisesRegex(ValueError, "10 MB"):
            decode_image(b"0" * (MAX_UPLOAD_BYTES + 1))


if __name__ == "__main__":
    unittest.main()
