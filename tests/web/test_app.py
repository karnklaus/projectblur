"""Unit tests for the FastAPI prototype route without real inference."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np
from fastapi import HTTPException

from projectblur.detection import OpenVinoRetinaFaceDetector, YuNetDetector
from projectblur.web.app import blur_uploaded_image, get_detector, health, index


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        checker = np.indices((40, 40)).sum(axis=0) % 2
        image = np.repeat((checker * 255).astype(np.uint8)[:, :, None], 3, axis=2)
        encoded, buffer = cv2.imencode(".png", image)
        self.assertTrue(encoded)
        self.content = buffer.tobytes()

    @patch("projectblur.web.app.get_detector")
    def test_blur_route_returns_jpeg_and_face_count(self, get_detector: Mock) -> None:
        detector = Mock()
        detector.detect.return_value = [
            {
                "confidence": 0.99,
                "bbox": {"x1": 10, "y1": 10, "x2": 30, "y2": 30},
                "landmarks": {},
            }
        ]
        get_detector.return_value = detector

        response = blur_uploaded_image(self.content, 9, 0)

        self.assertEqual(response.media_type, "image/jpeg")
        self.assertEqual(response.headers["x-faces-detected"], "1")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("detect;dur=", response.headers["server-timing"])
        self.assertGreaterEqual(float(response.headers["x-detection-milliseconds"]), 0)
        self.assertGreaterEqual(float(response.headers["x-server-milliseconds"]), 0)
        self.assertGreater(len(response.body), 0)

    @patch("projectblur.web.app.get_detector", return_value=Mock())
    def test_blur_route_rejects_invalid_image(self, _get_detector: Mock) -> None:
        with self.assertRaises(HTTPException) as context:
            blur_uploaded_image(b"not an image", 45, 0.15)
        self.assertEqual(context.exception.status_code, 400)

    def test_index_exposes_upload_camera_and_screen_inputs(self) -> None:
        body = index().body.decode("utf-8")

        self.assertIn('type="file"', body)
        self.assertIn("navigator.mediaDevices.getUserMedia", body)
        self.assertIn("navigator.mediaDevices.getDisplayMedia", body)
        self.assertIn("/api/blur", body)
        self.assertIn("Stop source", body)
        self.assertIn("X-Detection-Milliseconds", body)

    def test_web_detector_uses_openvino_auto_by_default(self) -> None:
        get_detector.cache_clear()
        detector = get_detector()
        self.assertIsInstance(detector, OpenVinoRetinaFaceDetector)
        self.assertEqual(detector.device, "AUTO")
        get_detector.cache_clear()

    def test_health_reports_selected_backend_without_loading_model(self) -> None:
        self.assertEqual(
            health(),
            {
                "status": "ok",
                "detector": "retinaface-openvino",
                "device": "AUTO",
            },
        )

    def test_yunet_backend_is_explicit_and_uses_configured_model(self) -> None:
        get_detector.cache_clear()
        with (
            patch("projectblur.web.app.DETECTOR_BACKEND", "yunet"),
            patch("projectblur.web.app.YUNET_MODEL_PATH", "models/test-yunet.onnx"),
        ):
            detector = get_detector()
            self.assertIsInstance(detector, YuNetDetector)
            self.assertEqual(detector.model_path.as_posix(), "models/test-yunet.onnx")
            self.assertEqual(
                health(), {"status": "ok", "detector": "opencv-yunet"}
            )
        get_detector.cache_clear()


if __name__ == "__main__":
    unittest.main()
