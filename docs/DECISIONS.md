# ProjectBlur Decision Records

Create a new record when a decision changes. Mark the old record `Superseded`
and link the replacement; never delete historical rationale.

## DEC-001 — Isolate external detectors behind adapters

- Date: 2026-07-13
- Status: Accepted
- Related modules: `src/projectblur/detection`
- Related research: `research/external_repositories/retinaface.md`
- Related experiment: `EXP-001`

### Context

ProjectBlur needs to evaluate third-party face detectors without mixing their
source code or result formats into business logic.

### Options Considered

1. Copy detector repository source into ProjectBlur.
2. Call each detector directly throughout the application.
3. Use published packages through ProjectBlur-owned adapters.

### Decision

Use published external packages behind adapters in the detection module.

### Rationale

Adapters preserve attribution, limit coupling, normalize outputs, and allow a
detector to be replaced after evidence-based evaluation.

### Consequences

#### Positive

- External code remains separate and replaceable.
- Validation and error behavior can be tested without model inference.

#### Negative

- Each detector needs maintained mapping and compatibility tests.
- Package behavior and model assets still require integration validation.

### Validation Criteria

- Unit tests cover input and result normalization without network access.
- A real-model integration test confirms compatibility with a pinned version.
- A detector replacement does not require business-logic changes.

### Superseded By

None.

## DEC-002 — Use FastAPI for the browser-input blur prototype

- Date: 2026-07-13
- Status: Accepted for prototype scope
- Related modules: `src/projectblur/web`, `src/projectblur/anonymization`
- Related research: `research/external_repositories/retinaface.md`
- Related experiment: `EXP-001`

### Context

ProjectBlur needs a minimal interface that demonstrates the implemented
RetinaFace adapter and privacy-first blurring for images and browser-captured
frames without prematurely building the planned video architecture or React
application.

### Options Considered

1. Build FastAPI with a small server-rendered browser interface.
2. Add Flask as an alternative web framework.
3. Build the planned FastAPI and React stack immediately.

### Decision

Use FastAPI with a static HTML/JavaScript page for bounded image requests. The
page may capture a camera or shared screen through permission-gated browser APIs
and send frames sequentially through the same endpoint. Keep detection and
anonymization in reusable Python modules.

### Rationale

FastAPI was already the planned backend candidate, supports typed upload
validation, and allows a working web demonstration without adding a separate
frontend build system. The smaller scope limits architectural commitment.

### Consequences

#### Positive

- Demonstrates upload or browser capture, detection, blur, and response behavior
  end to end.
- Does not intentionally retain uploaded biometric media.
- Keeps UI, inference adapter, and anonymization responsibilities separate.

#### Negative

- TensorFlow/RetinaFace startup is heavy for a small prototype.
- Camera and screen preview uses repeated JPEG requests; inference concurrency,
  production streaming, authentication, and deployment hardening are not solved.
- Disabling upstream input upscaling improves latency but may reduce detection
  of small or distant faces; selectable live resolutions expose this prototype
  tradeoff for measurement.
- The static page is not evidence that React is the correct final frontend.

### Validation Criteria

- Offline tests mock RetinaFace inference and require no model download.
- The application and health endpoint start in the project virtual environment.
- Authorized manual testing confirms uploaded and browser-captured faces are
  detected and blurred, and media tracks stop when requested.

### Superseded By

None.

## DEC-003 — Use OpenVINO RetinaFace as the web prototype trial backend

- Date: 2026-07-14
- Status: Accepted for prototype latency evaluation; not a production detector
- Related modules: `src/projectblur/detection`, `src/projectblur/web`
- Related research: `research/experiments/openvino_retinaface_trial.md`
- Related experiment: `EXP-003`

### Context

The corrected TensorFlow RetinaFace path averaged 1.47 FPS at 640x360 in a
30-iteration synthetic sequential benchmark. ProjectBlur needs a more responsive
backend without discarding the RetinaFace evaluation path or coupling business
logic to one runtime.

### Options Considered

