# Testing ProjectBlur

## Environment

Create and activate a virtual environment, then install the current dependency
set:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Set `PYTHONPATH` to `src` for the commands below because packaging metadata has
not yet been added.

Prepare local detector models only for integration and manual tests:

```powershell
.\scripts\prepare_openvino_retinaface.ps1
.\scripts\prepare_yunet.ps1
```

The preparation command requires network access and creates ignored local
artifacts. It is never run by the offline unit suite.

## Unit Tests

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

POSIX shells:

```bash
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py' -v
```

Relevant suites can be run by changing `-s tests` to `tests/detection`,
`tests/anonymization`, or `tests/web`.

## Syntax Validation

```bash
python -m compileall src examples benchmarks tests
```

## Synthetic Backend Benchmark

The benchmark uses an all-black frame and contains no biometric media:

```powershell
$env:PYTHONPATH = "src"
python benchmarks/retinaface_backend_benchmark.py --backend openvino --device AUTO
python benchmarks/retinaface_backend_benchmark.py --backend openvino --device CPU
python benchmarks/retinaface_backend_benchmark.py --backend tensorflow
python benchmarks/retinaface_backend_benchmark.py --backend yunet --mode adapter
python benchmarks/retinaface_backend_benchmark.py --backend yunet --mode pipeline
```

Do not interpret this latency test as face-detection accuracy evidence.

## Linting and Formatting

No linter, formatter, or type checker is configured in this repository. Do not
add one solely for validation.

## Model Test Rules

- No network access or model downloads in unit tests.
- No GPU requirement.
- Mock external inference.
- Use synthetic arrays or authorized sample assets.
- Keep slow integration tests separate and explicitly marked.

## Manual Test

The command-line example remains a TensorFlow adapter reference. After
installing the optional dependencies, supply an authorized image:

```powershell
python -m pip install -r requirements-tensorflow.txt
$env:PYTHONPATH = "src"
python examples/retinaface_example.py path/to/image.jpg
```

The TensorFlow dependency may download model weights during its first real
inference. Do not use the manual command in offline unit-test automation.

### Web Prototype

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m uvicorn projectblur.web.app:app --reload
```

Open `http://127.0.0.1:8000` and perform these checks with explicitly authorized
content:

1. Upload an image and verify that every detected face is blurred.
2. Start the camera, grant browser permission, and verify that input and blurred
   output previews appear and update without overlapping request failures.
   Compare Fast (480), Balanced (640), and Detail (960) while observing the
   displayed pipeline FPS and small-face detection behavior.
3. Stop the camera and confirm that its browser-use indicator turns off.
4. Share a window or screen, verify the blurred output, then stop sharing from
   the browser and confirm that ProjectBlur returns to the stopped state.
5. Deny either permission once and verify that the page reports the denial.
6. Confirm that **Performance log** updates every 30 iterations with rolling
   throughput, P95 pipeline latency, below-30-FPS count, detector/server P95,
   capture/decode P95, and hidden-sample count.
7. Stop the source, verify the panel changes to **Run summary**, and export the
   metrics JSON. Confirm it uses schema v2 and contains session samples,
   `slowest_frames`, `visibility_events`, `steady_state`, warm-up markers, and
   capture-stall markers, but contains no image data, URLs, titles, filenames,
   or identity fields.
8. Use **Reset log** and confirm stored sessions and summary values clear. When
   reset during an active source, confirm a fresh session begins.
9. During a separate run, leave the ProjectBlur tab for about 10 seconds and
   return. Verify the export records the visibility transition and that
   animation-frame presentation timing did not block `pipeline_ms`. Browser
   background policies may still throttle capture or JavaScript execution.

Camera and screen capture must be tested from `localhost` or HTTPS. Manual
real-face inference is not included in the offline unit suite. Prepare the local
OpenVINO model before the server starts processing input. This prototype
preview is not a virtual camera output.

See `docs/METRICS.md` for metric definitions and the contextual information to
record alongside an exported JSON file. Schema v2 processing time includes
capture, JPEG, request/response, and image decode, while presentation callback
delay is non-blocking and reported separately. Do not combine schema v1 and v2
pipeline values into one distribution.
