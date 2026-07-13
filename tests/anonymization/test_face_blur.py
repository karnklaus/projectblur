"""Unit tests for Gaussian face anonymization."""

from __future__ import annotations

import unittest

import numpy as np

from projectblur.anonymization import gaussian_blur_faces


class GaussianBlurFacesTests(unittest.TestCase):
    def setUp(self) -> None:
        checker = np.indices((40, 40)).sum(axis=0) % 2
        self.image = np.repeat((checker * 255).astype(np.uint8)[:, :, None], 3, axis=2)

    def test_blurs_only_the_detected_region(self) -> None:
        detections = [
            {
                "confidence": 0.99,
                "bbox": {"x1": 10, "y1": 10, "x2": 30, "y2": 30},
                "landmarks": {},
            }
        ]
        result = gaussian_blur_faces(
            self.image,
            detections,
            blur_strength=9,
            padding_ratio=0,
        )
        self.assertTrue(np.array_equal(result[:10], self.image[:10]))
        self.assertFalse(np.array_equal(result[10:30, 10:30], self.image[10:30, 10:30]))
        self.assertTrue(np.all(self.image[10:30, 10:30, 0] % 255 == 0))

    def test_clips_padding_to_image_bounds(self) -> None:
        detection = {
            "confidence": 0.99,
            "bbox": {"x1": 0, "y1": 0, "x2": 8, "y2": 8},
            "landmarks": {},
        }
        result = gaussian_blur_faces(
            self.image,
            [detection],
            blur_strength=7,
            padding_ratio=0.5,
        )
        self.assertEqual(result.shape, self.image.shape)
        self.assertFalse(np.array_equal(result[:8, :8], self.image[:8, :8]))

    def test_returns_copy_when_no_faces_are_detected(self) -> None:
        result = gaussian_blur_faces(self.image, [])
        self.assertTrue(np.array_equal(result, self.image))
        self.assertIsNot(result, self.image)

    def test_rejects_even_blur_strength(self) -> None:
        with self.assertRaisesRegex(ValueError, "odd"):
            gaussian_blur_faces(self.image, [], blur_strength=10)

    def test_rejects_invalid_padding(self) -> None:
        with self.assertRaises(ValueError):
            gaussian_blur_faces(self.image, [], padding_ratio=0.75)


if __name__ == "__main__":
    unittest.main()
