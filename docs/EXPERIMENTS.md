# ProjectBlur Experiments

Record only measured values. Use `Not yet measured` when results do not exist.
Inputs must be synthetic, public-domain, or explicitly authorized.

Successful CLI performance runs are saved automatically as immutable,
timestamped JSON files under `artifacts/benchmarks/`. Raw runs are never
rewritten. A paper-facing summary must cite every included source artifact,
state exclusions and aggregation, preserve configuration and environment
metadata, and keep latency, accuracy, browser, and transport experiments
separate unless an integrated procedure measured them together.

## EXP-001 — RetinaFace adapter compatibility baseline

- Date: To be confirmed
- Status: Planned
- Related decision: `DEC-001`
- Related research: `research/external_repositories/retinaface.md`
- Hardware: To be confirmed
- Software environment: Python and `retina-face` versions to be confirmed
- Dataset or test input: Authorized evaluation set to be confirmed

### Objective

Confirm that the adapter works with a pinned published package and establish a
reproducible CPU baseline for later detector comparisons.

### Hypothesis

The adapter will normalize valid RetinaFace output without changes to the
ProjectBlur result contract.

### Compared Approaches

- RetinaFace through `RetinaFaceDetector`
- YuNet baseline implemented separately in `EXP-004`

### Metrics

- Average latency and P95 latency
- FPS under a defined sequential workload
- CPU and memory usage
- Precision, recall, false positives, and false negatives on an authorized set

### Procedure

To be defined with fixed package versions, hardware metadata, warm-up policy,
input resolution, dataset authorization, and benchmark script path before the
experiment starts.

### Results

Not yet measured.

### Interpretation

Not yet measured.

### Conclusion

Need more testing.

### Artifacts

- Script path: To be created
- Config path: To be created if required
- Result file path: `artifacts/benchmarks/` (planned)
- Chart path: `artifacts/charts/` (planned)
- Log path: To be confirmed; logs must contain no biometric data

## EXP-002 — SIFT recognition baseline comparison

- Date: To be confirmed
- Status: Planned
- Related decision: None; no adoption decision has been made
- Related research: `research/papers/sift_features_for_face_recognition/research_note.md`
- Hardware: To be confirmed
- Software environment: To be confirmed
- Dataset or test input: Authorized evaluation set to be confirmed

### Objective

Determine whether aligned SIFT-based matching provides useful accuracy,
privacy-risk, or CPU trade-offs for ProjectBlur compared with a modern
fixed-size face-embedding baseline.

### Hypothesis

SIFT may tolerate limited scale, rotation, and partial occlusion, but its
variable descriptor count may make whitelist matching slower and less scalable.

### Compared Approaches

- Original SIFT matching on aligned face crops
- PDSIFT-inspired boundary handling, if it can be reproduced faithfully
- A modern embedding baseline to be selected

### Metrics

- Average and P95 latency
- CPU and memory usage
- False authorization and false rejection rates
- Robustness across scale, pose, illumination, occlusion, compression, and blur
- Matching cost as whitelist size increases

### Procedure

To be defined before execution. It must fix alignment, crop padding, feature
settings, matching policy, thresholds, hardware, software versions, input
authorization, and warm-up/repetition rules.

### Results

Not yet measured.

### Interpretation

Not yet measured.

### Conclusion

Need more testing.

### Artifacts

- Script path: To be created
- Config path: To be created if required
- Result file path: `artifacts/benchmarks/` (planned)
- Chart path: `artifacts/charts/` (planned)
- Log path: To be confirmed; logs must contain no identity or biometric data

## EXP-003 — TensorFlow and OpenVINO RetinaFace live-backend comparison

- Date: 2026-07-14
- Status: In progress; synthetic latency comparison complete, accuracy pending
- Related decision: `DEC-001`, `DEC-002`
- Related research:
  `research/experiments/retinaface_tensorflow_live_baseline.md`
  and `research/experiments/openvino_retinaface_trial.md`
- Hardware: Windows x64, Intel64 Family 6 Model 151 Stepping 2, 12 logical
  processors; exact retail CPU name not available
