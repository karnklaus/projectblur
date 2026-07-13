# OpenVINO RetinaFace

## Sources

- OpenVINO: https://github.com/openvinotoolkit/openvino
- Open Model Zoo: https://github.com/openvinotoolkit/open_model_zoo
- Model entry: `retinaface-resnet50-pytorch`
- Original implementation: https://github.com/biubug6/Pytorch_Retinaface
- Accessed: 2026-07-14

## Project Usage

ProjectBlur uses OpenVINO Runtime through a project-owned adapter. The official
Open Model Zoo downloader and converter prepare the RetinaFace ResNet50 model
locally. Third-party source is not copied into the ProjectBlur production
package.

## Versions Evaluated

- Runtime: `openvino 2026.2.1`
- Conversion tools: `openvino-dev 2024.6.0`
- Model precision: FP16-compressed OpenVINO IR
- Model input: `1x3x640x640`

OpenVINO Development Tools is deprecated and is used only in the isolated local
conversion environment. It is not a production dependency.

## Local Artifact Policy

Model weights, ONNX graphs, IR XML/BIN files, and the conversion environment
remain local and are ignored by Git. Authorized users can reproduce them with
`scripts/prepare_openvino_retinaface.ps1`.

## License Notes

- OpenVINO and Open Model Zoo report Apache License 2.0.
- The Open Model Zoo entry identifies the original RetinaFace model license as
  MIT.
- Preserve the terms and attribution of the runtime, conversion tools, original
  model implementation, and checkpoint separately.
- Recheck redistribution terms before publishing any model artifact.
