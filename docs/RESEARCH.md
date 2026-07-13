# Research Index

Statuses describe repository work, not general technology maturity.

## Face Detection

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| RetinaFace | https://github.com/serengil/retinaface | Current adapter; evaluation pending | Alternative detector | `research/external_repositories/retinaface.md` | `src/projectblur/detection/retinaface_detector.py` | Upstream reports MIT; verify before redistribution |
| YuNet | https://github.com/opencv/opencv_zoo | Under evaluation | CPU-first detector | To be created | None | Verify model and repository terms |
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
are candidates. None is implemented or benchmarked in this repository.

## Integrated Face-Processing Toolkits

| Topic | Source | Status | Intended use | Local summary | Implementation | License note |
| --- | --- | --- | --- | --- | --- | --- |
| dlib | https://dlib.net/ | Under evaluation | Learning reference and end-to-end face pipeline baseline | `research/external_repositories/dlib.md` | None | Boost-licensed library; pretrained model and training-data terms require separate review |

## Privacy and PDPA

Research must cover biometric-data handling, data minimization, access control,
logging restrictions, retention, and dataset authorization. Legal requirements
and review ownership are to be confirmed; repository documentation is not legal
advice.
