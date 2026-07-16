"""Tests for the versioned shared-memory latest-frame transport."""

from __future__ import annotations

import unittest

import numpy as np

from projectblur.pipeline import FramePublisher, FrameSubscriber


class FrameBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.publisher = FramePublisher(max_width=8, max_height=6)

    def tearDown(self) -> None:
        self.publisher.close()
        self.publisher.unlink()

    def test_returns_none_before_first_frame(self) -> None:
        with FrameSubscriber(self.publisher.name) as subscriber:
            self.assertIsNone(subscriber.read_latest())

    def test_publishes_stable_bgra_copy(self) -> None:
        frame = np.arange(4 * 3 * 4, dtype=np.uint8).reshape(3, 4, 4)

        sequence = self.publisher.publish(frame, timestamp_ns=1234)

        with FrameSubscriber(self.publisher.name) as subscriber:
            published = subscriber.read_latest()
        self.assertIsNotNone(published)
        assert published is not None
        self.assertEqual(sequence, 2)
        self.assertEqual(published.sequence, 2)
        self.assertEqual(published.timestamp_ns, 1234)
        np.testing.assert_array_equal(published.pixels, frame)

    def test_rejects_frames_larger_than_capacity(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.publisher.publish(np.zeros((7, 8, 4), dtype=np.uint8))

    def test_rejects_non_bgra_frame(self) -> None:
        with self.assertRaisesRegex(ValueError, "HxWx4"):
            self.publisher.publish(np.zeros((3, 4, 3), dtype=np.uint8))

    def test_publisher_can_open_mapping_created_by_another_owner(self) -> None:
        frame = np.full((3, 4, 4), 77, dtype=np.uint8)

        with FramePublisher(
            max_width=8,
            max_height=6,
            name=self.publisher.name,
            create=False,
        ) as attached:
            self.assertEqual(attached.publish(frame), 2)
            with self.assertRaisesRegex(RuntimeError, "another owner"):
                attached.unlink()

        with FrameSubscriber(self.publisher.name) as subscriber:
            published = subscriber.read_latest()
        self.assertIsNotNone(published)
        assert published is not None
        np.testing.assert_array_equal(published.pixels, frame)

    def test_existing_mapping_requires_a_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "name is required"):
            FramePublisher(max_width=8, max_height=6, create=False)

    def test_existing_mapping_must_have_requested_capacity(self) -> None:
        with self.assertRaisesRegex(ValueError, "smaller"):
            FramePublisher(
                max_width=128,
                max_height=128,
                name=self.publisher.name,
                create=False,
            )


if __name__ == "__main__":
    unittest.main()