- Software environment: Python 3.12.10; package versions recorded in the
  research note and result artifact
- Dataset or test input: Synthetic blank frames for latency diagnostics;
  authorized face evaluation set not yet supplied

### Objective

Determine whether an OpenVINO RetinaFace backend materially improves sustained
live-preview latency while preserving the ProjectBlur detection schema and
acceptable face-detection behavior.

### Compared Approaches

- `retina-face 0.0.18` with TensorFlow 2.21.0
- Open Model Zoo `retinaface-resnet50-pytorch` with OpenVINO 2026.2.1

### Metrics

- Cold-start, warm median, average, and P95 latency
- Sustained sequential FPS at fixed input resolution
- CPU and memory use
- Detection agreement on authorized images
- Small-face and distant-face false negatives
- End-to-end browser pipeline FPS

### Current Results

The 30-iteration fixed-resolution comparison is saved in
`artifacts/benchmarks/retinaface_openvino_trial_2026-07-14.json`. At 640x360,
OpenVINO AUTO averaged 0.1641 seconds (6.09 FPS) with P95 0.1718 seconds.
TensorFlow CPU with upscaling disabled averaged 0.6783 seconds (1.47 FPS) with
P95 0.7117 seconds. OpenVINO GPU was slower than CPU on this machine at 1.31
FPS. Inputs were blank synthetic frames, so these values measure latency only.

A same-machine repeat on 2026-07-17 used the same 640x360 all-black input,
three warm-ups, and 30 sequential adapter calls. The exact console results were
preserved in
`artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`:

| Backend | Device | Mean latency | P95 latency | Mean throughput |
| --- | --- | ---: | ---: | ---: |
| YuNet | CPU | 4.571 ms | 5.007 ms | 218.784 FPS |
| OpenVINO RetinaFace | AUTO | 154.133 ms | 172.779 ms | 6.488 FPS |
| TensorFlow RetinaFace | CPU | 557.959 ms | 611.162 ms | 1.792 FPS |

By mean latency, OpenVINO was 33.72 times slower than YuNet, TensorFlow was
122.07 times slower than YuNet, and TensorFlow was 3.62 times slower than
OpenVINO in this repeat. Only YuNet stayed below the 33.333 ms mean frame
budget corresponding to 30 FPS. This is a repeated latency ranking, not a
detector-accuracy or end-to-end product result.

After automatic recording was implemented, a second sequential repeat on the
same date verified that each backend produced its own immutable raw record:

| Backend | Device | Mean latency | P95 latency | Mean throughput |
| --- | --- | ---: | ---: | ---: |
| YuNet | CPU | 5.130 ms | 6.389 ms | 194.919 FPS |
| OpenVINO RetinaFace | AUTO | 161.243 ms | 173.093 ms | 6.202 FPS |
| TensorFlow RetinaFace | CPU | 579.648 ms | 609.054 ms | 1.725 FPS |

The run order was YuNet, OpenVINO, then TensorFlow; no randomized order,
cooldown, CPU utilization, or thermal state was recorded. These files verify
recording and provide additional raw observations, but should not be used as a
formal multi-run statistical comparison until the paper protocol defines
repetition, ordering, and aggregation:

- `artifacts/benchmarks/projectblur_detector_yunet_adapter_cpu_20260716T191400.616166Z.json`
- `artifacts/benchmarks/projectblur_detector_openvino_adapter_auto_20260716T191401.197728Z.json`
- `artifacts/benchmarks/projectblur_detector_tensorflow_adapter_cpu_20260716T191407.639099Z.json`

Manual browser observations reported 5.1 pipeline FPS at frame 367 with the
default `AUTO` setting and 5.3 pipeline FPS at frame 84 with explicit `CPU`;
both runs reported zero faces blurred. Because the run lengths and other test
conditions were not controlled, this only supports treating `AUTO` and `CPU`
as practically similar pending a repeated benchmark.

A later 480-pixel capture observation reported 5.5 pipeline FPS at frame 56
with zero faces blurred. Its device setting was not recorded, so the roughly
7.8% increase over 5.1 FPS is not a controlled resolution comparison. It is
consistent with smaller capture and JPEG overhead while RetinaFace inference
continues at the fixed 640x640 model shape.

