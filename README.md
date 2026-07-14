# ProjectBlur

ProjectBlur is an early-stage face-anonymization project for privacy- and
PDPA-conscious processing of images, recorded video, CCTV, and live streams.
The intended whitelist policy keeps authorized faces visible and anonymizes
unauthorized faces.

## Current status

The current prototype detects faces and applies Gaussian blur through a small
FastAPI web interface. OpenVINO RetinaFace is the default prototype backend;
TensorFlow RetinaFace remains a reference and OpenCV YuNet is an explicit
experimental CPU backend. The interface accepts uploaded images and browser
frames captured from a camera or shared screen. Tracking, recognition,
whitelist matching, video-file processing, and production streaming remain
planned.

## Installation

Create a virtual environment and install the current dependencies:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Prepare the official Open Model Zoo RetinaFace model locally. This creates an
isolated conversion environment and git-ignored model files:

```powershell
.\scripts\prepare_openvino_retinaface.ps1
```

The converter downloads a checkpoint of about 109 MB and produces an FP16 IR
with a weights file of about 55 MB. Model weights are not committed.

Prepare the current OpenCV 5.x-compatible YuNet experiment model separately:

```powershell
.\scripts\prepare_yunet.ps1
```

The script downloads about 230 KB into the git-ignored `models/` directory and
verifies its pinned SHA-256.

The TensorFlow RetinaFace reference is intentionally excluded from the default
runtime. Install it only for comparison or explicit rollback:

```powershell
python -m pip install -r requirements-tensorflow.txt
```

## Face detection

ProjectBlur has independent OpenVINO RetinaFace, TensorFlow RetinaFace, and
OpenCV YuNet adapters in `src/projectblur/detection`. The web prototype defaults
to the official Open Model Zoo ResNet50 model through OpenVINO. YuNet is
available only when explicitly selected for `EXP-004`. Upstream source is not
copied into the production package.

See [`research/external_repositories/openvino_retinaface.md`](research/external_repositories/openvino_retinaface.md)
[`research/external_repositories/retinaface.md`](research/external_repositories/retinaface.md),
and [`research/external_repositories/yunet.md`](research/external_repositories/yunet.md)
for source, attribution, version, and local-model information.

## Running

The repository does not yet have packaging metadata, so add `src` to
`PYTHONPATH`. In PowerShell, run the example with an authorized image:

```powershell
$env:PYTHONPATH = "src"
python examples/retinaface_example.py path/to/image.jpg
```

Run the browser face-blurring prototype:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m uvicorn projectblur.web.app:app --reload
```

Open `http://127.0.0.1:8000`. You can upload a JPEG, PNG, or WebP image, start a
camera, or share a screen. Camera and screen access require explicit browser
permission; audio is not requested. Live sources offer 480, 640, and 960 pixel
capture modes and default to 640 pixels on their longest edge. The web detector
uses OpenVINO device `AUTO` and sends one frame at a time to avoid an inference
backlog. The returned browser preview has every RetinaFace detection blurred.
When the explicit YuNet backend is selected, the same policy blurs every YuNet
detection.

Run the experimental YuNet backend for a controlled manual trial:

```powershell
$env:PROJECTBLUR_DETECTOR = "yunet"
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m uvicorn projectblur.web.app:app --reload
```

The status line reports detector and total server milliseconds. YuNet has only
synthetic no-face latency evidence; do not interpret faster preview as proof of
face-detection safety.

Live camera and screen sessions now collect bounded performance metrics in
browser memory. The panel shows rolling throughput, P95 latency, and iterations
below 30 FPS. Stop the source and choose **Export metrics** to download a JSON
record containing timing, dimensions, settings, and face counts only. See
[`docs/METRICS.md`](docs/METRICS.md) for schema and privacy details.
Presentation callbacks are measured separately and never block the processing
loop; visibility, warm-up, and capture/JPEG stalls are included in schema v2.

Inputs are processed in memory without intentional persistence. The live
preview is not a virtual camera and does not replace the video seen by other
applications. Set `PROJECTBLUR_OPENVINO_DEVICE=CPU` to force CPU. The explicit
reference fallback is `PROJECTBLUR_DETECTOR=tensorflow` after installing
`requirements-tensorflow.txt`; no silent fallback is performed when the
OpenVINO model is missing.

## Testing

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -t . -p "test_*.py" -v
python -m compileall src examples tests
```

Run the reproducible synthetic backend benchmark:

```powershell
$env:PYTHONPATH = "src"
python benchmarks/retinaface_backend_benchmark.py --backend openvino --device AUTO
python benchmarks/retinaface_backend_benchmark.py --backend yunet --mode pipeline
```

See `docs/TESTING.md` for POSIX commands and model-test rules.

## Project structure

- `src/projectblur/detection/`: external face-detector adapters
- `src/projectblur/anonymization/`: reusable face-blurring operations
- `src/projectblur/web/`: FastAPI prototype and browser interface
- `tests/`: mocked detector, anonymization, and image-processing unit tests
- `examples/`: runnable integration examples
- `benchmarks/`: reproducible non-biometric performance scripts
- `scripts/`: local model preparation utilities
- `research/`: local research material and external dependency summaries
- `docs/`: research and testing indexes
- `artifacts/`: commit-safe benchmark, chart, diagram, screenshot, and demo
  evidence; sensitive or large artifacts are prohibited

## Third-party dependencies

RetinaFace is used through OpenVINO/Open Model Zoo and the published
`retina-face` reference package. Upstream sources and model artifacts remain
external; see the records under `research/external_repositories/`.

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
