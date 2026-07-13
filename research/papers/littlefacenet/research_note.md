# LittleFaceNet Research Note

## Paper

LittleFaceNet: A Small-Sized Face Recognition Method Based on RetinaFace and AdaFace

## Purpose

This paper studies face recognition in surveillance environments where faces may be small, low-resolution, occluded, viewed from difficult angles, or affected by motion blur.

## Main Components

### Improved RetinaFace

Uses SPD-Conv to preserve spatial information during downsampling and improve small-face detection.

### AdaFace

Uses image-quality-aware adaptive margins for face recognition. This can improve recognition when face crops have inconsistent quality.

### ByteTrack

Maintains face tracks across video frames, including during temporary occlusion and low-confidence detections.

## Reported Results

- 96.12% face-detection accuracy on WIDER FACE
- 84.36% recognition accuracy in a university laboratory surveillance environment
- Some failures occurred with infrared footage and motion-blurred faces

These are results reported by the paper, not measurements from ProjectBlur.

## Relevance to Face Privacy AI

This paper is relevant to the whitelist recognition stage of the real-time face-blurring system.

Potential applications:

- Use ByteTrack to maintain persistent face IDs
- Cache whitelist decisions by Track ID
- Evaluate recognition performance at different face sizes and distances
- Test low light, occlusion, pose, infrared video, and motion blur
- Compare MobileFaceNet with AdaFace
- Define a minimum usable face size for whitelist recognition
- Blur by default when recognition confidence is insufficient

## Architectural Interpretation

Do not directly copy the paper's recognition-first behavior.

For Face Privacy AI, use the fail-safe policy:

1. Detect every visible face
2. Blur unknown and unverified faces by default
3. Remove blur only after a sufficiently reliable whitelist match
4. Continue blurring when the face is too small, unclear, occluded, or below the confidence threshold

## Comparison with Current Architecture

| Current Face Privacy AI Design | LittleFaceNet Paper |
|---|---|
| YuNet or YOLO face detector | Improved RetinaFace with SPD-Conv |
| MobileFaceNet embeddings | AdaFace recognition |
| SORT or ByteTrack | ByteTrack |
| Whitelist decision cached by Track ID | Tracking preserves identity across frames |
| Privacy-preserving selective blurring | Low-resolution surveillance recognition |

## Recommended Next Steps

1. Keep the current YuNet baseline for CPU testing
2. Add ByteTrack before changing the recognition model
3. Create a small-face and low-quality evaluation dataset
4. Measure false acceptance and false rejection rates
5. Compare MobileFaceNet and AdaFace under identical conditions
6. Always fall back to blur when recognition is uncertain

## Source

- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11766931/
- Accessed: 2026-07-13
