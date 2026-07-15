# ProjectBlur Development Log

Append significant work in chronological order. Preserve previous entries;
factual corrections must be recorded explicitly.

## 2026-07-13 — Establish RetinaFace detection baseline

### Objective

Integrate RetinaFace as an external dependency without copying upstream source
into ProjectBlur.

### Work Completed

- Added the detection package and `RetinaFaceDetector` adapter.
- Added result normalization, validation, confidence filtering, and missing
  dependency handling.
- Added a command-line example and mocked unit tests.
- Added dependency and upstream attribution documentation.

### Key Decisions

- Kept external code behind a ProjectBlur-owned adapter.
- Used mocked inference so unit tests require no network, weights, or GPU.

### Validation

- `python -m unittest discover -s tests/detection -p "test_*.py" -v`: nine
  tests passed.
- `python -m compileall src examples tests`: passed.

### Result

The adapter baseline is implemented. Real model compatibility, package version,
accuracy, and performance have not been validated.

### Next Step

Pin and validate the package in a project virtual environment, then compare the
detector against a CPU-oriented candidate with reproducible inputs.

## 2026-07-13 — Add agent context and development-history system

### Objective

Make project state, architecture status, research, decisions, experiments, and
presentation evidence maintainable inside the repository.

### Work Completed

- Added project context, architecture, coding, testing, research, and task
  documentation.
- Added decision, experiment, milestone, development-log, and presentation
  records.
- Added safe artifact directories for reproducible, non-sensitive outputs.
- Added rules for evidence-driven architecture evolution.

### Key Decisions

- Separated implemented facts from planned or evaluated designs.
- Required presentation claims to trace to repository evidence.
- Preserved architecture flexibility through append-only decision history.

### Validation

- Unit and syntax validation commands are recorded in `docs/TESTING.md`.
- Documentation paths and machine-specific path restrictions were checked.

### Result

The documentation system is ready for future factual entries. No benchmark or
real-model performance result has been claimed.

### Next Step

Run the planned detector baseline experiment and record measured results.

## 2026-07-13 — Review SIFT face-recognition research

### Objective

Assess whether the local SIFT paper can inform ProjectBlur recognition and
whitelist experiments.

### Work Completed

- Added a structured local research summary with bibliographic information,
  reported findings, ProjectBlur relevance, limitations, and privacy risks.
- Linked the paper from the research index.
- Added a planned, reproducible SIFT-versus-embedding experiment.

### Key Decisions

- Kept SIFT `Under evaluation`; it is not part of current architecture.
- Prioritized false authorization as a privacy-critical experiment metric.
- Did not transfer historical paper results into ProjectBlur performance claims.

### Validation

- Verified the DOI and abstract-level metadata against an online publication
  record.
- Confirmed that all implementation and benchmark fields remain unmeasured.

### Result

The research can now be reviewed without reopening the PDF, while limitations
of the available review and lack of ProjectBlur benchmarks remain explicit.

### Next Step

Define authorized inputs and a modern embedding baseline before implementing
the experiment.

## 2026-07-13 — Add RetinaFace browser-input web prototype

### Objective

Demonstrate a privacy-first path from an uploaded image, camera, or shared
screen to RetinaFace detection and Gaussian face anonymization.

### Work Completed

- Added reusable, padded Gaussian face blurring with clipped bounding boxes.
- Added bounded in-memory image decoding, mocked detection, and JPEG encoding.
- Added a FastAPI endpoint and responsive single-page browser interface with
  image upload, permission-gated camera capture, and screen sharing.
- Added sequential frame processing, capture resizing, explicit source stop,
  and automatic handling when browser screen sharing ends.
- Disabled RetinaFace's automatic 1024-pixel input upscaling for the web path,
  added 480/640/960 live modes, and displayed measured pipeline FPS.
- Added anonymization and web-processing unit tests.
- Added FastAPI, OpenCV, multipart, Uvicorn, and TensorFlow Keras compatibility
  dependencies.

### Key Decisions

- Blurred every detection because whitelist recognition is not implemented.
- Kept image and captured-frame processing in memory with no intentional
  persistence, and never requested audio capture.
- Used sequential requests to prevent a slow RetinaFace inference backlog.
- Serialized inference in the prototype until backend concurrency is tested.
- Used a static browser client instead of adding the planned React build now.

### Validation

- Twenty-four offline unit tests passed in the project virtual environment.
- `python -m compileall src tests examples` passed.
- FastAPI application import passed.
- Local `/` and `/health` HTTP smoke checks returned status 200.
- Installed environment included `retina-face 0.0.18` and `tf-keras 2.21.0`.
- A local CPU microbenchmark using synthetic blank frames and a warm model took
  21.016 seconds for the previous 960x540 frame with upstream upscaling and
  0.697 seconds for a 640x360 frame without upscaling. This measures inference
  latency only and is not face-detection accuracy or production FPS evidence.
