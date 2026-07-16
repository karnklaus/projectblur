# ProjectBlur Architecture

## Architecture Status and Evolution

This document distinguishes `Current`, `Planned`, `Under evaluation`,
`Deprecated`, and `Rejected` designs. Current code is not an immutable target.
Significant changes require evidence, impact analysis, migration and rollback
plans, tests, and a new entry in `docs/DECISIONS.md`. Superseded designs remain
in the decision history rather than being erased.

## System Overview

**Current:** The implemented surface is deliberately small: the detection
package adapts OpenVINO RetinaFace, TensorFlow RetinaFace, and experimental
OpenCV YuNet backends into a shared ProjectBlur-owned result shape, the
anonymization package applies Gaussian blur to detections, and a FastAPI
prototype API handles bounded in-memory images and reduced detector frames
captured by the browser from a camera or shared screen. The browser renders
returned face boxes on a matching source-resolution canvas and does not expose
image upload. Tracking, alignment, recognition, whitelist
matching, decision caching, continuous video output, and centralized
configuration are planned. Library modules use Python's standard `logging` API.
Unit tests mock external model inference.

## Browser Input Prototype

**Current:** `src/projectblur/web/app.py` retains `/api/blur` for bounded
in-memory decode, detection, Gaussian blur, and JPEG responses. The live browser
path instead copies each source frame at its original dimensions, creates a
reduced detector JPEG, and sends it to `/api/detect`. That endpoint returns only
the reduced-frame dimensions and face bounding boxes. The browser scales those
boxes and blurs the matching source-resolution canvas, so pixels outside face
regions do not pass through a server JPEG re-encode. The browser can explicitly
download the latest matching original and blurred canvases as PNG files;
downloads are user-initiated and are not persisted by the server. Detector
inputs offer 480, 640, and 960 pixel maximum-edge modes and default to 640
pixels. Frames remain sequential to prevent client request backlog; this is not
a production video protocol. A lock serializes prototype inference calls
because backend concurrency has not been validated. The default web detector
is OpenCV YuNet on CPU; OpenVINO RetinaFace ResNet50 and TensorFlow remain
explicit references.

**Current / Under evaluation:** YuNet is the web prototype default after passing
the synthetic adapter and in-process server
latency gates in `EXP-004`. Two schema v2 screen-share sessions achieved 46.986
FPS overall across 7,425 samples; the visible subset achieved 50.324 FPS with
23.9 ms P95 processing latency. This default is a performance-oriented
prototype choice, not a production-detector selection. Authorized face misses remain unmeasured. The
schema v2 measurements used the former returned-JPEG path. The source-resolution
canvas path starts metrics schema v3, so its performance must be measured again
and must not be combined with schema v2 results.

**Current:** Live sessions automatically collect bounded, privacy-safe metrics
in browser memory. Schema v3 processing measurements include source-resolution
capture, reduced detector JPEG, coordinate request/response, server stages, and
source-resolution canvas render. Presentation callbacks are observed separately
without blocking the sequential processing loop. Samples include document
visibility, warm-up, and capture-stall markers.
The UI shows a rolling 300-sample summary and can export retained per-frame
values as JSON. Exports contain dimensions, settings, timing, and face counts
but no image, identity, URL, or title data. Metrics are not persisted by the
server.

Browser background execution is not a reliable 30 FPS path. Intentional hidden
periods caused capture/JPEG to fall to approximately one iteration per second,
even though non-blocking presentation timing allowed the processing loop to
continue. A worker/media pipeline or non-browser runtime must be evaluated
separately if background operation is a hard requirement.

Lower capture resolution reduces latency but can reduce detection of small or
distant faces. This tradeoff must be measured with authorized face inputs before
selecting a production setting.

Browser capture requests video only and requires user permission. Stopping the
source stops all acquired media tracks; ending browser screen sharing also
stops the preview loop. The result is visible only in the ProjectBlur page. It
is not a virtual camera or replacement stream for other applications.

The prototype does not implement identity recognition or a whitelist. Every
detection is blurred.

## Process Architecture

**Planned / partially implemented:** A three-stage process architecture is planned:

1. An ingestion process reads images, files, cameras, or streams.
2. An inference process performs detection, tracking, and recognition.
3. A rendering/output process applies anonymization and publishes previews or
   recordings.

The high-resolution processor and versioned latest-frame shared-memory contract
are implemented in `src/projectblur/pipeline`. A Windows Media Foundation
source consumes the contract and streams through the registered ProjectBlur
virtual camera. Desktop webcam and Windows Graphics Capture ingestion,
browser/native orchestration, and production packaging are not implemented yet.

