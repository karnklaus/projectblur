# ProjectBlur Tasks

## Current

- [ ] Decide and define the domain-level face detection result schema.
- [ ] Compare RetinaFace with YuNet for CPU accuracy and latency.
- [ ] Run `EXP-004` YuNet CPU baseline using controlled latency and explicitly
  authorized face-detection comparisons.
- [ ] Repeat the YuNet browser trial with browser, exact resolution, visible-face
  ground truth, misses/flicker, CPU, and RAM recorded.
- [ ] Add a reproducible detector benchmark script and authorized test inputs.
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

## Planned

- [ ] Integrate ByteTrack or SORT.
- [ ] Add MobileFaceNet embeddings.
- [ ] Add FAISS whitelist matching.
- [ ] Add track decision caching.
- [ ] Replace sequential JPEG requests with a measured streaming architecture
  if prototype latency requires it, and evaluate a React preview.
- [ ] Add virtual-camera output.
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
