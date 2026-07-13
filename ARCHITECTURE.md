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
prototype handles uploaded images and sequential frames captured by the browser
from a camera or shared screen. Tracking, alignment, recognition, whitelist
matching, decision caching, continuous video output, and centralized
configuration are planned. Library modules use Python's standard `logging` API.
Unit tests mock external model inference.

## Browser Input Prototype

**Current:** `src/projectblur/web/app.py` accepts a bounded in-memory image,
passes the decoded OpenCV array through the configured detector, applies
Gaussian blur through `src/projectblur/anonymization`, and returns an encoded JPEG. The
browser page accepts an uploaded file or uses browser media APIs to capture a
camera or shared screen. Live capture offers 480, 640, and 960 pixel modes and
defaults to a 640-pixel maximum edge. The default web detector is Open Model Zoo
RetinaFace ResNet50 through OpenVINO `AUTO`. The TensorFlow adapter remains an
explicit reference fallback, and YuNet is an explicit experimental CPU option;
neither is selected silently. Frames are sent sequentially through
the same endpoint, which prevents client request backlog but does not provide a
production video protocol. A lock serializes prototype inference calls because
backend concurrency has not been validated.

**Under evaluation:** YuNet passed the synthetic adapter and in-process server
latency gates in `EXP-004`, but browser FPS and authorized face misses remain
unmeasured. The existing JPEG request/response path is retained until a
controlled 300-frame browser run shows that transport changes are necessary.

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

**Planned:** A three-stage process architecture is planned:

1. An ingestion process reads images, files, cameras, or streams.
2. An inference process performs detection, tracking, and recognition.
3. A rendering/output process applies anonymization and publishes previews or
   recordings.

No multiprocessing pipeline is implemented yet.

## Frame Transport

**Under evaluation:** use `multiprocessing.shared_memory` with a ring buffer and
pass frame indices rather than serialized frames. This should minimize frame
copies and pickling, but it has not been implemented or benchmarked.

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
- Missing video codec: report the unavailable output and preserve other safe
  outputs where possible.
- GPU unavailable: use a configured CPU fallback only when equivalent safe
  behavior is available; never silently change model semantics.
