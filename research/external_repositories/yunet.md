# OpenCV YuNet Integration Note

## Role in ProjectBlur

YuNet is an experimental CPU face-detector candidate for `EXP-004`. ProjectBlur
integrates it through the ProjectBlur-owned `YuNetDetector` adapter and OpenCV's
published `FaceDetectorYN` API. No OpenCV Zoo source code is copied into
`src/projectblur`.

OpenVINO RetinaFace remains the default web detector until explicitly
authorized face inputs establish detection agreement, small-face behavior, and
privacy-critical misses.

## Official Source

- Model directory and documentation:
  https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- OpenCV `FaceDetectorYN` API:
  https://docs.opencv.org/4.x/df/d20/classcv_1_1FaceDetectorYN.html
- YuNet paper DOI: https://doi.org/10.1007/s11633-023-1423-y

The upstream model directory describes YuNet as lightweight, reports WIDER Face
evaluation results, documents the 15-value output schema, and reports an
approximate trained face-size range of 10x10 to 300x300 pixels. These upstream
results are context only and are not ProjectBlur accuracy evidence.

## Selected Local Model

- Filename: `face_detection_yunet_2026may.onnx`
- Local location: `models/opencv/yunet/`
- Size: 229,738 bytes
- SHA-256:
  `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0`
- Preparation script: `scripts/prepare_yunet.ps1`
- Runtime validated: OpenCV 5.0.0 on 2026-07-14

The current OpenCV Zoo documentation identifies this dynamic-input model as the
default compatible path for the OpenCV 5.x ONNX Runtime engine. Model files stay
local under the git-ignored `models/` directory.

The earlier `face_detection_yunet_2023mar.onnx` was briefly measured before
this current upstream note was verified. Its diagnostic results and hash are
preserved in `artifacts/benchmarks/yunet_trial_2026-07-14.json`, but it is not
the ProjectBlur default YuNet artifact.

## License and Redistribution

The OpenCV Zoo YuNet model directory reports that its files use the MIT License.
ProjectBlur nevertheless does not commit or redistribute downloaded weights;
authorized users run the preparation script and verify the pinned SHA-256.

## Adapter Mapping

OpenCV documents each detected face as 15 values: bounding-box origin and size,
right eye, left eye, nose, right mouth corner, left mouth corner, and score. The
adapter clips these values to the source image and maps them into the existing
ProjectBlur `Detection` schema.

## Known Limitations

- Only synthetic no-face latency has been measured locally.
- The OpenCV runtime emitted a new-graph-engine target warning during model
  loading; inference succeeded, but this requires follow-up before production.
- Authorized face accuracy and false-negative behavior remain unmeasured.
- Threshold `0.6` is an experimental default, not a privacy-calibrated value.
- Model latency does not establish browser FPS or production suitability.

Accessed: 2026-07-14
