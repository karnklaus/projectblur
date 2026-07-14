# YuNet Real-Time Baseline

## Status

Implemented and synthetically benchmarked on 2026-07-14. Adapter, in-process
pipeline, and local HTTP latency gates pass. Browser camera/screen FPS,
authorized face accuracy, resource use, and production suitability remain
unmeasured.

## Question

Can OpenCV YuNet provide a materially faster CPU face-detection path than the
current OpenVINO RetinaFace ResNet50 adapter without introducing unacceptable
privacy-critical missed faces on ProjectBlur's authorized evaluation inputs?

## Why This Is Next

The manual OpenVINO browser preview reported 5.1 FPS on `AUTO` and 5.3 FPS on
explicit `CPU`, both with zero faces blurred. At 5.1 FPS, the full frame path is
approximately 196 ms. The separate OpenVINO adapter benchmark averaged about
164 ms per call, an estimated 84% of the live frame time. These are separate
measurements rather than a controlled component profile, but they show that the
detector is the first bottleneck to test.

## 30 FPS Engineering Budget

Thirty end-to-end output FPS allows approximately 33.3 ms for a complete frame.
The present measurements imply the following rough budget consumption:

| Component estimate | Time |
| --- | ---: |
| Current complete browser round trip at 5.1 FPS | 196.1 ms |
| Current OpenVINO detector mean from a separate run | 164.1 ms |
| Implied capture, JPEG, HTTP, decode, blur, return, and render remainder | about 32.0 ms |

The remainder is derived by subtracting separate measurements, so it is not a
component-level profile. Nevertheless, it shows that replacing the detector is
necessary but may not be sufficient: even a near-zero-cost detector would leave
almost no margin inside the 33.3 ms target with the current full-JPEG round
trip.

For EXP-004, use these provisional engineering gates:

- YuNet adapter P95 at or below 15 ms at the selected live input size.
- Complete server processing P95 at or below 25 ms.
- Browser blurred output sustained at or above 30 FPS for at least 300 frames,
  with source, resolution, device, and face count recorded.
- No detector selection until authorized face misses are measured separately.

These are prototype performance gates, not accuracy claims or production
service-level objectives.

OpenCV describes YuNet as a lightweight face detector and provides maintained
ONNX models plus the `FaceDetectorYN` interface. The official model note reports
WIDER Face results and an approximate trained face-size range of 10x10 through
300x300 pixels. Those upstream results are context only; they do not predict
ProjectBlur performance or privacy behavior on this computer.

The installed project environment has OpenCV 5.0.0 and exposes
`cv2.FaceDetectorYN.create`. This makes a small isolated adapter and controlled
benchmark possible without adding a new runtime dependency. Model weights must
remain local and git-ignored unless redistribution rights and repository policy
are separately confirmed.

## Why Tracking Is Not First

Running RetinaFace every several frames and predicting boxes between detections
could improve displayed FPS, but a new face could enter during a skipped
detection interval. ProjectBlur must define how such a face remains blurred
before using detector skipping as an optimization. A lightweight detector on
every submitted frame tests a safer performance path first. Tracking remains
valuable afterward for stable boxes, temporary occlusion, and cached whitelist
decisions.

## Candidate and Reference

| Role | Detector | Runtime | Initial device |
| --- | --- | --- | --- |
| Reference | RetinaFace ResNet50 FP16 IR | OpenVINO 2026.2.1 | `AUTO` and `CPU` |
| Candidate | YuNet ONNX | OpenCV `FaceDetectorYN` | CPU |

The selected official FP32 model is `face_detection_yunet_2026may.onnx`, which
the current OpenCV Zoo documentation identifies as its dynamic-input OpenCV 5.x
model. Test an official quantized variant only as a separate follow-up so
precision changes are not mixed into the first comparison.

## Synthetic Results

All results use an all-black input containing zero faces, three warm-ups, and
30 sequential measured calls. They measure latency only.

| Path | Resolution | Mean | P95 | Mean throughput |
| --- | --- | ---: | ---: | ---: |
| YuNet adapter | 640x360 | 5.40 ms | 6.12 ms | 185.18 FPS |
| Decode + YuNet + blur + encode | 640x360 | 6.11 ms | 6.92 ms | 163.67 FPS |
| YuNet adapter | 480x270 | 3.21 ms | 4.06 ms | 311.29 FPS |
| Decode + YuNet + blur + encode | 480x270 | 3.62 ms | 4.11 ms | 276.40 FPS |

At 640x360, mean server stages were approximately 0.36 ms decode, 5.18 ms
detection, 0.15 ms blur, and 0.41 ms encode. A separate local Uvicorn/curl
multipart test averaged 8.40 ms, P95 9.20 ms, or 119.02 sequential requests per
second after warm-up. The first request reported 17.66 ms detection and 18.90
ms total server time.

YuNet passes the provisional 15 ms adapter P95 and 25 ms complete-server P95
gates. Exact values and model provenance are saved in
`artifacts/benchmarks/yunet_trial_2026-07-14.json`.

## Manual Screen-Share Results

The backend health endpoint confirmed `opencv-yunet`. A manual screen-share run
used an online vlog/interview video and continued beyond 4,800 processed
iterations. No title, person identity, frame image, or video data was retained.

| Observed frame | Faces blurred | Pipeline FPS | Detection | Server |
| ---: | ---: | ---: | ---: | ---: |
| 2511 | 0 | 86.2 | 5.5 ms | 7.5 ms |
| 3670 | 2 | 74.1 | 6.9 ms | 10.2 ms |
| 4815 | 1 | 78.7 | 6.5 ms | 9.2 ms |

