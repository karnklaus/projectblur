[CmdletBinding()]
param(
    [string]$InstallDirectory = (Join-Path $env:ProgramFiles 'ProjectBlur\VirtualCamera')
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$buildDirectory = Join-Path $projectRoot 'native\virtual_camera\build\Release'
$sourceDll = Join-Path $buildDirectory 'ProjectBlurMediaSource.dll'
$sourceControl = Join-Path $buildDirectory 'ProjectBlurCameraControl.exe'

if (-not (Test-Path -LiteralPath $sourceDll -PathType Leaf) -or
    -not (Test-Path -LiteralPath $sourceControl -PathType Leaf)) {
    throw 'Build the Release virtual-camera targets before installing.'
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'This installer must be run as administrator.'
}

New-Item -ItemType Directory -Path $InstallDirectory -Force | Out-Null
$installedDll = Join-Path $InstallDirectory 'ProjectBlurMediaSource.dll'
$installedControl = Join-Path $InstallDirectory 'ProjectBlurCameraControl.exe'

$frameServer = Get-Service -Name 'FrameServer' -ErrorAction SilentlyContinue
$restartFrameServer = $null -ne $frameServer -and $frameServer.Status -eq 'Running'
if ($restartFrameServer) {
    Stop-Service -Name 'FrameServer' -Force
}
try {
    Copy-Item -LiteralPath $sourceDll -Destination $installedDll -Force
    Copy-Item -LiteralPath $sourceControl -Destination $installedControl -Force
} finally {
    if ($restartFrameServer) {
        Start-Service -Name 'FrameServer'
    }
}

& $installedControl install --dll $installedDll --machine-com
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output "installed_directory=$InstallDirectory"
