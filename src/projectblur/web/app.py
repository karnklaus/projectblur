"""FastAPI prototype for detector-powered browser input blurring."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response

from projectblur.detection import OpenVinoRetinaFaceDetector
from projectblur.web.processing import (
    FaceDetector,
    anonymize_image_bytes,
    detect_image_bytes,
)

APP_TITLE = "ProjectBlur Prototype"
STATIC_DIRECTORY = Path(__file__).with_name("static")
INFERENCE_LOCK = Lock()
DETECTOR_BACKEND = os.getenv("PROJECTBLUR_DETECTOR", "yunet").strip().lower()
OPENVINO_DEVICE = os.getenv("PROJECTBLUR_OPENVINO_DEVICE", "AUTO").strip().upper()
OPENVINO_MODEL_PATH = os.getenv("PROJECTBLUR_OPENVINO_MODEL")
YUNET_MODEL_PATH = os.getenv("PROJECTBLUR_YUNET_MODEL")

app = FastAPI(
    title=APP_TITLE,
    description="In-memory face detection and Gaussian face blurring for browser inputs.",
    version="0.1.0",
)


@lru_cache(maxsize=1)
def get_detector() -> FaceDetector:
    """Create the configured, cached face-detector backend."""
    if DETECTOR_BACKEND == "openvino":
        return OpenVinoRetinaFaceDetector(
            OPENVINO_MODEL_PATH,
            confidence_threshold=0.5,
            device=OPENVINO_DEVICE,
        )
    if DETECTOR_BACKEND == "tensorflow":
        from projectblur.detection import RetinaFaceDetector

        return RetinaFaceDetector(confidence_threshold=0.9, allow_upscaling=False)
    if DETECTOR_BACKEND == "yunet":
        from projectblur.detection import YuNetDetector

        return YuNetDetector(YUNET_MODEL_PATH, confidence_threshold=0.6)
    raise RuntimeError(
        "PROJECTBLUR_DETECTOR must be 'openvino', 'tensorflow', or 'yunet'"
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    """Serve the image, camera, and screen-input prototype interface."""
    return HTMLResponse(
        STATIC_DIRECTORY.joinpath("index.html").read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Return process health without loading model weights."""
    detector_name = (
        "opencv-yunet" if DETECTOR_BACKEND == "yunet" else f"retinaface-{DETECTOR_BACKEND}"
    )
    result = {"status": "ok", "detector": detector_name}
    if DETECTOR_BACKEND == "openvino":
        result["device"] = OPENVINO_DEVICE
    return result


@app.post("/api/blur", response_class=Response)
def blur_uploaded_image(
    image: Annotated[bytes, File(description="JPEG, PNG, or WebP image")],
    blur_strength: Annotated[int, Form(ge=3, le=99)] = 45,
    padding_ratio: Annotated[float, Form(ge=0, le=0.5)] = 0.15,
) -> Response:
    """Blur all face detections without retaining the uploaded image."""
    try:
        with INFERENCE_LOCK:
            result = anonymize_image_bytes(
                image,
                get_detector(),
                blur_strength=blur_strength,
                padding_ratio=padding_ratio,
            )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return Response(
        content=result.content,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Faces-Detected": str(result.faces_detected),
            "X-Detection-Milliseconds": f"{result.timings.detection_seconds * 1000:.3f}",
            "X-Server-Milliseconds": f"{result.timings.total_seconds * 1000:.3f}",
            "Server-Timing": (
                f"decode;dur={result.timings.decode_seconds * 1000:.3f}, "
                f"detect;dur={result.timings.detection_seconds * 1000:.3f}, "
                f"blur;dur={result.timings.blur_seconds * 1000:.3f}, "
                f"encode;dur={result.timings.encode_seconds * 1000:.3f}, "
                f"total;dur={result.timings.total_seconds * 1000:.3f}"
            ),
        },
    )


@app.post("/api/detect", response_class=JSONResponse)
def detect_browser_frame(
    image: Annotated[bytes, File(description="Reduced JPEG browser frame")],
) -> JSONResponse:
    """Return face coordinates so the browser can render at source resolution."""
    try:
        with INFERENCE_LOCK:
            result = detect_image_bytes(image, get_detector())
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return JSONResponse(
        content={
            "width": result.width,
            "height": result.height,
            "faces_detected": len(result.detections),
            "boxes": [detection["bbox"] for detection in result.detections],
        },
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Faces-Detected": str(len(result.detections)),
            "X-Detection-Milliseconds": (
                f"{result.timings.detection_seconds * 1000:.3f}"
            ),
            "X-Server-Milliseconds": f"{result.timings.total_seconds * 1000:.3f}",
            "Server-Timing": (
                f"decode;dur={result.timings.decode_seconds * 1000:.3f}, "
                f"detect;dur={result.timings.detection_seconds * 1000:.3f}, "
                f"total;dur={result.timings.total_seconds * 1000:.3f}"
            ),
        },
    )
