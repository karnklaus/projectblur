# ProjectBlur Milestones

## M1 — Project foundation

- Status: Current (partially complete)
- Completed date: Not complete
- Deliverables: repository guidance, context, architecture, testing, research,
  task, decision, experiment, and presentation documentation
- Evidence: `AGENTS.md`, `PROJECT_CONTEXT.md`, `ARCHITECTURE.md`, `docs/`

## M2 — Face detection baseline

- Status: Current (partially complete)
- Deliverables: TensorFlow and OpenVINO RetinaFace adapters, experimental YuNet
  adapter, mocked tests, CLI example, model-preparation scripts, and synthetic
  benchmark
- Selected approach: YuNet is the performance-oriented web prototype default;
  OpenVINO RetinaFace remains a reference and production
  detector is not selected
- Benchmark summary: the 2026-07-17 same-machine 640x360 synthetic repeat
  measured YuNet CPU adapter 218.784 FPS, OpenVINO AUTO 6.488 FPS, and
  TensorFlow CPU 1.792 FPS; accuracy was not measured
- Evidence: `src/projectblur/detection/`, `tests/detection/`, `examples/`

## M3 — Face tracking

- Status: Planned
- Evidence: No implementation or experiment yet

## M4 — Face recognition and whitelist

- Status: Planned
- Evidence: No implementation or experiment yet

## M5 — Anonymization pipeline

- Status: Current (sequential image/frame prototype only)
- Evidence: `src/projectblur/anonymization/`, `tests/anonymization/`

## M6 — Real-time optimization

- Status: Current (OpenVINO trial plus experimental YuNet latency checkpoint)
- Evidence: `benchmarks/retinaface_backend_benchmark.py`,
  `artifacts/benchmarks/retinaface_openvino_trial_2026-07-14.json`,
  `artifacts/benchmarks/yunet_trial_2026-07-14.json`, and
  `artifacts/benchmarks/detector_latency_repeat_2026-07-17_console.json`

## M7 — Web application integration

- Status: Current (camera/screen preview with source-resolution local blur;
  upload control removed)
- Evidence: `src/projectblur/web/`, `tests/web/`

## M8 — Virtual camera and recording

- Status: Current (native synthetic-output prototype; capture integration and
  recording pending)
- Evidence: `src/projectblur/pipeline/`, `native/virtual_camera/`, `DEC-006`,
  `DEC-008`, `EXP-005`, and the 720p/1080p benchmark artifacts; a ProjectBlur
  camera registered and streamed on one Windows 11 development machine

## M9 — Evaluation and final presentation

- Status: Planned
- Evidence: Presentation structure exists; measured results do not
