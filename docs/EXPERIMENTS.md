# ProjectBlur Experiments

Record only measured values. Use `Not yet measured` when results do not exist.
Inputs must be synthetic, public-domain, or explicitly authorized.

## EXP-001 — RetinaFace adapter compatibility baseline

- Date: To be confirmed
- Status: Planned
- Related decision: `DEC-001`
- Related research: `research/external_repositories/retinaface.md`
- Hardware: To be confirmed
- Software environment: Python and `retina-face` versions to be confirmed
- Dataset or test input: Authorized evaluation set to be confirmed

### Objective

Confirm that the adapter works with a pinned published package and establish a
reproducible CPU baseline for later detector comparisons.

### Hypothesis

The adapter will normalize valid RetinaFace output without changes to the
ProjectBlur result contract.

### Compared Approaches

- RetinaFace through `RetinaFaceDetector`
- Future YuNet baseline, not yet implemented

### Metrics

- Average latency and P95 latency
- FPS under a defined sequential workload
- CPU and memory usage
- Precision, recall, false positives, and false negatives on an authorized set

### Procedure

To be defined with fixed package versions, hardware metadata, warm-up policy,
input resolution, dataset authorization, and benchmark script path before the
experiment starts.

### Results

Not yet measured.

### Interpretation

Not yet measured.

### Conclusion

Need more testing.

### Artifacts

- Script path: To be created
- Config path: To be created if required
- Result file path: `artifacts/benchmarks/` (planned)
- Chart path: `artifacts/charts/` (planned)
- Log path: To be confirmed; logs must contain no biometric data

## EXP-002 — SIFT recognition baseline comparison

- Date: To be confirmed
- Status: Planned
- Related decision: None; no adoption decision has been made
- Related research: `research/papers/sift_features_for_face_recognition/research_note.md`
- Hardware: To be confirmed
- Software environment: To be confirmed
- Dataset or test input: Authorized evaluation set to be confirmed

### Objective

Determine whether aligned SIFT-based matching provides useful accuracy,
privacy-risk, or CPU trade-offs for ProjectBlur compared with a modern
fixed-size face-embedding baseline.

### Hypothesis

SIFT may tolerate limited scale, rotation, and partial occlusion, but its
variable descriptor count may make whitelist matching slower and less scalable.

### Compared Approaches

- Original SIFT matching on aligned face crops
- PDSIFT-inspired boundary handling, if it can be reproduced faithfully
- A modern embedding baseline to be selected

### Metrics

- Average and P95 latency
- CPU and memory usage
- False authorization and false rejection rates
- Robustness across scale, pose, illumination, occlusion, compression, and blur
- Matching cost as whitelist size increases

### Procedure

To be defined before execution. It must fix alignment, crop padding, feature
settings, matching policy, thresholds, hardware, software versions, input
authorization, and warm-up/repetition rules.

### Results

Not yet measured.

### Interpretation

Not yet measured.

### Conclusion

Need more testing.

### Artifacts

- Script path: To be created
- Config path: To be created if required
- Result file path: `artifacts/benchmarks/` (planned)
- Chart path: `artifacts/charts/` (planned)
- Log path: To be confirmed; logs must contain no identity or biometric data
