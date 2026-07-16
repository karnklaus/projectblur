"""Tests for virtual-camera benchmark result calculations."""

from __future__ import annotations

from argparse import Namespace
import importlib.util
from pathlib import Path
import unittest


BENCHMARK_PATH = (
    Path(__file__).resolve().parents[2]
    / "benchmarks"
    / "virtual_camera_output_benchmark.py"
)
SPEC = importlib.util.spec_from_file_location(
    "projectblur_virtual_camera_benchmark",
    BENCHMARK_PATH,
)
assert SPEC is not None and SPEC.loader is not None
BENCHMARK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCHMARK)


class VirtualCameraBenchmarkTests(unittest.TestCase):
    def test_summarizes_delivery_loss_and_serial_publish_cost(self) -> None:
        args = Namespace(
            width=1280,
            height=720,
            fps=30,
            seconds=10.0,
            warmup=1.5,
            baseline_fps=40.0,
        )
        native = {
            "delivered_fps": 29.0,
            "requested_fps": 30,
            "source_frame_span": 300,
            "source_frames_not_observed": 3,
        }

        result = BENCHMARK.summarize(
            args=args,
            native=native,
            published_frames=300,
            publisher_seconds=10.0,
            publish_timings_ms=[1.0, 2.0, 3.0],
        )

        comparison = result["comparison"]
        self.assertAlmostEqual(
            comparison["target_to_camera_fps_loss_percent"],
            100 / 30,
        )
        self.assertEqual(comparison["source_frames_not_observed_percent"], 1.0)
        self.assertAlmostEqual(
            comparison["estimated_pipeline_fps_with_publish"],
            1 / (1 / 40 + 0.002),
        )
        self.assertEqual(result["publisher"]["p95_publish_ms"], 3.0)


if __name__ == "__main__":
    unittest.main()