1. Keep TensorFlow RetinaFace as the web default.
2. Replace RetinaFace with an unrelated lightweight detector immediately.
3. Add the official Open Model Zoo RetinaFace model through a separate OpenVINO
   adapter and compare both under the same synthetic workload.

### Decision

Use OpenVINO RetinaFace with device `AUTO` as the default web prototype trial.
Keep TensorFlow available only through explicit configuration. Do not silently
fallback between runtimes, and do not claim production or accuracy selection.

### Rationale

OpenVINO AUTO averaged 6.09 FPS with P95 latency 0.1718 seconds, compared with
TensorFlow's 1.47 FPS and P95 0.7117 seconds at the same 640x360 synthetic input.
The adapters share a ProjectBlur-owned schema and can be compared or rolled
back independently.

### Consequences

#### Positive

- The synthetic adapter workload is approximately 4.13 times faster by mean
  throughput.
- TensorFlow is not imported when the OpenVINO backend is selected.
- OpenVINO can choose a suitable available device while explicit CPU/GPU
  configuration remains possible.

#### Negative

- The model requires a local download and conversion step.
- The legacy conversion toolchain is large and deprecated, so it is isolated
  from production dependencies.
- No authorized face dataset has validated detection agreement or small-face
  safety.
- The measured rate is still far below the unverified 30 FPS target.

### Validation Criteria

- Offline tests cover preprocessing, output schema, prior generation, decoding,
  non-maximum suppression, and missing-model errors.
- Local IR input/output names and shapes match the documented model.
- A reproducible benchmark records cold, mean, median, P95, minimum, maximum,
  and FPS for each backend/device.
- Authorized face tests must pass before any production detector decision.

### Rollback

Set `PROJECTBLUR_DETECTOR=tensorflow` to use the reference backend explicitly.
This is a diagnostic rollback, not an automatic failure fallback.

### Superseded By

None.

## DEC-004 â€” Add YuNet as an explicit experimental CPU detector

- Date: 2026-07-14
- Status: Accepted for experimental evaluation; not the default or production detector
- Related modules: `src/projectblur/detection`, `src/projectblur/web`
- Related research: `research/external_repositories/yunet.md`
- Related experiment: `EXP-004`

### Context

OpenVINO RetinaFace averaged about 164 ms per synthetic adapter call and the
manual browser preview reported about 5 FPS. ProjectBlur's unverified target is
30 end-to-end output FPS, while privacy-sensitive face misses remain a separate
selection constraint.

### Options Considered

1. Optimize JPEG transport while retaining a 164 ms every-frame detector.
2. Skip RetinaFace frames and add tracking before defining new-face fail-safe behavior.
3. Add a lightweight detector behind the existing adapter boundary, measure it,
   and retain RetinaFace as the default until accuracy evidence exists.

### Decision

Add OpenCV YuNet as an explicit `PROJECTBLUR_DETECTOR=yunet` experiment backend.
Keep OpenVINO RetinaFace as the default. Add server-stage timing and use the
existing JPEG path for the first controlled browser trial because synthetic
YuNet HTTP latency is already below the 30 FPS budget.

### Rationale

The dynamic-input OpenCV 5.x YuNet model produced 640x360 adapter P95 6.12 ms,
complete-function P95 6.92 ms, and local HTTP P95 9.20 ms on zero-face synthetic
input. These pass the provisional performance gates without introducing
detector skipping. They do not establish accuracy or privacy suitability.

### Consequences

#### Positive

- The experiment reuses the existing OpenCV dependency and detection schema.
- Model weights remain local, git-ignored, and hash-verified.
- RetinaFace, TensorFlow, and YuNet can be selected without business-logic changes.
- Per-stage headers make the next browser result easier to diagnose.

#### Negative

- A third adapter and model artifact require maintenance.
- YuNet thresholds and face misses are not calibrated for ProjectBlur.
- OpenCV emitted a new-graph-engine target warning during inference.
- Browser FPS, resource use, and real-face blur cost remain unmeasured.

