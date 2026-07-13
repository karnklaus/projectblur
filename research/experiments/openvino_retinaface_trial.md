# OpenVINO RetinaFace Backend Trial

## Status

- Date: 2026-07-14
- Outcome: Use as the default web prototype backend for further evaluation
- Production status: Not selected or validated for production
- Model: Open Model Zoo `retinaface-resnet50-pytorch`, FP16 IR
- Runtime: OpenVINO 2026.2.1
- Project adapter:
  `src/projectblur/detection/openvino_retinaface_detector.py`
- Benchmark script: `benchmarks/retinaface_backend_benchmark.py`
- Result artifact:
  `artifacts/benchmarks/retinaface_openvino_trial_2026-07-14.json`

## Purpose

The TensorFlow RetinaFace web path remained near 1.4 FPS after fixing accidental
input upscaling. This trial asks whether the same RetinaFace family can provide
a more responsive CPU-oriented prototype through OpenVINO while retaining the
ProjectBlur detection schema.

## Model Selection

The trial uses Intel Open Model Zoo's public
`retinaface-resnet50-pytorch` entry. The model documentation defines:

- input name `data` with shape `1x3x640x640`;
- BGR channel order;
- mean values `[104.0, 117.0, 123.0]`;
- 16,800 anchor predictions;
- bounding-box output `face_rpn_bbox_pred`, shape `1x16800x4`;
- face-score output `face_rpn_cls_prob`, shape `1x16800x2`;
- landmark output `face_rpn_landmark_pred`, shape `1x16800x10`;
- 88.8627 GFLOPs and 27.2646 million parameters;
- reported WIDER AP of 91.78% when the documented evaluation counts only faces
  larger than 64x64 pixels.

The model's original repository license is identified as MIT in the Open Model
Zoo configuration. OpenVINO Runtime is Apache-2.0. Model code, model weights,
and OpenVINO itself retain their separate upstream terms.

## Acquisition and Conversion

The official Open Model Zoo downloader obtained the pinned source files and
`Resnet50_Final.pth` checkpoint. Conversion used a separate, git-ignored
environment so the discontinued OpenVINO Development Tools would not downgrade
the application's OpenVINO 2026 runtime.

Conversion environment:

- Python 3.12.10
- `openvino-dev 2024.6.0`
- `openvino 2024.6.0`
- PyTorch 2.13.0
- TorchVision 0.28.0
- ONNX 1.22.0
- ONNX Script 0.7.1

The first conversion attempt failed because current PyTorch's ONNX exporter
required `onnxscript`, which the legacy Open Model Zoo dependency set did not
install. Adding the missing exporter dependency fixed the reported cause.

PyTorch exported an opset 18 ONNX graph and warned that automatic downgrade to
the requested opset 11 could not convert a `Resize` operator. The exporter then
reported that ONNX validation passed. OpenVINO Model Optimizer accepted that
graph and generated an FP16-compressed IR v11 model successfully. This warning
is preserved because it is part of the conversion provenance; detection
agreement still requires validation on authorized images.

Generated local files:

| File | Size | SHA-256 |
| --- | ---: | --- |
| `retinaface-resnet50-pytorch.xml` | 361,565 bytes | `65dd79854cc5aa20c8d45d3e98bafa3de8306c2159a5974d8376176b526ffd78` |
| `retinaface-resnet50-pytorch.bin` | 54,529,528 bytes | `98f5cf9f7382bfe1442c437b5301df8717bee2751037ce364778dcf46ef80c1f` |

The model directory is ignored by Git. The repository stores preparation
instructions, sources, and hashes rather than redistributing the weights.

## Adapter Design

`OpenVinoRetinaFaceDetector` is independent from the existing TensorFlow
adapter. It:

