# ProjectBlur Context

## Objective

ProjectBlur aims to provide privacy- and PDPA-conscious face anonymization for
images, video files, cameras, and live streams. The repository currently
contains independent OpenVINO and TensorFlow RetinaFace adapters, an experimental
OpenCV YuNet adapter, Gaussian face blurring, and a FastAPI prototype for
uploaded images plus browser camera or screen frames. YuNet is the current CPU
prototype default for responsiveness, while its accuracy remains under
evaluation; the broader video and whitelist pipeline below is planned.

## Architecture Evolution

The pipeline is a working direction, not a permanent constraint. Models,
libraries, component boundaries, and transport strategies may change when a
documented decision is supported by research, reproducible experiments, or
verified implementation constraints. Historical decisions and experiment
results must remain traceable in `docs/DECISIONS.md` and
`docs/EXPERIMENTS.md`.

## Core Pipeline

```text
Input Image / Video / Camera / Stream
        ↓
Frame Ingestion
        ↓
Face Detection
        ↓
Face Tracking
        ↓
Face Alignment
        ↓
Face Embedding
        ↓
Whitelist Matching
        ↓
Track Decision Cache
        ↓
Blur or Bypass
        ↓
Preview / Recording / Virtual Camera
```

Face detection through `src/projectblur/detection`, Gaussian anonymization, and
browser image/camera/screen preview are implemented as a prototype. Camera and
screen frames are sent sequentially as still images; continuous server-side
video transport, tracking, recognition, whitelist matching, and decision
caching remain planned.

## Core Behavior

The planned system will detect and track faces, reduce repeated inference using
track IDs, align faces before embedding, match embeddings against a whitelist,
keep authorized faces visible, and anonymize unauthorized faces. Face regions
should support configurable padding, pixelation, and Gaussian blur.

## Target Performance

These are unverified targets, not current performance claims:

- Approximately 30 FPS input
- CPU-first baseline with optional GPU acceleration
- Non-blocking web interface and real-time preview
- Reduced repeated recognition through tracking and decision caching
- Optional virtual-camera output

## Technology Status

| Area | Technology | Status |
| --- | --- | --- |
| Backend | FastAPI | Current in-memory image/frame prototype |
| Frontend | Server-rendered HTML/JavaScript | Current upload, camera, screen preview, and privacy-safe metrics export |
| CPU detection | OpenCV YuNet | Current web prototype default; synthetic 640x360 pipeline P95 6.92 ms, accuracy pending |
| Reference detection | OpenVINO RetinaFace ResNet50 | Current explicit reference; accuracy validation pending |
| Reference detection | TensorFlow RetinaFace | Current reference adapter; not preferred for live preview |
| GPU detection | YOLO nano with TensorRT | Under evaluation |
| Tracking | SORT or ByteTrack | Under evaluation |
| Face embedding | MobileFaceNet | Under evaluation |
| Whitelist search | FAISS HNSW | Under evaluation |
| CPU optimization | OpenVINO 2026.2.1 | Current prototype trial; about 6 FPS synthetic adapter benchmark |
| GPU optimization | TensorRT | Under evaluation |
| Virtual camera | pyvirtualcam | Under evaluation |
| Anonymization | Gaussian blur | Current image/frame prototype |

## Privacy Requirements

- Face images and embeddings are sensitive biometric data.
- Private datasets must not be committed.
- Logs must not expose identity or biometric information.
- Test assets must be synthetic, public-domain, or explicitly authorized.
- Outputs must not retain sensitive data longer than necessary.
