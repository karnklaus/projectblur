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

Camera and screen capture must be tested from `localhost` or HTTPS. Manual
real-face inference is not included in the offline unit suite. Prepare the local
OpenVINO model before the server starts processing input. This prototype
preview is not a virtual camera output.
