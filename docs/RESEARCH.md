# Research Index

Statuses describe repository work, not general technology maturity.

## Face Detection

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| RetinaFace | https://github.com/serengil/retinaface | Current adapter; evaluation pending | Alternative detector | `research/external_repositories/retinaface.md` | `src/projectblur/detection/retinaface_detector.py` | Upstream reports MIT; verify before redistribution |
| OpenVINO RetinaFace | https://docs.openvino.ai/2023.3/omz_models_model_retinaface_resnet50_pytorch.html | Current web prototype trial; accuracy pending | Default prototype detector | `research/experiments/openvino_retinaface_trial.md` | `src/projectblur/detection/openvino_retinaface_detector.py` | OpenVINO/OMZ Apache-2.0; original model reports MIT; verify separately |
| YuNet | https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet | Experimental adapter; latency gates pass, accuracy pending | CPU-first detector candidate | `research/external_repositories/yunet.md`; `research/experiments/yunet_realtime_baseline_plan.md` | `src/projectblur/detection/yunet_detector.py` | Model folder reports MIT; weights remain local with pinned hash |
| CenterFace | https://github.com/Star-Clouds/CenterFace | Under evaluation | Detector comparison | To be created | None | Verify before use |
| YOLO face detection | To be confirmed | Under evaluation | GPU detector | To be created | None | Model-specific license required |

## Face Tracking

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| SORT | https://github.com/abewley/sort | Under evaluation | Lightweight tracking | To be created | None | Verify before use |
| ByteTrack | https://github.com/ifzhang/ByteTrack | Under evaluation | Multi-object tracking | To be created | None | Verify code and model terms |
| Inter-frame tracking | To be confirmed | Under evaluation | Reduce detection frequency | To be created | None | Technique-dependent |

## Face Recognition

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| MobileFaceNet | To be confirmed | Under evaluation | Face embeddings | To be created | None | Model license required |
| ArcFace | https://github.com/deepinsight/insightface | Under evaluation | Embedding comparison | To be created | None | Verify code, model, and dataset terms separately |
| FaceNet | https://arxiv.org/abs/1503.03832 | Under evaluation | Embedding comparison | To be created | None | Implementation-specific |
| SIFT / KPSIFT / PDSIFT | https://doi.org/10.1109/ICCSIT.2009.5234877 | Under evaluation | Classical local-feature recognition baseline | `research/papers/sift_features_for_face_recognition/research_note.md` | None | Implementation and dependency terms require review |

## Anonymization

Gaussian blur, pixelation, selective de-identification, and whitelist-based
anonymization are planned. Sources, implementation paths, quality criteria, and
privacy evaluation are to be confirmed.

## Real-time Optimization

OpenVINO, TensorRT, multiprocessing, shared memory, and detection-by-tracking
are candidates. TensorFlow and OpenVINO RetinaFace diagnostics are recorded in
`research/experiments/`. OpenVINO is the faster current web prototype trial,
but no production backend is selected because authorized accuracy and
small-face evaluation remain incomplete.

## Integrated Face-Processing Toolkits

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| dlib | https://dlib.net/ | Under evaluation | Learning reference and end-to-end face pipeline baseline | `research/external_repositories/dlib.md` | None | Boost-licensed library; pretrained model and training-data terms require separate review |

## Privacy and PDPA

Research must cover biometric-data handling, data minimization, access control,
logging restrictions, retention, and dataset authorization. Legal requirements
and review ownership are to be confirmed; repository documentation is not legal
advice.
