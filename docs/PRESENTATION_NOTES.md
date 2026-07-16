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
detection and Gaussian blurring through the API or sequential camera/screen
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
- A browser prototype accepts a camera or shared screen, sends only a reduced
  detector JPEG, and blurs returned face boxes on the matching
  source-resolution canvas; image upload is no longer exposed in the browser.
- Fifty-four offline unit tests pass without network, model downloads, or GPU.
- A separate pipeline checkpoint detects on reduced frames, maps detections to
  source resolution, blurs full-resolution pixels, and publishes latest-only
  BGRA frames through shared memory.
- A ProjectBlur-owned Windows Media Foundation camera registered and delivered
  synthetic 720p and 1080p output at 30.1 FPS for 10 seconds each, with no
  missing, duplicate, stale, or fallback samples after the pacing fix. This is
  transport evidence, not authorized-face or application-compatibility proof.
- Measured publish copy time was 0.307 ms at 720p and 0.734 ms at 1080p. Applied
  serially to the earlier 45.1 FPS log, that estimates 1.37% and 3.20% pipeline
  reductions; the camera output remains intentionally capped at 30 FPS.
- The initial 30-iteration synthetic 640x360 adapter benchmark measured YuNet
  CPU at 185.18 FPS, OpenVINO AUTO at 6.09 FPS, and TensorFlow CPU at 1.47 FPS.
  The initial YuNet complete in-process pipeline measured 163.67 FPS with P95
  6.92 ms, and local HTTP measured 119.02 requests per second.
- A same-machine 2026-07-17 repeat measured YuNet CPU at 218.784 FPS (P95 5.007
  ms), OpenVINO AUTO at 6.488 FPS (P95 172.779 ms), and TensorFlow CPU at 1.792
  FPS (P95 611.162 ms). Only YuNet was below the 33.333 ms mean 30 FPS frame
  budget. Exact values are in
  `artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`.
- A manual YuNet screen-share run exceeded 4,800 iterations; three spot readings
  ranged from 74.1 to 86.2 pipeline FPS. This is provisional browser performance
  evidence, not a per-frame distribution or accuracy result.
- Real-face ground truth, missed/unblurred frames, exact browser configuration,
  and resource use are not yet validated. YuNet is now the performance-oriented
  web prototype default; OpenVINO RetinaFace remains an explicit reference.

## Paper-use guardrails

- Describe these detector numbers as sequential, synthetic, zero-face latency;
  do not call them accuracy, recall, privacy safety, or integrated output FPS.
- Cite raw JSON artifacts and state resolution, warm-up, measured iterations,
  hardware/software versions, Git dirty state, and model hashes.
- Use repeated runs and disclose every inclusion or exclusion. The 2026-07-17
  console artifact is one repeat, not a confidence interval.
- Keep browser schema v1/v2/v3, detector adapter, and virtual-camera transport
  results in separate tables unless a future experiment measures an integrated
  path under one clock and procedure.

## Contributions

Current ProjectBlur-owned work is the adapter contract, normalization and error
handling, mocked tests, CLI example, and evidence-oriented documentation. The
RetinaFace implementation itself is third-party work.

## Future Work

Finalize the domain schema, pin and validate dependencies, run detector
benchmarks, select tracking and recognition components, connect physical-camera
and screen capture to the Windows source, sign and test the native output in
target applications, and evaluate deployment and privacy controls. Any major
flow change must retain decision and experiment history.
