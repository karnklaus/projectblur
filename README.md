# ProjectBlur

ProjectBlur is an early-stage face-anonymization project for privacy- and
PDPA-conscious processing of images, recorded video, CCTV, and live streams.
The intended whitelist policy keeps authorized faces visible and anonymizes
unauthorized faces.

## Current status

Only the RetinaFace detection adapter, example, and mocked unit tests are
implemented. Tracking, recognition, whitelist matching, anonymization, video
processing, API, and UI components are planned.

## Installation

Create a virtual environment and install the current dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

## Face detection

ProjectBlur uses RetinaFace for face detection through the published
`retina-face` dependency. The ProjectBlur-specific adapter lives in
`src/projectblur/detection`; upstream source is not copied into this project.

The upstream project is [serengil/retinaface](https://github.com/serengil/retinaface).
See [`research/external_repositories/retinaface.md`](research/external_repositories/retinaface.md)
for dependency, attribution, and version-tracking information.

## Running

The repository does not yet have packaging metadata, so add `src` to
`PYTHONPATH`. In PowerShell, run the example with an authorized image:

```powershell
$env:PYTHONPATH = "src"
python examples/retinaface_example.py path/to/image.jpg
```

## Testing

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests/detection -p "test_*.py" -v
python -m compileall src examples tests
```

See `docs/TESTING.md` for POSIX commands and model-test rules.

## Project structure

- `src/projectblur/detection/`: external face-detector adapters
- `tests/detection/`: mocked detector unit tests
- `examples/`: runnable integration examples
- `research/`: local research material and external dependency summaries
- `docs/`: research and testing indexes
- `artifacts/`: commit-safe benchmark, chart, diagram, screenshot, and demo
  evidence; sensitive or large artifacts are prohibited

## Third-party dependencies

RetinaFace is used through the published `retina-face` package. Its upstream
source remains external; see `research/external_repositories/retinaface.md`.

## Privacy warning

Do not commit personal face images, biometric embeddings, whitelist data, raw
CCTV footage, secrets, or private model files. Use only synthetic,
public-domain, or explicitly authorized test assets.

## Agent documentation

- `AGENTS.md`: repository instructions for AI agents
- `PROJECT_CONTEXT.md`: goals, scope, and technology status
- `ARCHITECTURE.md`: implemented and planned component boundaries
- `CODING_RULES.md`: code, dependency, privacy, and test rules
- `TASKS.md`: verified completed work and pending decisions
- `docs/RESEARCH.md`: research and external technology index
- `docs/TESTING.md`: commands and test constraints
- `docs/DEVELOPMENT_LOG.md`: chronological significant development work
- `docs/DECISIONS.md`: architecture and technology decision history
- `docs/EXPERIMENTS.md`: reproducible experiment plans and measured results
- `docs/MILESTONES.md`: evidence-linked project progress
- `docs/PRESENTATION_NOTES.md`: presentation material traceable to evidence

Architecture and technology choices may change when credible research,
reproducible measurements, or verified implementation constraints justify the
change. Planned and evaluated approaches are not current capabilities.
