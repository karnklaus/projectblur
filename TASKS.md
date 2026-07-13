# ProjectBlur Tasks

## Current

- [ ] Decide and define the domain-level face detection result schema.
- [ ] Validate the RetinaFace adapter against a pinned package version in a
  project virtual environment.
- [ ] Compare RetinaFace with YuNet for CPU accuracy and latency.
- [ ] Add a reproducible detector benchmark script and authorized test inputs.
- [ ] Design `EXP-002` to compare SIFT-based matching with a modern embedding
  baseline using privacy-critical error metrics.

## Completed

- [x] Add `retina-face` as an external dependency.
- [x] Add a ProjectBlur-owned RetinaFace adapter for image paths and NumPy
  arrays.
- [x] Normalize RetinaFace bounding boxes and landmarks.
- [x] Add mocked unit tests that do not download a model or use the network.
- [x] Add a command-line RetinaFace example.
- [x] Record RetinaFace source and attribution information.
- [x] Add evidence-linked development, decision, experiment, milestone, and
  presentation records.

## Planned

- [ ] Integrate ByteTrack or SORT.
- [ ] Add MobileFaceNet embeddings.
- [ ] Add FAISS whitelist matching.
- [ ] Add track decision caching.
- [ ] Add FastAPI streaming and a React preview.
- [ ] Add virtual-camera output.
- [ ] Evaluate OpenVINO and TensorRT optimization.
- [ ] Add recording and video-codec fallback.
- [ ] Add centralized privacy-focused logging and configuration.

## Blocked or Needs Decision

- [ ] Primary face detector and benchmark acceptance criteria
- [ ] Final standard detection/domain schema
- [ ] Supported Python version
- [ ] Packaging approach beyond `requirements.txt`
- [ ] Tracker and embedding model selection
- [ ] Model redistribution licenses
- [ ] Recognition and anonymization threshold calibration