### Validation Criteria

- Offline tests mock model inference and validate the documented 15-value schema.
- The downloaded model hash and OpenCV version are recorded.
- Synthetic adapter, server-function, and HTTP results are reproducible.
- A 300-frame authorized browser trial and face-size comparison must pass before
  any default-detector change.

### Rollback

At the time of this decision, unsetting `PROJECTBLUR_DETECTOR` or setting it to
`openvino` retained the RetinaFace path. After `DEC-005`, rollback requires the
explicit value `PROJECTBLUR_DETECTOR=openvino`.

### Superseded By

`DEC-005` supersedes only the web prototype default. YuNet remains under
evaluation for production use.

## DEC-005 — Make YuNet the performance-oriented web prototype default

- Date: 2026-07-15
- Status: Accepted for the web prototype; production detector selection remains pending
- Related modules: `src/projectblur/web`, `src/projectblur/detection`
- Related experiment: `EXP-004`
- Supersedes: `DEC-004` only for the prototype default

### Context

The OpenVINO RetinaFace browser path sustained roughly 4–6 FPS in local trials.
YuNet passed the provisional latency gates and two schema v2 sessions measured
46.986 FPS overall and 50.324 FPS for visible-tab samples. Authorized
face-detection accuracy, small-face misses, CPU, and RAM remain unmeasured.

### Decision

Use YuNet when `PROJECTBLUR_DETECTOR` is unset so the browser prototype is
responsive by default. Keep OpenVINO RetinaFace available explicitly through
`PROJECTBLUR_DETECTOR=openvino`. Treat this as a performance-oriented prototype
choice, not a production or privacy-safety selection.

### Consequences

- New clones prepare the smaller YuNet model for the default path.
- The default preview meets the provisional browser performance gate on the
  measured machine.
- Accuracy limitations must remain visible in user and presentation records.
- Existing deployments that require RetinaFace must set the backend explicitly.

### Validation Criteria

- Unit tests verify YuNet is the unset-environment default.
- Unit tests verify OpenVINO remains an explicit rollback with device metadata.
- The full offline suite and Python syntax validation pass.

### Migration and Rollback

Prepare YuNet with `scripts/prepare_yunet.ps1` before starting a new clone.
Set `PROJECTBLUR_DETECTOR=openvino` and prepare the OpenVINO model to roll back.
No detector failure triggers a silent fallback.

### Superseded By

None.

## DEC-006 — Use a ProjectBlur-owned Windows 11 Media Foundation virtual camera

- Date: 2026-07-16
- Status: Accepted architecture; native prototype implemented
- Related modules: `src/projectblur/pipeline`, `native/virtual_camera`
- Related experiment: `EXP-005`
- Supersedes: the unevaluated `pyvirtualcam` direction for the Windows prototype

### Context

The browser prototype detects and blurs a reduced JPEG frame, then returns a
second JPEG as its output. Enlarging that frame reduces visible quality, and a
browser preview cannot be selected as a camera by conferencing applications.
The product requirement is to support both physical-camera and screen-capture
inputs without depending on OBS or another virtual-camera product.

Microsoft supports user-mode software virtual cameras through
`MFCreateVirtualCamera` on Windows build 22000 and newer. The reviewed official
Virtual Camera sample built successfully with Visual C++ 19.44 and Windows SDK
10.0.26100 on the development machine. This proves toolchain compatibility,
not ProjectBlur virtual-camera functionality.

### Decision

Target Windows 11 first. Capture a full-resolution physical-camera or screen
frame in a desktop ingestion process, create a reduced copy for detection,
scale detections back to source coordinates, blur the full-resolution frame,
and publish latest-only BGRA frames through a versioned shared-memory contract.
A ProjectBlur-owned Media Foundation custom media source will read that mapping
and expose one anonymized virtual camera through `MFCreateVirtualCamera`.