- The real web processing function successfully processed a synthetic 640x360
  JPEG through RetinaFace in 3.475 seconds on its first call, including model
  initialization, and confirmed that upscaling was disabled.

### Result

The upload, camera, and screen-source interface and offline blur pipeline are
implemented. Real RetinaFace inference and browser permission flows were not
run because no authorized face source was supplied, so actual model download,
detection quality, preview latency, and end-to-end face output remain
unverified.

### Next Step

Manually test authorized upload, camera, and screen inputs; record model and
latency observations; and pin compatible dependency versions before designing
the production video path.

## 2026-07-14 — Add and benchmark the OpenVINO RetinaFace backend

### Objective

Preserve the slow TensorFlow result as research evidence and evaluate an
official Open Model Zoo RetinaFace model through OpenVINO.

### Work Completed

- Added detailed TensorFlow and OpenVINO research notes plus machine-readable
  benchmark artifacts.
- Downloaded and converted the official `retinaface-resnet50-pytorch` checkpoint
  to local FP16 OpenVINO IR with recorded hashes.
- Added a separate OpenVINO adapter with fixed model-schema validation,
  preprocessing, anchor decoding, landmarks, NMS, and ProjectBlur normalization.
- Moved the detection schema out of the TensorFlow adapter and made backend
  imports lazy.
- Added a reproducible synthetic backend benchmark and local model-preparation
  script.
- Configured the web prototype to use OpenVINO AUTO by default while retaining
  an explicit TensorFlow fallback.

### Key Decisions

- Did not commit or redistribute model weights.
- Kept the deprecated conversion tools in a separate ignored environment.
- Selected OpenVINO only for continued prototype evaluation; accuracy and
  production selection remain open.
- Did not assume Intel GPU was faster after measurements showed otherwise.

### Validation

- Thirty-three offline unit tests passed.
- The generated IR has input `data` at `1x3x640x640` and the three expected
  outputs at `1x16800x4`, `1x16800x2`, and `1x16800x10`.
- OpenVINO AUTO averaged 6.09 FPS with P95 0.1718 seconds over 30 synthetic
  iterations after three warm-ups.
- TensorFlow averaged 1.47 FPS under the matching corrected 640x360 policy.
- Explicit Intel GPU averaged 1.31 FPS and was slower than AUTO/CPU.
- The complete in-process web function averaged about 5.14 FPS in a separate
  ten-call synthetic check.

### Result

OpenVINO is the current faster web prototype trial backend. No real-face
accuracy, false-negative, browser-permission, or small-face result is claimed.

### Next Step

Use an explicitly authorized face set to compare detection agreement and
privacy-critical misses, then add tracking to bridge detector updates safely.

## 2026-07-14 â€” Add and benchmark the experimental YuNet CPU adapter

### Objective

Test whether a lightweight per-frame detector can fit the 33.3 ms budget for a
30 FPS browser prototype without first introducing detector skipping.

### Work Completed

- Added a ProjectBlur-owned `YuNetDetector` around OpenCV `FaceDetectorYN` with
  validated settings, input handling, bounding boxes, five landmarks, and the
  shared detection schema.
- Added an explicit `PROJECTBLUR_DETECTOR=yunet` web option while retaining
  OpenVINO RetinaFace as the default.
- Added decode, detection, blur, encode, and total server-stage timers plus
  response headers and live status feedback.
- Added a hash-verifying preparation script for the official dynamic-input
  OpenCV 5.x YuNet model; weights remain local and ignored.
- Extended the reproducible benchmark for YuNet adapter and complete-pipeline
  modes at arbitrary synthetic resolutions.
- Added offline adapter and web timing tests, model provenance, a detailed
  experiment record, and a machine-readable artifact.

### Key Decisions

- Used `face_detection_yunet_2026may.onnx` after current upstream documentation
  identified it as the OpenCV 5.x dynamic-input model.
- Preserved the preliminary 2023 model measurement as diagnostic evidence but
  did not select it as the experiment artifact.
- Did not switch the default detector because no authorized face comparison
  exists.
- Did not implement JSON/canvas transport because the existing local HTTP path
  passed the synthetic 30 FPS latency budget; browser evidence comes next.

### Validation

- Forty offline unit tests passed.
- Syntax compilation passed for `src`, `examples`, `benchmarks`, and `tests`.
- `pip check` reported no broken requirements.
- The model preparation script verified 229,738 bytes and SHA-256
  `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0`.
- At 640x360, YuNet adapter mean/P95 were 5.40/6.12 ms and complete-function
  mean/P95 were 6.11/6.92 ms over 30 zero-face calls after three warm-ups.
- A separate local Uvicorn/curl run averaged 8.40 ms with P95 9.20 ms over 30
  sequential requests and returned the expected timing headers.

### Result

