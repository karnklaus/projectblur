$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$converterEnvironment = Join-Path $projectRoot ".omz-venv"
$converterPython = Join-Path $converterEnvironment "Scripts\python.exe"
$downloader = Join-Path $converterEnvironment "Scripts\omz_downloader.exe"
$converter = Join-Path $converterEnvironment "Scripts\omz_converter.exe"
$downloadDirectory = Join-Path $projectRoot "models\openvino"
$outputDirectory = Join-Path $downloadDirectory "ir"
$modelOptimizer = Join-Path $converterEnvironment "Lib\site-packages\openvino\tools\mo\mo.py"

if (-not (Test-Path -LiteralPath $converterPython)) {
    python -m venv $converterEnvironment
}

& $converterPython -m pip install `
    "openvino-dev[pytorch]==2024.6.0" `
    "torch==2.13.0" `
    "torchvision==0.28.0" `
    "onnx==1.22.0" `
    "onnxscript==0.7.1"

& $downloader `
    --name retinaface-resnet50-pytorch `
    --output_dir $downloadDirectory

& $converter `
    --name retinaface-resnet50-pytorch `
    --download_dir $downloadDirectory `
    --output_dir $outputDirectory `
    --precisions FP16 `
    --mo $modelOptimizer

$modelPath = Join-Path $outputDirectory `
    "public\retinaface-resnet50-pytorch\FP16\retinaface-resnet50-pytorch.xml"

if (-not (Test-Path -LiteralPath $modelPath)) {
    throw "OpenVINO RetinaFace conversion did not produce the expected model: $modelPath"
}

Write-Host "OpenVINO RetinaFace model prepared at: $modelPath"
