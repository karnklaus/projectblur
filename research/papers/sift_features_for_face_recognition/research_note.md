# SIFT Features for Face Recognition

## Bibliographic Information

- Title: SIFT Features for Face Recognition
- Authors: Cong Geng and Xudong Jiang
- Published: 2009
- DOI: https://doi.org/10.1109/ICCSIT.2009.5234877
- Local paper (not committed; redistribution permission not confirmed):
  `research/papers/sift_features_for_face_recognition/paper.pdf`
- Review status: Abstract and available metadata reviewed; full local PDF text
  extraction was unavailable in the current development environment

## Research Question

The paper examines whether the original Scale-Invariant Feature Transform
(SIFT), which was designed for general object recognition, is suitable for face
recognition and how its face-specific weaknesses can be reduced.

## Methods

The paper proposes two adaptations:

- **Keypoints-Preserving-SIFT (KPSIFT):** retains all initially detected
  keypoints as features.
- **Partial-Descriptor-SIFT (PDSIFT):** uses partial descriptors for large-scale
  keypoints and keypoints near face boundaries, where a complete descriptor may
  include irrelevant image content.

The reported experiments compare SIFT, KPSIFT, and PDSIFT with holistic methods
including Fisherface (FLDA), a null-space approach (NLDA), and Eigenfeature
Regularization and Extraction (ERE) on the ORL and AR face databases.

## Reported Findings

According to the paper abstract, KPSIFT and PDSIFT outperform original SIFT in
the reported experiments. PDSIFT reportedly performs better than FLDA and NLDA
and reaches performance comparable to or better than ERE on the evaluated
datasets. These historical results must not be treated as ProjectBlur results.

## Relevance to ProjectBlur

SIFT may be useful as an experimental, non-neural recognition baseline for
small whitelists or CPU-oriented/offline evaluation. Its local descriptors may
also provide a secondary similarity signal when scale, limited rotation,
partial occlusion, or local facial detail matters.

The paper also supports several pipeline design considerations:

- Detect and align faces before extracting recognition features.
- Use RetinaFace landmarks to create consistent aligned crops.
- Treat descriptors near crop boundaries carefully because they may include
  background or incomplete facial structure.
- Evaluate region-aware or partial descriptors rather than assuming unmodified
  SIFT is optimal for faces.
- Keep recognition behind an adapter so SIFT can be compared with modern
  embedding methods without changing whitelist business logic.

## Possible ProjectBlur Flow

This is an experiment proposal, not current architecture:

```text
RetinaFace detection
        -> landmark-based alignment
        -> SIFT or PDSIFT-style local descriptors
        -> keypoint matching
        -> whitelist similarity decision
        -> keep visible or anonymize
```

For privacy-safe behavior, uncertainty or infrastructure failure must not cause
an unknown face to bypass anonymization.

## Limitations and Risks

- The paper was published in 2009 and evaluates older controlled datasets.
- Its results do not establish performance on CCTV, compressed video, motion
  blur, low-resolution faces, or ProjectBlur target hardware.
- SIFT produces a variable number of high-dimensional local descriptors, which
  can increase matching time and storage compared with fixed-size embeddings.
- Direct keypoint matching may not scale well to a large whitelist.
- The approach must be benchmarked against modern embedding candidates such as
  MobileFaceNet or ArcFace before adoption.
- Dataset, implementation, patent-history, and dependency license constraints
  require review before distribution or deployment.

## Proposed Evaluation

Evaluate SIFT only as an `Under evaluation` recognition approach. A reproducible
experiment should compare it with a modern embedding baseline using authorized
inputs and measure:

- Average and P95 latency
- CPU and memory usage
- False authorization rate
- False rejection rate
- Robustness to scale, pose, illumination, occlusion, compression, and blur
- Whitelist-size scaling

False authorization is the critical privacy failure: an unauthorized face is
incorrectly left visible. Thresholds must therefore be calibrated for the
ProjectBlur anonymization policy rather than copied from the paper.

## Decision Status

- Research status: Reviewed
- Implementation status: Not implemented
- Architecture status: Under evaluation
- Benchmark status: Not yet measured
- Decision: No adoption decision; evidence is insufficient without a current,
  reproducible ProjectBlur experiment
