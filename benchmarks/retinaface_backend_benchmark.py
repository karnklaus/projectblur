"""Measure sequential face-detector and web-pipeline latency."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, median
import sys
from time import perf_counter

import numpy as np
import cv2

from projectblur.benchmarking import (
    create_benchmark_metadata,
    file_evidence,
    save_benchmark_record,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional exact JSON path. By default, a unique record is saved under "
            "artifacts/benchmarks/. Existing files are never overwritten."
        ),
    )
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


def model_evidence(detector: object) -> dict[str, object]:
    """Return hashes for local detector model files when the adapter exposes them."""
    model_path = getattr(detector, "model_path", None)
    if not isinstance(model_path, Path):
        return {
            "files": [],
            "note": "Model storage is managed externally by the selected package.",
        }
    paths = [model_path]
    if model_path.suffix.lower() == ".xml":
        weights_path = model_path.with_suffix(".bin")
        if weights_path.is_file():
            paths.append(weights_path)
    return {
        "files": [file_evidence(path, project_root=PROJECT_ROOT) for path in paths]
    }


def main() -> None:
    args = parse_args()
    metadata = create_benchmark_metadata(
        PROJECT_ROOT,
        packages=(
            "numpy",
            "opencv-python",
            "openvino",
            "retina-face",
            "tensorflow",
            "tf-keras",
        ),
    )
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
        "schema_version": 1,
        "benchmark": "projectblur_detector_latency",
        **metadata,
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
        "model": model_evidence(detector),
        "limitations": [
            "The synthetic all-black input contains no faces.",
            "This run measures latency only, not detection accuracy or privacy safety.",
            "CPU and memory utilization are not measured by this script.",
        ],
    }
    if args.mode == "pipeline":
        result["stage_timings"] = {
            name: summarize(values) for name, values in stage_timings.items()
        }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    output_path = save_benchmark_record(
        result,
        project_root=PROJECT_ROOT,
        filename_prefix=(
            f"projectblur_detector_{args.backend}_{args.mode}_{result['device'].lower()}"
        ),
        output=args.output,
    )
    print(rendered)
    print(f"Saved benchmark record: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
