# dlib Research Note

## Source

- Project website: https://dlib.net/
- Python API: https://dlib.net/python/
- Type: External open-source C++ toolkit with Python bindings
- Current ProjectBlur status: Under evaluation as a learning and benchmark
  baseline
- ProjectBlur implementation: None

## Why It Is Relevant

dlib provides examples for most stages of a classical face-recognition
pipeline: face detection, landmark estimation, alignment, descriptor
generation, distance-based comparison, and object tracking. This makes it
useful for understanding and benchmarking an end-to-end whitelist workflow
before ProjectBlur selects production components.

dlib must not be described as ProjectBlur's current implementation. The only
implemented detector integration in ProjectBlur is the RetinaFace adapter.

## Relevant Components

### Face Detection

dlib provides two relevant detector approaches:

- `get_frontal_face_detector()` uses FHOG features with a linear classifier,
  image pyramid, and sliding-window detection.
- `cnn_face_detection_model_v1` loads a CNN/MMOD face detector. The official
  example describes it as more accurate than the HOG example but substantially
  more computationally expensive and intended for GPU use at reasonable speed.

The HOG detector must not be assumed to handle small, distant, occluded, or
strongly non-frontal surveillance faces without ProjectBlur-specific tests.

Official examples:

- https://dlib.net/opencv_webcam_face_detection.py.html
- https://dlib.net/cnn_face_detector.py.html

### Facial Landmarks and Alignment

dlib supports shape-predictor models for facial landmarks. Its landmark example
uses a 68-point model, while its face-recognition example uses a 5-point model
for alignment. Aligned face chips are rotated, centered, and scaled before
descriptor extraction.

This demonstrates why ProjectBlur should align whitelist candidates
consistently before comparing embeddings.

Official examples:

- https://dlib.net/face_landmark_detection.py.html
- https://dlib.net/face_recognition.py.html

### Face Recognition

The official recognition model maps an aligned face to a 128-dimensional
descriptor. The example compares descriptors using Euclidean distance and uses
`0.6` as the decision threshold the network was trained to use.

The official example reports 99.38% accuracy on LFW when using 100 jittered
samples, but also states that this configuration makes descriptor extraction
approximately 100 times slower. This historical benchmark is not evidence of
ProjectBlur performance, CCTV accuracy, or a safe whitelist threshold.

ProjectBlur must calibrate its own threshold using authorized, representative
inputs. False authorization—leaving an unauthorized face visible—is the
privacy-critical failure.

Official example:

- https://dlib.net/face_recognition.py.html

### Correlation Tracking

`dlib.correlation_tracker` accepts an initial bounding box and updates the
estimated position in later video frames. It demonstrates the basic
detection-by-tracking concept.

It is not a direct substitute for ByteTrack. A correlation tracker alone does
not supply multi-object data association, automatic track creation/deletion,
persistent identity management, or robust re-identification after a lost track.

Official example:

- https://dlib.net/correlation_tracker.py.html

## Baseline Pipeline for ProjectBlur

This is a proposed experiment, not current architecture:

```text
Input frame
    -> dlib face detection
    -> facial landmarks
    -> aligned face chip
    -> 128-D face descriptor
    -> calibrated whitelist comparison
    -> authorized: remove blur
    -> unknown, uncertain, or failed: keep blur
```

The privacy-safe policy differs from a recognition-first demonstration:

1. Detect and anonymize visible faces by default.
2. Attempt alignment and recognition only after detection.
3. Remove anonymization only after a sufficiently reliable whitelist match.
4. Keep anonymization when detection, alignment, tracking, or recognition is
   uncertain or unavailable.

## Comparison with Evaluated ProjectBlur Technologies

| Stage | dlib baseline | ProjectBlur status |
| --- | --- | --- |
| Detection | FHOG or CNN/MMOD | RetinaFace adapter is current; YuNet/YOLO are under evaluation |
| Alignment | 5-point or 68-point shape predictor | Planned; detector landmarks may be used |
| Recognition | dlib ResNet, 128-D descriptor | MobileFaceNet and AdaFace are under evaluation |
| Tracking | Correlation tracker | SORT and ByteTrack are under evaluation |
| Whitelist search | Linear Euclidean-distance comparison | Search method and threshold are undecided |
| Optimization | Native C++ with Python bindings; optional GPU paths | OpenVINO and TensorRT are under evaluation |

This comparison does not establish that either side is faster or more accurate.
Those claims require measurements on identical inputs and hardware.

## Recommended Evaluation

Use dlib as a learning reference and reproducible baseline rather than replacing
the architecture immediately. Compare:

- FHOG and CNN detection against RetinaFace and a CPU-oriented detector
- dlib descriptors against a selected modern embedding baseline
- dlib correlation tracking against a multi-object tracker
- Average and P95 latency
- CPU, GPU, and memory usage
- Small-face and difficult-pose detection recall
- False authorization and false rejection rates
- Behavior under low light, infrared, compression, occlusion, and motion blur
- Scaling as the number of simultaneous faces and whitelist entries increases

No performance result has been measured by ProjectBlur yet.

## Licensing and Distribution Risks

dlib's library source uses the Boost Software License. Examples and downloaded
model assets may have separate terms. In particular, the official 68-point
landmark example warns that its model was trained on the iBUG 300-W dataset,
whose license excludes commercial use. ProjectBlur must review the library,
each pretrained model, and its training-data terms independently before
redistribution or deployment.

Do not copy the dlib repository into `src`. If evaluated in code, use the
published dependency behind ProjectBlur-owned adapters and record the tested
version and model checksums.

## Decision Status

- Research status: Reviewed
- Architecture status: Under evaluation
- Dependency status: Not added
- Implementation status: Not implemented
- Benchmark status: Not yet measured
- Adoption decision: None

## Access Information

- Accessed: 2026-07-13
- Official site release shown at access time: dlib 20.0
