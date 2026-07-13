$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$modelDirectory = Join-Path $projectRoot "models\opencv\yunet"
$modelPath = Join-Path $modelDirectory "face_detection_yunet_2026may.onnx"
$modelUrl = "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2026may.onnx"
$expectedSha256 = "EBAFCE4E3C118D6554634BE5C27AB333B4C047A9A8C3FAF1D7CF93101C22F0F0"

New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null

if (-not (Test-Path -LiteralPath $modelPath)) {
    Invoke-WebRequest -Uri $modelUrl -OutFile $modelPath
}

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $modelPath).Hash
if ($actualSha256 -ne $expectedSha256) {
    throw "YuNet model hash mismatch at $modelPath. Expected $expectedSha256 but found $actualSha256."
}

Write-Host "YuNet model verified at: $modelPath"