Keep virtual-camera access current-user scoped. `DEC-008` refines the COM
registration boundary after implementation showed that Windows Camera Frame
Server cannot activate an HKCU-only COM server. Do not implement a kernel-mode
camera driver, depend on OBS, or send full-resolution JPEG frames through the
browser round trip. Keep the existing FastAPI browser prototype available
until the native path passes its validation gates.

### Benefits and Trade-offs

- Full-resolution pixels outside blurred regions avoid browser JPEG
  downscaling and re-encoding.
- Webcam and screen capture share one detector/anonymizer/output boundary.
- The latest-only mapping prevents an output backlog.
- Windows 10 is not supported by the first implementation.
- A native COM media source, registration, installer, and release-signing
  process add substantial maintenance and security review.
- BGRA frame transport costs memory bandwidth and requires measurement before
  selecting 720p, 1080p, frame rate, or an NV12 conversion boundary.

### Migration

1. Introduce the high-resolution frame processor without changing the browser
   endpoint.
2. Validate the Python/native shared-memory header and latest-frame semantics.
3. Add the Media Foundation source and registrar behind explicit start/stop
   commands, following the elevation boundary in `DEC-008`.
4. Add desktop webcam and Windows Graphics Capture ingestion.
5. Make the web interface a control/preview surface only after native output
   passes compatibility, privacy, and performance tests.

### Rollback

Stop and remove the current-user-access virtual camera, unregister the
ProjectBlur machine COM CLSID, close its shared memory, and continue using the
existing FastAPI browser prototype. No existing endpoint or detector adapter
is removed by the migration.

### Validation Criteria

- Offline tests prove detection coordinates map back to the source frame while
  unaffected pixels retain their original resolution.
- Python and native code agree on header size, offsets, pixel format, sequence,
  dimensions, stride, timestamp, and payload size.
- The ProjectBlur camera registers and removes cleanly and streams in Windows
  Camera plus the named conferencing applications.
- Stale or invalid input produces a documented fail-closed frame rather than a
  raw or previously authorized image.
- Authorized 720p and 1080p trials record output FPS, P95 latency, CPU, memory,
  missed faces, blur flicker, and input type separately.

### Superseded By

`DEC-008` supersedes only the current-user COM registration detail; the chosen
Media Foundation architecture remains accepted.

## DEC-007 — Render live browser anonymization at source resolution

- Date: 2026-07-16
- Status: Accepted and implemented for the browser prototype
- Related modules: `src/projectblur/web`, `tests/web`
- Related experiments: `EXP-004`, `EXP-005`
- Complements: `DEC-006`

### Context

The original live browser path reduced the captured frame, encoded it as JPEG,
sent it through `/api/blur`, and displayed a second server-encoded JPEG. Even
when detection was fast, enlarging that returned frame reduced detail across
the entire preview. ProjectBlur already had evidence and offline primitives for
detecting on a reduced copy and mapping boxes to a source-resolution frame.

### Decision

Keep one source-resolution canvas for the exact captured frame and create a
separate reduced JPEG only for detector input. Add `/api/detect`, which returns
the detector-frame dimensions, face count, and bounding boxes without returning
an image, landmarks, or confidence scores. Scale the boxes in the browser and
apply the selected padding and blur to the matching source-resolution output
canvas. Process requests sequentially so a response cannot be applied to a
different frame.

Retain `/api/blur` for backward-compatible in-memory image/frame processing.
The browser remains a preview surface and does not become a virtual camera.

### Benefits and Trade-offs

- Pixels outside anonymized regions avoid the server output JPEG re-encode.
- The response payload is coordinates rather than a complete image.
- Freezing one source frame per request keeps detection coordinates aligned.
- Full-resolution browser canvases increase client memory and render work.
- Face regions are blurred on a hidden canvas and published to the visible
  canvas only after rendering succeeds; filtering is cropped to each padded
  region instead of re-filtering the complete frame.
- Canvas blur and OpenCV Gaussian blur are not pixel-identical and need visual
  privacy validation on authorized faces.
- Browser scheduling and background throttling limitations remain.

### Migration and Rollback

