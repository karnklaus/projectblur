# TensorFlow RetinaFace Live-Preview Baseline

## Status

- Date: 2026-07-14
- Outcome: Retain as a reference implementation; do not select as the preferred
  real-time backend
- Backend: `serengil/retinaface` through TensorFlow/Keras
- Project path: `src/projectblur/detection/retinaface_detector.py`
- Result artifact:
  `artifacts/benchmarks/retinaface_tensorflow_live_baseline_2026-07-14.json`

## Question

Can the current TensorFlow RetinaFace integration provide a sufficiently
responsive browser camera or screen-blurring preview on the development
machine?

## Environment

- Operating system: Microsoft Windows 10.0.26200, x64
- Processor identifier: Intel64 Family 6 Model 151 Stepping 2, GenuineIntel
- Logical processors visible to Python: 12
- Python: 3.12.10
- `retina-face`: 0.0.18
- TensorFlow: 2.21.0
- `tf-keras`: 2.21.0
- OpenCV: 5.0.0
- Inference device observed in TensorFlow output: CPU

The exact retail CPU name and total memory were not recorded because Windows
CIM access was denied in the current environment. The processor identifier is
preserved instead of guessing a product name.

## Root Cause of the Slow Preview

The original browser client limited a live frame to 960 pixels on its longest
edge, producing a typical 960x540 frame. However, `retina-face 0.0.18` calls
its preprocessing with `allow_upscaling=True` by default. Its preprocessing
target uses a 1024-pixel short edge and a 1980-pixel maximum long edge. The
960x540 frame was therefore expanded to approximately 1820x1024 before model
inference.

This means the browser-side resize did not limit the TensorFlow model to the
expected pixel count. The model processed approximately 1.86 million pixels
instead of 0.52 million pixels per frame, before considering model and graph
overheads.

## Procedure

1. Build the model once with `RetinaFace.build_model()`.
2. Use all-black synthetic BGR arrays so no biometric or copyrighted media is
   involved.
3. Run two sequential detections for each configuration in the same Python
   process.
4. Measure wall-clock time around `RetinaFace.detect_faces()` with
   `time.perf_counter()`.
5. Compare the previous 960x540 input with automatic upscaling against a
   640x360 input with upscaling disabled.
6. Separately call ProjectBlur's real web processing function with an encoded
   synthetic 640x360 JPEG to verify the complete decode, detection, blur, and
   encode path.

This was a diagnostic microbenchmark, not the full planned `EXP-001`. It used
only two timed calls per configuration, did not randomize test order, did not
measure resource utilization, and did not use a face dataset.

## Results

| Configuration | Call | Latency | Approximate throughput |
| --- | --- | ---: | ---: |
| 960x540, upstream upscaling enabled | First | 22.114 s | 0.045 FPS |
| 960x540, upstream upscaling enabled | Warm | 21.016 s | 0.048 FPS |
| 640x360, upstream upscaling disabled | First | 0.667 s | 1.499 FPS |
| 640x360, upstream upscaling disabled | Warm | 0.697 s | 1.435 FPS |

The warm-call ratio is approximately 30.2 times lower latency for the optimized
configuration. This ratio combines two intentional changes: lower capture
resolution and disabled RetinaFace upscaling. It must not be described as a
general TensorFlow-versus-OpenVINO result.

The first real ProjectBlur web-processing call completed successfully in 3.475
seconds for a synthetic 640x360 JPEG. That measurement included model
initialization and confirmed `allow_upscaling=False`; it detected zero faces, as
expected for the blank input.

## Changes Applied to the Reference Backend

- Added an explicit `allow_upscaling` policy to `RetinaFaceDetector`.
- Disabled automatic upscaling in the web application only.
- Added selectable 480, 640, and 960 pixel live-capture modes.
- Removed the fixed 100 ms delay between completed live requests.
- Added browser-visible round-trip pipeline FPS.

The general adapter still defaults to upstream-compatible upscaling so command
line and future evaluation callers must choose the tradeoff explicitly.

## Why This Backend Is Not Selected for Real-Time Use

Even after the 640x360 optimization, the measured warm inference rate was about
1.4 FPS on this machine before a full browser-camera benchmark. That is much
more responsive than the faulty upscaled path but remains far below the
project's unverified 30 FPS target.

Additional limitations are:

- Every preview frame is JPEG encoded, uploaded, decoded, inferred, blurred,
  encoded again, downloaded, and displayed.
- There is no face tracking, so detection must run for every output update.
- Lower input resolution can miss small or distant faces, which is a privacy
  risk for a blur-by-default system.
- The diagnostic input contained no faces, so it says nothing about precision,
  recall, small-face performance, or false negatives.
- The two-sample timing is insufficient for average, median, P95, thermal, or
  sustained-load conclusions.

Therefore the TensorFlow backend remains useful for compatibility and accuracy
comparison, but it should not become the default live backend without new
evidence.

## Follow-Up Candidate: OpenVINO RetinaFace

The follow-up controlled trial uses the official Open Model Zoo
`retinaface-resnet50-pytorch` model through OpenVINO. Its documented input is
fixed at `1x3x640x640` in BGR order, and its outputs are bounding-box, two-class
score, and five-landmark tensors. The model documentation reports 88.8627
GFLOPs, 27.2646 million parameters, and WIDER AP measured only for faces larger
than 64x64 pixels. These details make small-face testing essential.

The OpenVINO adapter must remain separate from the TensorFlow adapter and emit
the same ProjectBlur detection schema. It must not become the default until
model loading, post-processing, authorized face detection, latency, and license
handling are verified. Results are recorded in
`research/experiments/openvino_retinaface_trial.md`.

## Sources

- TensorFlow RetinaFace implementation:
  https://github.com/serengil/retinaface
- OpenVINO RetinaFace model documentation:
  https://docs.openvino.ai/2023.3/omz_models_model_retinaface_resnet50_pytorch.html
- Open Model Zoo model configuration:
  https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/retinaface-resnet50-pytorch/model.yml
- OpenVINO ONNX model loading documentation:
  https://docs.openvino.ai/2026/openvino-workflow/model-preparation/convert-model-onnx.html

Accessed: 2026-07-14