1. validates the configured IR input and output schema before compilation;
2. resizes BGR input to the fixed 640x640 tensor and emits NCHW float32;
3. compiles the model with OpenVINO's latency performance hint;
4. generates the model's 16,800 verified priors;
5. decodes bounding boxes and five landmarks with the documented variances;
6. applies confidence filtering and non-maximum suppression;
7. maps coordinates back to the original image dimensions; and
8. returns the same ProjectBlur `Detection` schema as the TensorFlow adapter.

The model's mean subtraction is embedded in the converted IR. Applying it again
in Python would be incorrect.

The detection schema was moved into its own lightweight module, and backend
imports are lazy. Importing the OpenVINO web path no longer imports TensorFlow
or `retina-face`.

## Benchmark Environment

- Operating system: Microsoft Windows 10.0.26200, x64
- Processor identifier: Intel64 Family 6 Model 151 Stepping 2, GenuineIntel
- Logical processors visible to Python: 12
- Main Python environment: 3.12.10
- OpenVINO Runtime: 2026.2.1
- Input: all-black synthetic BGR array, 640x360
- Warm-up iterations after cold call: 3
- Measured sequential iterations: 30
- TensorFlow comparison: `retina-face 0.0.18`, TensorFlow 2.21.0,
  `allow_upscaling=False`

The input contains no face or private media. It measures inference and adapter
post-processing latency, not detection accuracy.

## Results

| Backend | Device | Cold | Mean | Median | P95 | Mean FPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TensorFlow RetinaFace | CPU | 3.6328 s | 0.6783 s | 0.6760 s | 0.7117 s | 1.47 |
| OpenVINO RetinaFace | AUTO | 0.6921 s | 0.1641 s | 0.1642 s | 0.1718 s | 6.09 |
| OpenVINO RetinaFace | CPU | 0.6670 s | 0.1659 s | 0.1647 s | 0.1815 s | 6.03 |
| OpenVINO RetinaFace | Intel GPU | 5.1423 s | 0.7614 s | 0.7750 s | 0.7842 s | 1.31 |

For this specific synthetic sequential workload, OpenVINO AUTO had about 4.13
times the mean throughput of the corrected TensorFlow 640x360 path. AUTO and
explicit CPU were effectively similar. Explicit Intel GPU was slower and had a
much larger cold compile cost, so GPU must not be assumed faster on this
machine.

A separate ten-call check of ProjectBlur's complete server function, including
JPEG decode, detection, blur, and JPEG encode, measured about 5.14 FPS after
warm-up. Browser capture, HTTP transfer, rendering, and a real face workload can
reduce the observed UI rate further.

### Manual Live-Preview Observation

The browser UI later reported the following sustained pipeline rates:

| OpenVINO device setting | Capture setting | Observed frame | Faces blurred | Reported pipeline FPS |
| --- | --- | ---: | ---: | ---: |
| `AUTO` (no explicit device environment variable) | Not recorded | 367 | 0 | 5.1 |
| `CPU` (explicit environment variable) | Not recorded | 84 | 0 | 5.3 |
| Not recorded | 480 px | 56 | 0 | 5.5 |

The explicit CPU result was about 3.9% higher, but this is not evidence of a
meaningful performance difference. The observations used different run lengths,
contained no detected faces, and did not record repeated trials, latency
percentiles, source resolution, CPU load, or other concurrent activity. They do
support the earlier finding that `AUTO` and explicit `CPU` behave similarly on
this machine; `AUTO` may already be selecting the CPU for this workload.

The 480-pixel observation was about 7.8% higher than the earlier 5.1 FPS
observation, but its device setting and other conditions were not recorded and
the run stopped at frame 56. It is therefore not a controlled resolution
comparison. The small change is consistent with reducing capture, JPEG, and
transport work while leaving the fixed 640x640 model inference unchanged.

### Bottleneck Interpretation