### Remaining Procedure

1. Run detection agreement and privacy-critical false-negative tests only on an
   explicitly authorized face set.
2. Measure CPU and memory utilization under sustained browser input.
3. Add tracking and define safe behavior when a detection becomes stale.
4. Select or reject a production detector only after comparable accuracy and
   latency results exist.

### Artifacts

- TensorFlow diagnostic:
  `artifacts/benchmarks/retinaface_tensorflow_live_baseline_2026-07-14.json`
- OpenVINO comparison:
  `artifacts/benchmarks/retinaface_openvino_trial_2026-07-14.json`
- Same-machine three-backend repeat:
  `artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`
- Automatic-recording verification runs: the three timestamped detector files
  listed above
- Reproducible script: `benchmarks/retinaface_backend_benchmark.py`

## EXP-004 — YuNet CPU real-time baseline

- Date proposed: 2026-07-14
- Status: In progress; latency and browser-performance gates pass, accuracy pending
- Reference: OpenVINO RetinaFace ResNet50 on `AUTO` and explicit `CPU`
- Candidate: OpenCV YuNet through `cv.FaceDetectorYN`
- Detailed plan: `research/experiments/yunet_realtime_baseline_plan.md`

### Objective

Determine whether a lightweight detector can remove the dominant per-frame
inference bottleneck while continuing to detect on every submitted frame. Do
not select a production detector from latency alone.

### Required Measurements

1. Run the same cold-start, warm-up, mean, median, P95, minimum, maximum, and
   throughput procedure used by EXP-003.
2. Measure the complete server function and manual browser pipeline using a
   fixed source, resolution, run length, and device setting.
3. Compare detections on explicitly authorized faces grouped by approximate
   face size, pose, occlusion, lighting, and motion blur.
4. Record CPU and memory use under sustained input.
5. Treat missed faces as privacy-critical and retain blur-by-default behavior
   whenever detection or later tracking is uncertain.

### Selection Rule

YuNet may become the live prototype candidate only if it materially improves
latency and its authorized-input face misses are understood and acceptable for
the prototype. RetinaFace remains the reference. Tracking is evaluated after
this comparison because detector skipping needs an explicit new-face and
stale-track privacy policy.

### 30 FPS Checkpoints

The first implementation checkpoint is an isolated YuNet adapter with stage
timing. The provisional targets are adapter P95 at or below 15 ms, complete
server processing P95 at or below 25 ms, and at least 30 browser output FPS for
300 controlled frames. If detector latency passes but the JPEG round trip does
not, the next checkpoint returns detection metadata and performs blur rendering
on the browser canvas with latest-frame dropping and full-frame fail-safe blur
for missing or stale results. Detection-update FPS and displayed-output FPS must
be reported separately.

### Current Results

The official dynamic-input `face_detection_yunet_2026may.onnx` model was tested
through OpenCV 5.0.0 on CPU with all-black, zero-face inputs. After three
warm-ups, 30 measured 640x360 adapter calls averaged 5.40 ms with P95 6.12 ms
(185.18 FPS). The complete decode, detection, blur, and encode function averaged
6.11 ms with P95 6.92 ms (163.67 FPS).

The 2026-07-17 same-machine adapter repeat averaged 4.571 ms with P95 5.007 ms
(218.784 FPS). Its OpenVINO and TensorFlow comparison results are tabulated in
`EXP-003` and preserved with the exact YuNet values in
`artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`. The
repeat confirms the latency ranking but does not replace the separate initial
pipeline measurement or provide accuracy evidence.

At 480x270, adapter mean/P95 were 3.21/4.06 ms and complete-function mean/P95
were 3.62/4.11 ms. A separate 30-request local Uvicorn/curl test at 640x360
averaged 8.40 ms with P95 9.20 ms (119.02 requests per second). Every input
contained zero faces, so none of these values measure detection accuracy or the
cost of blurring real face regions.