All three spot readings exceed 30 FPS; the lowest was 74.1 FPS and their
arithmetic mean was 79.7 FPS. This provisionally passes the browser performance
gate and does not justify replacing the JPEG transport yet.

This does not pass an accuracy gate. The browser, exact capture setting,
visible-face count, missed or unblurred frames, CPU/RAM use, and whether a face
was visible at frame 2511 were not recorded. In addition, the UI pipeline metric
ends after response blob receipt and image-source assignment; it is not a P95
distribution or proof that every iteration was a unique rendered video frame.

### Automatic Metrics Follow-Up

The first schema v1 automatic screen-share run recorded 7,898 samples over
219.614 seconds with YuNet and a 640x386 captured frame. No samples were dropped.

| Metric | Result |
| --- | ---: |
| Overall throughput | 36.01 FPS |
| Median pipeline | 24.2 ms |
| P95 pipeline | 30.2 ms |
| P99 pipeline | 36.6 ms |
| Samples below 30 FPS | 193 (2.444%) |
| Detector P95 | 7.215 ms |
| Server P95 | 9.706 ms |

The performance gate passes, but the recorder exposed its own presentation
measurement flaw. Five blocking animation-frame waits totaled 35.592 seconds,
including one 26.011 second wait. Of 20 iterations over 50 ms, 15 were dominated
by capture/JPEG and five by presentation waits; none were dominated by the
request/server stage. Excluding iterations over 100 ms gives 43.621 FPS. This
supports keeping the current server transport while investigating browser-side
capture stalls.

Schema v2 no longer awaits an animation-frame callback in the processing loop.
It records presentation delay opportunistically, adds document-visibility
events, marks the first 30 samples as warm-up, marks capture/JPEG work over 50
ms as a stall, and provides a steady-state summary. The raw 2.65 MB export stays
local. Its SHA-256 and derived result are stored in
`artifacts/benchmarks/yunet_trial_2026-07-14.json`. See `docs/METRICS.md`.

## Experiment Procedure

1. Record the exact YuNet model filename, upstream URL, byte size, SHA-256,
   license file, OpenCV version, and detector thresholds.
2. Implement a separate adapter that returns the existing ProjectBlur detection
   schema. Do not modify the RetinaFace adapter.
3. Add mocked offline tests for input validation, bounding boxes, five
   landmarks, confidence, empty detections, and missing model errors.
4. Extend the reproducible benchmark to run both detectors on the same 640x360
   synthetic input with three warm-ups and at least 30 sequential measured
   calls.
5. Record cold, mean, median, P95, minimum, maximum, and FPS. Measure JPEG
   decode, detection, blur, and JPEG encode separately from adapter-only time.
6. Repeat the browser observation with the same input source, capture size,
   duration or frame count, device setting, and no competing workload.
7. With explicitly authorized media, compare both detectors across face-size
   bands, front and difficult poses, occlusion, low light, screen sharing, and
   motion blur. Record every privacy-critical miss rather than only aggregate
   FPS.
8. Record sustained CPU and memory use. Do not include biometric media in logs
   or committed artifacts.

## Evidence Required for a Prototype Switch

- Material adapter and end-to-end latency improvement on this machine.
- Repeated browser measurements rather than one status-line observation.
- Authorized-input detection comparison, especially for small and distant
  faces.
- Explicit thresholds and fail-safe behavior that blurs when uncertain.
- No claim that upstream WIDER Face results equal ProjectBlur accuracy.

Until these conditions are met, OpenVINO RetinaFace remains the web prototype
default and YuNet remains an explicit experiment candidate.

## Ordered Path to 30 FPS

1. Completed: add stage timers and the isolated YuNet adapter, then benchmark it
   without changing the current web default.
2. Completed for performance: run the existing JPEG path for 7,898 automatic
   screen-share samples; overall throughput was 36.01 FPS and P95 was 30.2 ms.
3. Next: repeat with browser, resolution, visible-face ground truth, misses,
   flicker, CPU, and RAM recorded; separately evaluate small/distant faces.
4. Only if a controlled browser path later misses 30 FPS, add a live-only
   endpoint that returns face boxes and landmarks as JSON and render blur on the
   browser canvas with a latest-frame-only detection loop.
5. For any metadata-rendering path, fail safe by blurring the full preview until
   the first valid result and whenever results are stale or detection fails.
6. Report detection-update FPS and displayed-output FPS separately.
7. Only after per-frame lightweight detection is measured, evaluate tracking
   for box stability and temporary occlusion. Do not use tracking to hide a
   detector that misses newly entering faces.
8. If the browser path misses the performance gate despite the measured server
   margin, profile capture, browser JPEG, HTTP, response decode, and rendering
   before changing transport. If YuNet misses the privacy gate, retain RetinaFace
   and evaluate a smaller RetinaFace backbone or a privacy-safe hybrid rather
   than accepting the faster detector by FPS alone.

## Official Sources

- OpenCV Zoo YuNet model documentation and reported evaluation:
  https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- OpenCV `FaceDetectorYN` class reference:
  https://docs.opencv.org/master/df/d20/classcv_1_1FaceDetectorYN.html
- OpenCV Zoo repository and benchmarking context:
  https://github.com/opencv/opencv_zoo

Accessed: 2026-07-14