At 5.1 pipeline FPS, one browser round trip takes approximately 196 ms. The
separate OpenVINO `AUTO` adapter benchmark averaged approximately 164 ms per
inference, so detector execution accounts for an estimated 84% of that time.
This percentage is an approximation because it combines separate measurements,
but it identifies inference as the dominant bottleneck. Eliminating every other
measured cost while keeping this detector would still cap output near the 6.09
FPS adapter result.

Every live frame currently incurs browser JPEG encoding, HTTP upload, server
JPEG decoding, resize to the model's fixed 640x640 input, RetinaFace ResNet50
inference, output decoding, optional Gaussian blur, server JPEG encoding, HTTP
download, and browser rendering. A frame with no detected face still requires
the full neural-network forward pass. The 480-pixel browser mode reduces image
transport work, but it does not reduce the current model's 640x640 inference
shape.

Thirty pipeline FPS permits about 33.3 ms per frame. The observed 196 ms path
would therefore require approximately a 5.9-times reduction in total frame
time, which is not achievable through JPEG or UI tuning alone while the current
164 ms detector remains on every frame.

## Current Prototype Decision

The web prototype now defaults to OpenVINO with device `AUTO`. The TensorFlow
backend remains available only when explicitly selected with
`PROJECTBLUR_DETECTOR=tensorflow` and installed from
`requirements-tensorflow.txt`. TensorFlow is excluded from the default runtime.
There is no silent fallback: an invalid or missing OpenVINO model is an
actionable error instead of an unreported semantic change.

This is a prototype decision based on latency, not a final detector selection.

## Selected Next Experiment

Run `EXP-004`, a CPU comparison between the current OpenVINO RetinaFace ResNet50
adapter and OpenCV YuNet. Keep RetinaFace as the reference and do not switch the
web default until both latency and privacy-critical detection behavior have
been measured on explicitly authorized inputs. The experiment plan is recorded
in `research/experiments/yunet_realtime_baseline_plan.md`.

YuNet is selected before tracking because it addresses the dominant per-frame
detection cost while retaining detection on every submitted frame. Skipping
detection and relying on a tracker first could leave a newly appearing face
unblurred until the next detector frame. Tracking remains the following step for
box stability and workload reduction only after stale-track and new-face
fail-safe behavior is defined.

## Limitations and Required Follow-Up

- The benchmark input contains no faces.
- Accuracy, precision, recall, and detection agreement were not measured.
- Small and distant faces are especially uncertain because the documented model
  result excludes faces at or below 64x64 pixels.
- Only sequential batch-one inference was tested.
- CPU and memory utilization were not recorded.
- The browser live-preview path was manually exercised, but camera versus screen
  source, source resolution, and end-to-end latency were not recorded.
- Five to six detector updates per second is not the project's unverified 30
  FPS target.
- Tracking is still required to update blur regions between detector frames.
- A privacy-first design must continue blurring when a detection or track is
  stale, missing, or uncertain.

Before any production or presentation accuracy claim, run the same TensorFlow
and OpenVINO adapters on an explicitly authorized dataset containing varied
face sizes, pose, occlusion, lighting, blur, and screen-share conditions.

## Sources

- OpenVINO RetinaFace model documentation:
  https://docs.openvino.ai/2023.3/omz_models_model_retinaface_resnet50_pytorch.html
- Open Model Zoo model configuration:
  https://github.com/openvinotoolkit/open_model_zoo/blob/master/models/public/retinaface-resnet50-pytorch/model.yml
- Versioned official post-processing reference:
  https://github.com/openvinotoolkit/open_model_zoo/blob/2023.3.0/demos/common/python/openvino/model_zoo/model_api/models/retinaface.py
- OpenVINO ONNX loading documentation:
  https://docs.openvino.ai/2026/openvino-workflow/model-preparation/convert-model-onnx.html
- OpenVINO repository and license:
  https://github.com/openvinotoolkit/openvino
- Original PyTorch RetinaFace implementation:
  https://github.com/biubug6/Pytorch_Retinaface

Accessed: 2026-07-14
