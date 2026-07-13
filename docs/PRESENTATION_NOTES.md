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
whitelist matching, decision caching, anonymization, and output. Only the
RetinaFace adapter is currently implemented. Evidence: `ARCHITECTURE.md` and
`src/projectblur/detection/`.

## Research Basis

RetinaFace is the first external detector integration. Candidate detection,
tracking, recognition, and optimization sources are indexed in
`docs/RESEARCH.md`; most remain under evaluation.

## Development Journey

The project established an adapter boundary to avoid copying or coupling to an
external repository, then added mocked validation and an evidence-tracking
documentation system. Evidence: `docs/DEVELOPMENT_LOG.md` and
`docs/DECISIONS.md`.

## Experiments

Detector compatibility and performance testing is planned in `EXP-001`.
Metrics and results are not yet measured.

## Current Results

- RetinaFace adapter accepts image paths and OpenCV-style arrays.
- It validates inputs and normalizes confidence, bounding boxes, and landmarks.
- Nine mocked unit tests pass without network, model downloads, or GPU.
- Real-model accuracy, latency, FPS, and resource use are not yet validated.

## Contributions

Current ProjectBlur-owned work is the adapter contract, normalization and error
handling, mocked tests, CLI example, and evidence-oriented documentation. The
RetinaFace implementation itself is third-party work.

## Future Work

Finalize the domain schema, pin and validate dependencies, run detector
benchmarks, select tracking and recognition components, implement anonymization,
and evaluate deployment and privacy controls. Any major flow change must retain
decision and experiment history.
