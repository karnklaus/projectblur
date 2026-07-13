"""Measure sequential face-detector and web-pipeline latency."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, median
from time import perf_counter

import numpy as np
import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend", choices=("openvino", "tensorflow", "yunet"), required=True
    )
    parser.add_argument("--mode", choices=("adapter", "pipeline"), default="adapter")
    parser.add_argument("--device", default="AUTO", help="OpenVINO device name")
    parser.add_argument("--model", type=Path, help="Optional detector model override")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0:
        parser.error("width and height must be positive")
    if args.warmup < 0 or args.iterations <= 0:
        parser.error("warmup must be non-negative and iterations must be positive")
    return args


def create_detector(backend: str, device: str, model: Path | None):
    if backend == "openvino":
        from projectblur.detection import OpenVinoRetinaFaceDetector

        return OpenVinoRetinaFaceDetector(model, device=device)
    if backend == "yunet":
        from projectblur.detection import YuNetDetector

        return YuNetDetector(model)
    from projectblur.detection import RetinaFaceDetector

    return RetinaFaceDetector(confidence_threshold=0.9, allow_upscaling=False)


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def summarize(timings: list[float]) -> dict[str, float]:
    """Return consistent latency statistics for a non-empty timing list."""
    average = mean(timings)
    return {
        "mean_seconds": average,
        "median_seconds": median(timings),
        "p95_seconds": percentile_nearest_rank(timings, 0.95),
        "minimum_seconds": min(timings),
        "maximum_seconds": max(timings),
        "mean_fps": 1 / average,
    }


def main() -> None:
    args = parse_args()
    detector = create_detector(args.backend, args.device, args.model)
    image = np.zeros((args.height, args.width, 3), dtype=np.uint8)

    if args.mode == "pipeline":
        from projectblur.web.processing import anonymize_image_bytes

        encoded, buffer = cv2.imencode(
            ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 86]
        )
        if not encoded:
            raise RuntimeError("Unable to encode the synthetic benchmark input")
        content = buffer.tobytes()

        def execute():
            return anonymize_image_bytes(content, detector)

    else:
        def execute():
            return detector.detect(image)

    started = perf_counter()
    first_result = execute()
    cold_seconds = perf_counter() - started
    for _ in range(args.warmup):
        execute()

    timings: list[float] = []
    stage_timings: dict[str, list[float]] = {
        "decode": [],
        "detection": [],
        "blur": [],
        "encode": [],
        "total": [],
    }
    for _ in range(args.iterations):
        started = perf_counter()
        result = execute()
        timings.append(perf_counter() - started)
        if args.mode == "pipeline":
            stage_timings["decode"].append(result.timings.decode_seconds)
            stage_timings["detection"].append(result.timings.detection_seconds)
            stage_timings["blur"].append(result.timings.blur_seconds)
            stage_timings["encode"].append(result.timings.encode_seconds)
            stage_timings["total"].append(result.timings.total_seconds)

    faces_detected = (
        first_result.faces_detected if args.mode == "pipeline" else len(first_result)
    )
    result = {
        "backend": args.backend,
        "mode": args.mode,
        "device": args.device.upper() if args.backend == "openvino" else "CPU",
        "input_width": args.width,
        "input_height": args.height,
        "input": "all-black synthetic BGR array",
        "warmup_iterations": args.warmup,
        "measured_iterations": args.iterations,
        "cold_seconds": cold_seconds,
        **summarize(timings),
        "faces_detected": faces_detected,
    }
    if args.mode == "pipeline":
        result["stage_timings"] = {
            name: summarize(values) for name, values in stage_timings.items()
        }
    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
