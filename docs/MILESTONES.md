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
- Selected approach: OpenVINO RetinaFace is the web prototype trial; production
  detector is not selected
- Benchmark summary: at 640x360 synthetic input, YuNet CPU adapter 185.18 FPS,
  OpenVINO AUTO 6.09 FPS, and TensorFlow CPU 1.47 FPS; accuracy not measured
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
  `artifacts/benchmarks/yunet_trial_2026-07-14.json`

## M7 — Web application integration

- Status: Current (upload, camera, and screen preview prototype)
- Evidence: `src/projectblur/web/`, `tests/web/`

## M8 — Virtual camera and recording

- Status: Planned
- Evidence: No implementation yet

## M9 — Evaluation and final presentation

- Status: Planned
- Evidence: Presentation structure exists; measured results do not