The adapter and server latency gates pass. The existing JPEG transport remains
unchanged. A manual screen-share run continued beyond frame 4,800 and reported
three spot readings of 86.2, 74.1, and 78.7 pipeline FPS, with 0, 2, and 1 faces
blurred respectively. Detection was 5.5–6.9 ms and server time was 7.5–10.2 ms.
This provisionally passes the browser performance gate.

The result does not pass an accuracy gate because browser, exact resolution,
visible-face ground truth, missed/unblurred frames, and CPU/RAM use were not
recorded. In particular, the zero-face result at frame 2511 cannot be classified
as correct or as a privacy-critical miss. OpenVINO RetinaFace remains the
default until authorized face misses and small-face behavior are evaluated.

A later automatic schema v1 screen-share run recorded 7,898 samples over
219.614 seconds at a 640x386 capture size. Overall throughput was 36.01 FPS;
median/P95/P99 processing times were 24.2/30.2/36.6 ms, and 2.444% of samples
exceeded the 33.333 ms budget. Detector and server P95 were 7.215 and 9.706 ms.
No iteration over 50 ms was request/server dominated, so the current evidence
does not justify changing the JPEG transport to improve this performance case.

The run also exposed an instrumentation problem: five blocking
`requestAnimationFrame` waits consumed 35.592 seconds, including one 26.011
second wait. Fifteen of the remaining 20 iterations over 50 ms were dominated
by capture/JPEG. These stalls explain the visible pauses without implicating
YuNet. The raw 2.65 MB export remains local; its SHA-256 and derived summary are
stored in `artifacts/benchmarks/yunet_trial_2026-07-14.json`.

### Instrumentation Follow-Up

The browser records every retained live iteration automatically, up to 50,000
samples per session. Schema v2 measures the blocking processing path through
returned-image decode but observes animation-frame presentation callbacks
without awaiting them. It adds visibility events, 30-sample warm-up markers,
capture-stall markers, and a steady-state summary. This prevents the metrics
recorder itself from freezing the sequential loop when a tab is hidden.

Schema v1 and v2 processing values must not be combined into one distribution.
The first automatic run remains useful evidence because its per-stage values
show exactly which waits were browser-side.

On 2026-07-16 the live preview advanced to schema v3: the server returns face
boxes and the browser renders a source-resolution canvas instead of decoding a
returned JPEG. New v3 measurements must be analyzed separately from the v1/v2
results below.

Two schema v2 sessions then recorded 7,425 combined samples. Combined processing
throughput was 46.986 FPS with 19.5/25.9/35.8 ms median/P95/P99. Across 6,362
visible samples, throughput was 50.324 FPS with 23.9 ms P95. A deliberately
hidden session recorded a 3.427 second presentation-callback delay without
blocking the processing metric, confirming that the schema v2 change worked.

Background execution remains limited by browser policy. During the longest
hidden interval, eight consecutive capture/JPEG calls took approximately one
second each. Ten of 16 capture stalls occurred while hidden. Detector/server
P95 stayed below 8.4/11.0 ms in both sessions. Therefore, visible-tab web
performance passes; reliable background processing is not established and
would require a separately evaluated worker/media pipeline or a non-browser
runtime. Accuracy remains pending.

### Artifacts

- Machine-readable results:
  `artifacts/benchmarks/yunet_trial_2026-07-14.json`
- Same-machine three-backend repeat:
  `artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`
- Adapter and benchmark interpretation:
  `research/experiments/yunet_realtime_baseline_plan.md`
- Model provenance: `research/external_repositories/yunet.md`
- Reproducible script: `benchmarks/retinaface_backend_benchmark.py`

## EXP-005 — Full-resolution anonymization and Windows virtual-camera output

- Date proposed: 2026-07-16
- Status: In progress; native synthetic output checkpoint complete, authorized
  capture and application trials pending
- Related decisions: `DEC-006`, `DEC-008`
- Inputs: explicitly authorized webcam and screen sources; synthetic frames for
  offline protocol tests

### Objective

Determine whether reduced-resolution detection can drive privacy-safe blur on
full-resolution frames and sustain a ProjectBlur-owned Windows 11 virtual
camera without a browser JPEG output round trip.

### Required Measurements

