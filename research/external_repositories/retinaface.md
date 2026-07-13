# RetinaFace

## Source

- Repository: https://github.com/serengil/retinaface
- Package: `retina-face`
- Type: External open-source dependency
- Purpose: Face detection evaluation and possible ProjectBlur integration

## Project Usage

ProjectBlur uses RetinaFace through the published Python package and a
project-specific adapter.

The upstream repository source code is not copied directly into the main
ProjectBlur source directory. Project-specific integration code is maintained
separately inside the detection module.

## Integration Rule

- Keep third-party library code separate from ProjectBlur code.
- Use an adapter in the detection module.
- Lock the tested package version after validation.
- Record the tested version and evaluation date.
- Preserve license and attribution.

## Status

- Evaluation status: Runtime evaluation pending
- Adapter status: Implemented
- Tested package version: To be confirmed
- Evaluated date: To be confirmed
- Relevant implementation path: `src/projectblur/detection/retinaface_detector.py`
- Relevant test path: `tests/detection/test_retinaface_detector.py`

## License and Attribution

RetinaFace is an external open-source project. Its upstream license,
repository, authorship, and attribution must be preserved when used,
modified, or redistributed.

Check the upstream repository license before distributing modified source code.

The upstream repository reports an MIT license. Check the upstream repository
license before copying, modifying, distributing, or embedding source code, and
preserve its authorship and attribution.