YuNet passes the provisional synthetic adapter and server latency gates. This
is not browser FPS or accuracy evidence, and the runtime emitted an OpenCV
new-graph-engine target warning that remains recorded for follow-up.

### Next Step

Run an explicitly authorized 300-frame browser camera or screen test at 640 px.
Record output FPS, detection/server milliseconds, face count, missed faces,
source type, and resolution. Change transport only if that controlled run misses
30 FPS.

## 2026-07-14 â€” Record YuNet screen-share performance observations

### Result

A manual online-video screen-share session confirmed the `opencv-yunet` backend
and continued beyond 4,800 processed iterations. Spot readings at frames 2511,
3670, and 4815 reported 86.2, 74.1, and 78.7 pipeline FPS. Detection ranged from
5.5 to 6.9 ms and server processing from 7.5 to 10.2 ms.

The browser performance gate passes provisionally, so transport replacement is
not currently justified. Accuracy remains pending because visible-face ground
truth, missed/unblurred frames, exact capture setting, browser, and resource use
were not recorded; the zero-face observation at frame 2511 is therefore
unclassified.

## 2026-07-14 - Add automatic browser performance recording

### Objective

Capture short lag spikes and reproducible full-run statistics that cannot be
read reliably from a rapidly changing latest-frame status line.

### Work Completed

- Expanded live timing to cover capture/JPEG, request/response, server work,
  returned-image decode, and one animation-frame boundary.
- Added automatic bounded per-iteration recording for camera and screen sources.
- Added rolling 300-sample and final-run summaries with P95/P99, below-30-FPS
  counts, detector/server P95, zero-face counts, and the 20 slowest frames.
- Added explicit JSON export and reset controls. Metrics remain in browser
  memory and contain no frames, identity data, URLs, or video titles.
- Documented the export schema, interpretation limits, privacy boundary, and
  manual validation procedure.

### Result

The next YuNet browser run can be analyzed from every retained iteration rather
than three manually copied status readings. Because the timing boundary changed,
new exports must be treated as a separate, better-defined follow-up measurement.

## 2026-07-14 - Analyze the first metrics export and remove blocking presentation timing

### Evidence

The first automatic YuNet screen-share export contained 7,898 samples over
219.614 seconds at 640x386. It measured 36.01 FPS overall, 24.2 ms median, 30.2
ms P95, and 36.6 ms P99. Detector/server P95 were 7.215/9.706 ms, and no
iteration over 50 ms was request/server dominated.

Five animation-frame waits consumed 35.592 seconds, including one 26.011 second
wait. Fifteen of the 20 iterations over 50 ms were instead dominated by browser
capture/JPEG. The evidence identifies browser scheduling and capture as the
stall sources; it does not identify a YuNet or server bottleneck.

### Work Completed

- Recorded a derived, privacy-safe result and source-export SHA-256 in the
  existing YuNet benchmark artifact while keeping the 2.65 MB raw export local.
- Advanced browser metrics to schema v2 and removed the blocking
  `requestAnimationFrame` wait from the sequential processing loop.
- Added non-blocking presentation observations, document-visibility events,
  per-sample visibility state, 30-sample warm-up markers, capture-stall markers,
  browser-stage P95 values, and a steady-state summary.
- Updated experiment, architecture, testing, and metric-definition records.

### Remaining Risk

Browsers may still throttle capture or JavaScript in background tabs. The next
manual run must intentionally include a visibility transition and separately
record authorized visible-face ground truth, blur misses/flicker, CPU, and RAM.

## 2026-07-14 - Validate non-blocking metrics during visibility changes

Two schema v2 screen-share sessions recorded 7,425 combined samples. Overall
throughput was 46.986 FPS with 25.9 ms P95. The visible subset achieved 50.324
FPS with 23.9 ms P95. A presentation callback was delayed 3.427 seconds across
a visibility transition but did not block `pipeline_ms`, validating the schema
v2 instrumentation change.

The intentional hidden periods exposed a platform limitation rather than a
server bottleneck. Eight consecutive capture/JPEG iterations took about one
second each during the longest hidden interval, and ten of 16 capture stalls
were hidden. Detector/server P95 remained below 8.4/11.0 ms. The derived result
and source SHA-256 were added to the YuNet benchmark artifact; the 4.72 MB raw
export remains local.

Visible-tab performance now passes with automatic percentile evidence. Face
accuracy, browser version, CPU, RAM, and reliable background execution remain
open requirements.

## 2026-07-15 - Make YuNet the web prototype default

Changed the unset-environment web backend from OpenVINO RetinaFace to YuNet for
prototype responsiveness, based on the recorded EXP-004 browser performance.
OpenVINO remains an explicit `PROJECTBLUR_DETECTOR=openvino` rollback. Updated
startup guidance, configuration examples, architecture/status records, and
offline tests. This does not resolve the pending accuracy or privacy-critical
face-miss evaluation and does not select a production detector.
