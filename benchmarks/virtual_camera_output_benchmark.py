"""Measure ProjectBlur's BGRA publisher and Windows virtual-camera output."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import sys
from time import monotonic, perf_counter, sleep

import numpy as np

from projectblur.pipeline import FramePublisher
from projectblur.benchmarking import create_benchmark_metadata, save_benchmark_record


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTROL = (
    PROJECT_ROOT
    / "native"
    / "virtual_camera"
    / "build"
    / "Release"
    / "ProjectBlurCameraControl.exe"
)
MEDIA_SOURCE_CLSID = "{615F8DBA-693F-476C-8A89-37E62854263D}"


def installed_media_source_sha256() -> str | None:
    """Return the registered ProjectBlur DLL hash when readable on Windows."""
    if os.name != "nt":
        return None
    import winreg

    key_path = f"Software\\Classes\\CLSID\\{MEDIA_SOURCE_CLSID}\\InprocServer32"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            dll_value, _ = winreg.QueryValueEx(key, None)
        dll_path = Path(dll_value)
        return hashlib.sha256(dll_path.read_bytes()).hexdigest()
    except (FileNotFoundError, OSError, TypeError):
        return None


def parse_args() -> argparse.Namespace:
    """Parse and validate benchmark command-line options."""
    parser = argparse.ArgumentParser(
        description=(
            "Publish synthetic BGRA frames and read them through the installed "
            "ProjectBlur Windows virtual camera."
        )
    )
    parser.add_argument("--control", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--width", type=int, choices=(1280, 1920), default=1280)
    parser.add_argument("--height", type=int, choices=(720, 1080), default=720)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--warmup", type=float, default=1.5)
    parser.add_argument(
        "--baseline-fps",
        type=float,
        help=(
            "Optional measured pipeline FPS used to estimate the serial FPS "
            "cost of publishing one output frame."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional exact JSON path. By default, a unique record is saved under "
            "artifacts/benchmarks/. Existing files are never overwritten."
        ),
    )
    args = parser.parse_args()
    if (args.width, args.height) not in ((1280, 720), (1920, 1080)):
        parser.error("supported sizes are 1280x720 and 1920x1080")
    if args.fps != 30:
        parser.error("the current virtual-camera source supports 30 FPS")
    if args.seconds <= 0 or args.warmup < 0:
        parser.error("seconds must be positive and warmup must be non-negative")
    if args.baseline_fps is not None and args.baseline_fps <= 0:
        parser.error("baseline-fps must be positive")
    return args


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    """Return a nearest-rank percentile for a non-empty list."""
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def create_synthetic_bgra(width: int, height: int) -> np.ndarray:
    """Create a reusable privacy-safe BGRA test frame."""
    frame = np.empty((height, width, 4), dtype=np.uint8)
    horizontal = np.arange(width, dtype=np.uint16)
    frame[:, :, 0] = ((horizontal * 3) % 256).astype(np.uint8)
    frame[:, :, 1] = ((horizontal * 5) % 256).astype(np.uint8)
    frame[:, :, 2] = 32
    frame[:, :, 3] = 255
    return frame


def summarize(
    *,
    args: argparse.Namespace,
    native: dict[str, object],
    published_frames: int,
    publisher_seconds: float,
    publish_timings_ms: list[float],
) -> dict[str, object]:
    """Combine publisher and camera-reader metrics into one JSON result."""
    delivered_fps = float(native["delivered_fps"])
    requested_fps = float(native["requested_fps"])
    source_span = int(native["source_frame_span"])
    source_not_observed = int(native["source_frames_not_observed"])
    mean_publish_ms = sum(publish_timings_ms) / len(publish_timings_ms)
    comparison: dict[str, float | None] = {
        "target_to_camera_fps_delta": requested_fps - delivered_fps,
        "target_to_camera_fps_loss_percent": max(
            0.0, (requested_fps - delivered_fps) / requested_fps * 100.0
        ),
        "source_frames_not_observed_percent": (
            source_not_observed / source_span * 100.0 if source_span else None
        ),
        "estimated_pipeline_fps_with_publish": None,
        "estimated_pipeline_fps_loss_percent": None,
    }
    if args.baseline_fps is not None:
        estimated_fps = 1.0 / (1.0 / args.baseline_fps + mean_publish_ms / 1000.0)
        comparison["estimated_pipeline_fps_with_publish"] = estimated_fps
        comparison["estimated_pipeline_fps_loss_percent"] = (
            (args.baseline_fps - estimated_fps) / args.baseline_fps * 100.0
        )

    return {
        "schema_version": 1,
        "benchmark": "projectblur_virtual_camera_output",
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "process_bits": 64 if os.sys.maxsize > 2**32 else 32,
            "installed_media_source_sha256": installed_media_source_sha256(),
        },
        "input": {
            "kind": "synthetic moving BGRA frame",
            "width": args.width,
            "height": args.height,
            "target_fps": args.fps,
            "measurement_seconds": args.seconds,
            "warmup_seconds": args.warmup,
            "baseline_pipeline_fps": args.baseline_fps,
        },
        "publisher": {
            "frames_published": published_frames,
            "active_seconds": publisher_seconds,
            "achieved_fps": published_frames / publisher_seconds,
            "mean_publish_ms": mean_publish_ms,
            "p95_publish_ms": percentile_nearest_rank(publish_timings_ms, 0.95),
            "max_publish_ms": max(publish_timings_ms),
        },
        "camera_reader": native,
        "comparison": comparison,
        "limitations": [
            "The test isolates output transport and BGRA-to-NV12 conversion; it does not run face detection.",
            "The camera media type is currently capped at 30 FPS.",
            "Estimated pipeline FPS is a serial-cost estimate, not a concurrent end-to-end detector benchmark.",
        ],
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    """Run the publisher and native camera reader concurrently."""
    control = args.control.resolve()
    if not control.is_file():
        raise FileNotFoundError(f"virtual-camera control was not found: {control}")
    mapping_name = subprocess.run(
        [str(control), "mapping-name"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with tempfile.TemporaryDirectory(prefix="projectblur-vcam-") as temp_dir:
        native_output = Path(temp_dir) / "native.json"
        command = [
            str(control),
            "benchmark",
            "--seconds",
            str(args.seconds),
            "--warmup",
            str(args.warmup),
            "--width",
            str(args.width),
            "--height",
            str(args.height),
            "--fps",
            str(args.fps),
            "--output",
            str(native_output),
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        publisher: FramePublisher | None = None
        attach_deadline = monotonic() + max(5.0, args.warmup + 2.0)
        while monotonic() < attach_deadline and process.poll() is None:
            try:
                publisher = FramePublisher(
                    max_width=1920,
                    max_height=1080,
                    name=mapping_name,
                    create=False,
                )
                break
            except FileNotFoundError:
                sleep(0.02)
        if publisher is None:
            stdout, stderr = process.communicate(timeout=5)
            raise RuntimeError(
                "unable to attach to the virtual-camera frame mapping; "
                f"exit={process.returncode}, stdout={stdout!r}, stderr={stderr!r}"
            )

        frame = create_synthetic_bgra(args.width, args.height)
        publish_timings_ms: list[float] = []
        published_frames = 0
        publisher_start = perf_counter()
        next_frame = publisher_start
        period = 1.0 / args.fps
        previous_bar = 0
        try:
            while process.poll() is None:
                now = perf_counter()
                if now < next_frame:
                    sleep(min(next_frame - now, period))
                    continue
                frame[:, previous_bar : previous_bar + 12, 2] = 32
                bar = (published_frames * 17) % max(1, args.width - 12)
                frame[:, bar : bar + 12, 2] = 255
                previous_bar = bar
                started = perf_counter()
                publisher.publish(frame)
                publish_timings_ms.append((perf_counter() - started) * 1000.0)
                published_frames += 1
                next_frame += period
                if next_frame < perf_counter() - period:
                    next_frame = perf_counter() + period
        finally:
            publisher_seconds = perf_counter() - publisher_start
            publisher.close()

        stdout, stderr = process.communicate(timeout=5)
        if process.returncode != 0:
            raise RuntimeError(
                f"native camera benchmark failed ({process.returncode}): {stderr or stdout}"
            )
        if not publish_timings_ms:
            raise RuntimeError("no frames were published during the benchmark")
        native = json.loads(native_output.read_text(encoding="utf-8"))
        return summarize(
            args=args,
            native=native,
            published_frames=published_frames,
            publisher_seconds=publisher_seconds,
            publish_timings_ms=publish_timings_ms,
        )


def main() -> None:
    """Run the benchmark, print it, and persist an immutable JSON record."""
    args = parse_args()
    metadata = create_benchmark_metadata(
        PROJECT_ROOT,
        packages=("numpy", "opencv-python"),
    )
    result = run(args)
    result.update(
        {
            "run_id": metadata["run_id"],
            "recorded_at_utc": metadata["recorded_at_utc"],
            "repository": metadata["repository"],
        }
    )
    result["environment"] = {
        **metadata["environment"],
        **result["environment"],
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    output_path = save_benchmark_record(
        result,
        project_root=PROJECT_ROOT,
        filename_prefix=(
            f"projectblur_virtual_camera_{args.width}x{args.height}_{args.fps}fps"
        ),
        output=args.output,
    )
    print(rendered)
    print(f"Saved benchmark record: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