## Frame Transport

**Current prototype primitive / Under evaluation:**
`projectblur.pipeline.frame_bridge` publishes the latest BGRA frame through a
versioned `multiprocessing.shared_memory` mapping. The 56-byte header uses an
odd/even sequence guard so readers reject a frame while it is being written.
The native header in `native/virtual_camera` fixes the matching layout. This is
a single latest-frame transport, not the previously proposed ring buffer; it
intentionally drops superseded frames instead of building output latency.

The contract has offline Python validation, C++ layout validation, a synthetic
Python-to-native cross-process read, and end-to-end Media Foundation benchmark
coverage. On the development machine, 10-second 720p and 1080p trials each
delivered 30.1 FPS with 301 unique source frames, no fallback frames, and no
unobserved or duplicate frames. These synthetic transport results are not
face-detection, CPU/resource, or application-compatibility evidence.

## High-resolution Anonymization

**Current prototype primitive:** `projectblur.pipeline.high_resolution`
reduces a copy of a BGR source frame to a configurable detector edge, maps
detections and landmarks back into source coordinates, and applies Gaussian
blur to a copy of the full-resolution frame. This preserves unaffected source
pixels in memory and its BGRA result can be published through the frame bridge.
It does not yet provide desktop capture, recording, orchestration, tracking, or
a guarantee that the current detector finds every face.

## Windows Virtual Camera

**Current prototype:** `DEC-006` and `DEC-008` define a ProjectBlur-owned
user-mode Media Foundation virtual camera for Windows 11 build 22000 or newer.
The x64 source exposes 1280x720 and 1920x1080 NV12/RGB32 media types at 30 FPS,
reads a per-user global BGRA mapping, and returns black for absent, stale,
wrong-sized, or malformed input rather than exposing a raw source frame. The
camera is registered with current-user access; its COM CLSID must be
machine-visible because Windows Camera Frame Server runs outside the user's
HKCU context. The installer therefore requires explicit elevation and places
the DLL under Program Files with service-readable ACLs.

Registration, source activation, fallback streaming, and synthetic 720p/1080p
delivery have passed on one Windows 11 development machine. The DLL is unsigned.
Physical-camera and Windows Graphics Capture ingestion, detector failure
orchestration, Windows Camera/Zoom/Meet/Teams compatibility, release signing,
CPU/memory measurement, and authorized-face validation remain pending. The
current browser page is still not a publisher for the virtual camera.

## Detection-by-Tracking

**Planned:** The pipeline runs detection periodically, tracks faces between
detection frames, and caches recognition/anonymization decisions by track ID.
Recognition should run again when tracking quality drops or cached identity
confidence expires. The cadence and expiry policy are to be confirmed.

## Standard Detection Schema

Both detector adapters return `list[Detection]`, where `Detection` is a
ProjectBlur-owned `TypedDict` defined in
`src/projectblur/detection/schema.py`:

```python
{
    "confidence": 0.98,
    "bbox": {"x1": 100, "y1": 80, "x2": 220, "y2": 240},
    "landmarks": {"nose": [160.0, 150.0]},
}
```

The end-to-end schema is not finalized. A proposed future domain result adds
`track_id`, `identity`, `authorized`, and `anonymize`. These fields must not be
added to detector adapters until the domain boundary and compatibility policy
are decided.

## Module Boundaries

- External detector adapters belong in `src/projectblur/detection`.
- Business logic must not depend directly on a detector library.
- Tracking must remain independent of UI code.
- Anonymization must not perform recognition.
- API endpoints must not contain the complete inference pipeline.
- Configuration must be separated from implementation when introduced.
- The web layer may orchestrate adapters and domain operations but must not
  implement detection or anonymization algorithms itself.

## Failure Handling

- Missing models or dependencies: fail with an actionable configuration error.
- Invalid images: reject before inference.
- No face detected: return an empty detection list.
- Camera unavailable or stream disconnected: report degraded input state and
  allow controlled retry or shutdown.
- Virtual-camera publisher missing, stale, malformed, or wrong-sized: emit a
  black frame and flag the sample as fallback; never expose an unprocessed
  physical or screen source.
- Missing video codec: report the unavailable output and preserve other safe
  outputs where possible.
- GPU unavailable: use a configured CPU fallback only when equivalent safe
  behavior is available; never silently change model semantics.
