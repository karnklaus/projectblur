# ProjectBlur Presentation Notes

Only evidence-backed statements belong here. Performance and compliance claims
remain targets until measured or independently reviewed.

## Problem

Images and video may expose faces and identity. ProjectBlur investigates
selective anonymization for privacy-conscious workflows. Legal PDPA compliance
has not been validated, so the project must not claim compliance.

## Objective

Build an extensible pipeline for images, recordings, CCTV, and live input. The
planned whitelist policy keeps authorized faces visible and anonymizes others.

## Proposed System

The planned flow covers ingestion, detection, tracking, alignment, embedding,
whitelist matching, decision caching, anonymization, and output. RetinaFace
detection and Gaussian blurring for image uploads or sequential camera/screen
frames are currently implemented as a prototype. Evidence: `ARCHITECTURE.md`, `src/projectblur/detection/`,
`src/projectblur/anonymization/`, and `src/projectblur/web/`.

## Research Basis

RetinaFace is the first external detector integration. TensorFlow and OpenVINO
backends now share a ProjectBlur detection schema. Candidate tracking,
recognition, and further optimization sources are indexed in
`docs/RESEARCH.md`; most remain under evaluation.

## Development Journey

The project established an adapter boundary to avoid copying or coupling to an
external repository, then added mocked validation and an evidence-tracking
documentation system. Evidence: `docs/DEVELOPMENT_LOG.md` and
`docs/DECISIONS.md`.

## Experiments

Synthetic detector latency is recorded in `EXP-003` and `EXP-004`. Authorized
accuracy, browser, and resource measurements remain pending.

## Current Results

- RetinaFace adapter accepts image paths and OpenCV-style arrays.
- It validates inputs and normalizes confidence, bounding boxes, and landmarks.
- A browser prototype accepts an image, camera, or shared screen and blurs every
  normalized detection in its returned preview.
- Forty offline unit tests pass without network, model downloads, or GPU.
- In a 30-iteration synthetic 640x360 adapter benchmark, OpenVINO AUTO averaged
  6.09 FPS versus TensorFlow CPU at 1.47 FPS. This is latency evidence only.
- The experimental YuNet adapter averaged 185.18 FPS with P95 6.12 ms, while
  its complete in-process pipeline averaged 163.67 FPS with P95 6.92 ms on the
  same zero-face resolution. Local HTTP averaged 119.02 requests per second.
- Real-face accuracy, 300-frame browser FPS, and resource use are not yet
  validated. OpenVINO RetinaFace remains the default.

## Contributions

Current ProjectBlur-owned work is the adapter contract, normalization and error
handling, mocked tests, CLI example, and evidence-oriented documentation. The
RetinaFace implementation itself is third-party work.

## Future Work

Finalize the domain schema, pin and validate dependencies, run detector
benchmarks, select tracking and recognition components, implement anonymization,
and evaluate deployment and privacy controls. Any major flow change must retain
decision and experiment history.