Metrics advance to schema v3 because returned-image decode becomes
source-resolution canvas render. Schema v2 measurements remain historical and
must not be combined with v3. Rollback changes the live client to `/api/blur`;
the legacy endpoint and tests remain available.

### Validation Criteria

- Offline tests prove `/api/detect` returns dimensions and boxes without image
  bytes or extra landmark/confidence data.
- Client JavaScript parses successfully and metrics expose `render_ms`.
- Authorized manual camera and screen trials verify box alignment, blur
  coverage, unchanged non-face detail, and sustained schema v3 performance.
- A detected face must never be rendered unblurred merely because local canvas
  rendering fails; fail-closed behavior remains required before production.

### Superseded By

None.

## DEC-008 — Use machine-visible COM with current-user camera access

- Date: 2026-07-16
- Status: Accepted and implemented for the Windows prototype
- Related modules: `native/virtual_camera`, `scripts`
- Related experiment: `EXP-005`
- Refines: `DEC-006`

### Context

The first registrar wrote the ProjectBlur media-source CLSID only under HKCU.
`MFCreateVirtualCamera` succeeded, but `IMFVirtualCamera::Start` rolled back with
`0x80070003`; Frame Server telemetry showed source initialization with zero
streams. A direct in-process COM probe activated the same DLL and returned one
stream, isolating the failure to the service boundary. Registering the CLSID
under HKLM made the camera enumerable. Leaving the DLL under the user's Desktop
then caused Frame Server activation to fail with `0x80070005`; installing it
under Program Files resolved the service-read boundary.

### Decision

Keep `MFVirtualCameraAccess_CurrentUser`, so only the installing account can
enumerate and activate its ProjectBlur camera. Register only ProjectBlur's
media-source CLSID machine-wide and install the DLL plus control executable
under `C:\Program Files\ProjectBlur\VirtualCamera`. Require explicit UAC for
installation and removal. Do not install a kernel driver or third-party virtual
camera.

The media source creates `Global\ProjectBlurFrame-<user SID>` with a protected
DACL limited to LocalSystem, LocalService, and that user. It accepts only the
versioned BGRA protocol, supports 720p/1080p NV12 or RGB32 at 30 FPS, and emits
black output when the frame is missing, stale beyond 500 ms, malformed, or the
wrong size. It never falls back to an unblurred physical source.

### Benefits and Trade-offs

- Camera enumeration stays per-user while the out-of-process Frame Server can
  resolve and load the COM media source.
- Program Files provides an appropriate service-readable deployment location.
- Installation and updates require administrator approval and briefly restart
  Windows Camera Frame Server when replacing an in-use DLL.
- The current development DLL is unsigned; release signing and installer
  hardening remain mandatory before distribution.
- Machine COM visibility increases review scope even though the camera device
  remains current-user scoped.

### Migration and Rollback

Build with `scripts/build_virtual_camera.ps1`, then run
`scripts/install_virtual_camera.ps1` elevated. The installer replaces the two
native binaries, removes any stale user-level CLSID override, registers the
machine CLSID, and starts the current-user camera. Roll back by running
`scripts/remove_virtual_camera.ps1` elevated; this removes the virtual device
and ProjectBlur COM registration without changing the FastAPI prototype.

### Validation Criteria

- Direct COM source probe returns one stream.
- The camera enumerates as `ProjectBlur Camera (Windows Virtual Camera)`.
- A no-publisher probe sustains black fallback output.
- Synthetic 720p and 1080p trials sustain 30 FPS with no duplicate, missing,
  stale, or fallback frames after warm-up.
- Removal leaves neither the camera device nor ProjectBlur CLSID registered.
- Target application compatibility and release-signature validation remain
  required before release.

### Superseded By

None.

## Decisions Awaiting Evidence

Primary detector, tracker, embedding model, frame transport, detection interval,
anonymization technique, whitelist threshold, web stack, codec fallback, and
virtual-camera release packaging remain `Proposed` only when a complete
decision record is added with evidence. They are not accepted decisions today.
