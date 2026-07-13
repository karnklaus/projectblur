# ProjectBlur Architecture

## Architecture Status and Evolution

This document distinguishes `Current`, `Planned`, `Under evaluation`,
`Deprecated`, and `Rejected` designs. Current code is not an immutable target.
Significant changes require evidence, impact analysis, migration and rollback
plans, tests, and a new entry in `docs/DECISIONS.md`. Superseded designs remain
in the decision history rather than being erased.

## System Overview

**Current:** The implemented surface is deliberately small: the detection package adapts an
external detector into a ProjectBlur-owned result shape. Frame ingestion,
tracking, alignment, recognition, whitelist matching, decision caching,
anonymization, output, API, frontend, and centralized configuration are planned.
Library modules use Python's standard `logging` API. Unit tests mock external
model inference.

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

`RetinaFaceDetector.detect()` currently returns `list[Detection]`, where
`Detection` is a `TypedDict` defined in
`src/projectblur/detection/retinaface_detector.py`:

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
