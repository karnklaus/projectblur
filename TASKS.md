# ProjectBlur Tasks

## Current

- [ ] Add desktop physical-camera and Windows Graphics Capture ingestion for
  the high-resolution anonymization pipeline.
- [ ] Benchmark the integrated anonymization and virtual-camera output at 720p
  and 1080p with authorized webcam and screen sources (`EXP-005`).
- [ ] Define integrated fail-closed behavior for capture and detector failures
  before virtual-camera compatibility testing.
- [ ] Decide and define the domain-level face detection result schema.
- [ ] Compare RetinaFace with YuNet for CPU accuracy and latency.
- [ ] Run `EXP-004` YuNet CPU baseline using controlled latency and explicitly
  authorized face-detection comparisons.
- [ ] Run the YuNet browser accuracy/resource trial with browser version,
  visible-face ground truth, misses/flicker, CPU, and RAM recorded.
- [ ] Add explicitly authorized detector-accuracy inputs and ground truth to
  complement the synthetic latency benchmark.
- [ ] Design `EXP-002` to compare SIFT-based matching with a modern embedding
  baseline using privacy-critical error metrics.
- [ ] Validate the web prototype with authorized real images and record
  RetinaFace model-download, latency, and small-face behavior.
- [ ] Validate camera and screen capture manually with authorized sources and
  record end-to-end preview latency.
- [ ] Compare OpenVINO and TensorFlow detection agreement on authorized faces,
  including faces at or below 64x64 pixels.
- [ ] Pin dependency versions after real-inference compatibility validation.

## Completed

- [x] Add browser controls to export the latest matching original and blurred
  source-resolution frames as PNG images.
- [x] Automatically save every successful detector and virtual-camera CLI
  benchmark as a unique, immutable JSON record with environment and Git
  provenance for later paper analysis.
- [x] Implement, install, and stream the ProjectBlur Windows 11 Media Foundation
  virtual-camera source with current-user camera access and machine-visible COM
  registration (`DEC-006`, `DEC-008`).
- [x] Add a reproducible synthetic virtual-output benchmark and record 720p and
  1080p 30 FPS transport results with zero unobserved/duplicate source frames.
- [x] Make the native source emit black for missing, stale, malformed, or
  wrong-sized publisher frames instead of exposing an unprocessed source.
- [x] Replace the live returned-JPEG preview with a detection-only endpoint and
  source-resolution browser canvas anonymization while retaining `/api/blur`.
- [x] Add full-resolution anonymization using reduced detector frames and a
  versioned latest-frame BGRA shared-memory contract.
- [x] Validate one synthetic BGRA frame across the Python publisher and native
  Windows shared-memory reader.
- [x] Add `retina-face` as an external dependency.
- [x] Add a ProjectBlur-owned RetinaFace adapter for image paths and NumPy
  arrays.
- [x] Normalize RetinaFace bounding boxes and landmarks.
- [x] Add mocked unit tests that do not download a model or use the network.
- [x] Add a command-line RetinaFace example.
- [x] Record RetinaFace source and attribution information.
- [x] Add evidence-linked development, decision, experiment, milestone, and
  presentation records.
- [x] Add an in-memory FastAPI prototype for RetinaFace detection and Gaussian
  face blurring.
- [x] Add offline anonymization and web-processing unit tests.
- [x] Add browser camera and screen-share inputs with sequential blurred-frame
  preview and explicit source controls.
- [x] Disable RetinaFace automatic upscaling in the web path and add selectable
  live resolutions plus measured pipeline FPS feedback.
- [x] Add an OpenVINO RetinaFace adapter, official model-preparation script,
  mocked post-processing tests, and reproducible backend benchmark.
- [x] Select OpenVINO `AUTO` as the faster web prototype trial backend while
  preserving TensorFlow as an explicit reference fallback.
- [x] Validate pinned TensorFlow and OpenVINO RetinaFace runtimes with synthetic
  real inference while keeping face-accuracy validation pending.
- [x] Add an experimental OpenCV YuNet adapter, pinned local-model preparation,
  offline tests, per-stage web timing, and synthetic adapter/pipeline benchmark.
- [x] Run a YuNet screen-share session beyond 4,800 processed iterations and
  record three 74.1–86.2 FPS performance spot readings.
- [x] Add automatic bounded browser metrics, rolling/final summaries, slow-frame
  capture, and privacy-safe JSON export.
- [x] Analyze the first 7,898-sample automatic YuNet run, record its derived
  result, and make presentation timing non-blocking with visibility, warm-up,
  and capture-stall telemetry in schema v2.
- [x] Validate schema v2 across 7,425 samples and intentional visibility
  changes; confirm visible-tab performance and background capture throttling.
- [x] Make YuNet the performance-oriented web prototype default with an
  explicit OpenVINO rollback; accuracy selection remains pending.
- [x] Remove the image-upload control from the browser while preserving camera,
  screen sharing, and the internal frame-processing API.

## Planned

- [ ] Integrate ByteTrack or SORT.
- [ ] Add MobileFaceNet embeddings.
- [ ] Add FAISS whitelist matching.
- [ ] Add track decision caching.
- [ ] Replace sequential JPEG requests with a measured streaming architecture
  if prototype latency requires it, and evaluate a React preview.
- [ ] Connect desktop physical-camera and screen ingestion to the ProjectBlur
  virtual camera and validate signed release packaging and target applications.
- [ ] Evaluate OpenVINO and TensorRT optimization.
- [ ] Add recording and video-codec fallback.
- [ ] Add centralized privacy-focused logging and configuration.

## Blocked or Needs Decision

- [ ] Primary face detector and benchmark acceptance criteria
- [ ] Final standard detection/domain schema
- [ ] Supported Python version
- [ ] Packaging approach beyond `requirements.txt`
- [ ] Tracker and embedding model selection
- [ ] Model redistribution licenses
- [ ] Recognition and anonymization threshold calibration
