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

Unset `PROJECTBLUR_DETECTOR` or set it to `openvino`. The existing default and
RetinaFace code path are unchanged.

### Superseded By

None.

## Decisions Awaiting Evidence

Primary detector, tracker, embedding model, frame transport, detection interval,
anonymization technique, whitelist threshold, web stack, codec fallback, and
virtual-camera implementation remain `Proposed` only when a complete decision
record is added with evidence. They are not accepted decisions today.