- 1280x720 and 1920x1080 output FPS plus median/P95 end-to-end latency.
- Capture, resize, detection, coordinate mapping, blur, publish, native read,
  pixel conversion, and Media Foundation delivery time.
- CPU, memory, shared-memory bandwidth, dropped frames, and stale-frame events.
- Detection misses and blur flicker for authorized webcam and screen inputs.
- Enumeration and sustained streaming in Windows Camera, Zoom, Meet, and Teams.

### Current Results

Seven offline tests validate full-resolution coordinate mapping and the
latest-only BGRA shared-memory contract. A C++ layout check confirms the native
header is 56 bytes with the sequence field at byte 16. A synthetic 4x3 BGRA
frame crossed from the Python publisher to the native Windows mapping reader
with matching sequence, dimensions, and 48-byte payload. The official
Microsoft Virtual Camera sample built with Visual C++ 19.44 and Windows SDK
10.0.26100.

The live browser now freezes a source-resolution frame, sends only a reduced
JPEG to `/api/detect`, receives bounding boxes, and blurs those regions on a
source-resolution canvas. Automated tests cover the detection-only response and
the legacy JPEG endpoint. Authorized visual comparison and schema v3 browser
performance measurements remain pending.

The ProjectBlur x64 Media Foundation source, registrar, build/install/remove
scripts, fail-black source behavior, and synthetic publisher benchmark are now
implemented. On Windows 11 build 26200, the camera registered as `ProjectBlur
Camera (Windows Virtual Camera)` and streamed through an actual Media Foundation
source reader. The first 720p trial exposed 15.6 ms `Sleep` granularity: total
delivery stayed at 30.1 FPS but 41 of 301 source frames were not observed and 41
samples were duplicates. Replacing that pacing with a high-resolution waitable
timer removed the issue in the repeated trials below.

| Output | Delivered | Unique / samples | Missing / duplicate / fallback | Publish mean / P95 | Read P95 | Frame-age P95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1280x720 BGRA to NV12 | 30.1 FPS | 301 / 301 | 0 / 0 / 0 | 0.307 / 0.353 ms | 34.177 ms | 95.144 ms |
| 1920x1080 BGRA to NV12 | 30.1 FPS | 301 / 301 | 0 / 0 / 0 | 0.734 / 0.867 ms | 34.610 ms | 105.380 ms |

Each measured interval was 10 seconds after 1.5 seconds of warm-up. The Python
publisher achieved approximately 30.0 FPS in both runs. Using the earlier 45.1
FPS browser log only as an optional serial-cost baseline, the measured publish
copy estimates 44.48 FPS at 720p (1.37% reduction) and 43.65 FPS at 1080p
(3.20% reduction). Those two values are calculations, not integrated detector
measurements. The virtual camera itself is intentionally capped at 30 FPS.

The benchmark uses only generated BGRA pixels and does not establish detection
accuracy, blur safety, CPU/RAM usage, webcam/screen ingestion, browser
integration, release signing, or compatibility with Camera, Zoom, Meet, or
Teams. The machine-readable results are
`artifacts/benchmarks/projectblur_virtual_camera_720p_2026-07-16.json` and
`artifacts/benchmarks/projectblur_virtual_camera_1080p_2026-07-16.json`.

A 2026-07-17 720p automatic-recording verification repeated the 1.5-second
warm-up and 10-second measurement. It delivered 301 samples at 30.1 FPS with
301 unique source frames and zero unobserved, duplicate, or fallback samples.
Publisher mean/P95 were 0.364/0.806 ms, native read P95 was 36.505 ms, and frame
age P95 was 100.599 ms. The immutable raw record, including installed DLL hash
and Git/environment provenance, is
`artifacts/benchmarks/projectblur_virtual_camera_1280x720_30fps_20260716T191552.660919Z.json`.
This repeat validates the automatic recorder and transport behavior only; its
publish timing does not replace a pre-defined multi-run aggregate.

### Selection Rule

The native output may be described only as an installed synthetic prototype.
Do not describe the integrated anonymization product as ready until removal,
authorized sustained capture, detector-failure handling, application
compatibility, and release-signature validation pass. Performance alone cannot
establish privacy safety.
