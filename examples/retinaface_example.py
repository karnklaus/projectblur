"""Run ProjectBlur's RetinaFace adapter on one image."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from projectblur.detection import RetinaFaceDetector


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect faces in an image")
    parser.add_argument("image", type=Path, help="path to the input image")
    args = parser.parse_args()

    try:
        detections = RetinaFaceDetector().detect(str(args.image))
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")

    for detection in detections:
        print(f"confidence={detection['confidence']:.4f} bbox={detection['bbox']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
