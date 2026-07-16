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

The benchmark uses an all-black frame and contains no biometric media. Every
successful command automatically creates a unique JSON file in
`artifacts/benchmarks/`:

```powershell
$env:PYTHONPATH = "src"
python benchmarks/retinaface_backend_benchmark.py --backend openvino --device AUTO
python benchmarks/retinaface_backend_benchmark.py --backend openvino --device CPU
python benchmarks/retinaface_backend_benchmark.py --backend tensorflow
python benchmarks/retinaface_backend_benchmark.py --backend yunet --mode adapter
python benchmarks/retinaface_backend_benchmark.py --backend yunet --mode pipeline
```

The default filename contains backend, mode, device, and a microsecond UTC run
ID. Each record includes the full timing summary, configuration, environment
and package versions, Git commit and dirty state, limitations, and SHA-256 for
local model files exposed by the adapter. Console JSON remains available for
quick inspection. Use `--output path\to\new-record.json` only when a specific
new path is required. Existing output files are rejected instead of
overwritten.

Do not interpret this latency test as face-detection accuracy evidence. For a
paper comparison, keep resolution, mode, device, warm-up, iterations, power
state, and competing workload fixed; run repeated trials rather than selecting
the fastest file. Report all included/excluded runs and retain their raw JSON.

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

1. Start the camera, grant browser permission, and verify that the anonymized
   preview appears and updates without overlapping request failures. Switch
   between **Original** and **Anonymized** and verify only one is visible.
   After a processed frame appears, export both images and confirm that the
   original and blurred PNG files have matching dimensions and frame content,
   with detected faces blurred only in the latter.
   Compare Fast (480), Balanced (640), and Detailed (960) while observing the
   displayed pipeline FPS and small-face detection behavior.
2. Stop the camera and confirm that its browser-use indicator turns off.
3. Share a window or screen, verify the blurred output, then stop sharing from
   the browser and confirm that ProjectBlur returns to the stopped state.
4. Deny either permission once and verify that the page reports the denial.
5. Confirm that **Performance log** updates every 30 iterations with rolling
   throughput, P95 pipeline latency, below-30-FPS count, detector/server P95,
   capture/render P95, and hidden-sample count.
6. Stop the source, verify the panel changes to **Run summary**, and export the
   metrics JSON. Confirm it uses schema v3 and contains session samples,
   `slowest_frames`, `visibility_events`, `steady_state`, warm-up markers, and
   capture-stall markers plus `render_ms`, but contains no image data, face
   boxes, URLs, titles, filenames, or identity fields.
7. Use **Reset log** and confirm stored sessions and summary values clear. When
   reset during an active source, confirm a fresh session begins.
8. During a separate run, leave the ProjectBlur tab for about 10 seconds and
   return. Verify the export records the visibility transition and that
   animation-frame presentation timing did not block `pipeline_ms`. Browser
   background policies may still throttle capture or JavaScript execution.

For paper measurements, export every completed browser session before reload or
reset. Browser metrics intentionally remain in memory until the user explicitly
exports them; unlike the CLI benchmarks, they cannot become durable evidence
automatically.

Camera and screen capture must be tested from `localhost` or HTTPS. Manual
real-face inference is not included in the offline unit suite. Prepare the local
OpenVINO model before the server starts processing input. This prototype
preview is not a virtual camera output.

Compare the Original and Anonymized views around non-face text and edges. Those
pixels should retain the source-frame detail because only the reduced detector
copy is JPEG-encoded; record any mismatch or browser-specific canvas behavior.

See `docs/METRICS.md` for metric definitions and the contextual information to
record alongside an exported JSON file. Schema v3 processing time includes
source-frame capture, reduced JPEG, coordinate request/response, and
source-resolution canvas render, while presentation callback delay is
non-blocking and reported separately. Do not combine schema v1, v2, and v3
pipeline values into one distribution.

### High-resolution Pipeline and Virtual Camera

Run the offline coordinate-mapping and shared-memory tests:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests\pipeline -p "test_*.py" -v
```

From an x64 Visual Studio developer command prompt, validate the matching C++
header without registering a camera:

```powershell
cl /nologo /std:c++20 /W4 /WX /EHsc `
  /I native\virtual_camera\include `
  native\virtual_camera\tests\frame_protocol_layout.cpp `
  /Fe:.tmp\native\frame_protocol_layout.exe
.\.tmp\native\frame_protocol_layout.exe
```

Build the Windows 11 x64 source and control executable without registering a
camera:

```powershell
.\scripts\build_virtual_camera.ps1 -Configuration Release
```

The build requires Visual Studio 2022 Build Tools with Desktop development with
C++, Windows SDK 10.0.26100, and NuGet CLI. Installation requires UAC because
the out-of-process Windows Camera Frame Server must resolve the ProjectBlur COM
source machine-wide. Camera access remains current-user scoped:

```powershell
Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList @(
  '-NoProfile', '-ExecutionPolicy', 'Bypass',
  '-File', (Resolve-Path '.\scripts\install_virtual_camera.ps1').Path
)

.\native\virtual_camera\build\Release\ProjectBlurCameraControl.exe status
```

Run the synthetic source-to-Media-Foundation performance test. It generates
pixels in memory and stores JSON metrics only:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe benchmarks\virtual_camera_output_benchmark.py `
  --width 1280 --height 720 --fps 30 --warmup 1.5 --seconds 10

.\.venv\Scripts\python.exe benchmarks\virtual_camera_output_benchmark.py `
  --width 1920 --height 1080 --fps 30 --warmup 1.5 --seconds 10
```

These runs are also saved automatically with unique UTC run IDs. Supplying an
explicit `--output` is optional and may only name a path that does not exist.

Use `--baseline-fps` only with a separately measured pipeline value. The
resulting `estimated_pipeline_fps_with_publish` is a serial-cost estimate, not
an integrated detector benchmark. `camera_reader.delivered_fps` is the actual
Media Foundation delivery rate.

Remove the prototype from an elevated PowerShell session:

```powershell
.\scripts\remove_virtual_camera.ps1
```

The automated native benchmark validates enumeration, activation, media-type
selection, metadata, fallback counts, frame uniqueness, pacing, and delivery.
It does not validate physical-camera or screen capture, face detection, CPU or
RAM, Windows Camera/Zoom/Meet/Teams compatibility, DLL signing, or removal.
Those remain manual gates in `EXP-005`.
