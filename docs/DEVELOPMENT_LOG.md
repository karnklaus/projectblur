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
