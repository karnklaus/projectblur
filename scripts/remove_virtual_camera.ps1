[CmdletBinding()]
param(
    [string]$InstallDirectory = (Join-Path $env:ProgramFiles 'ProjectBlur\VirtualCamera')
)

$ErrorActionPreference = 'Stop'
$control = Join-Path $InstallDirectory 'ProjectBlurCameraControl.exe'
if (-not (Test-Path -LiteralPath $control -PathType Leaf)) {
    throw "ProjectBlur virtual-camera control was not found at $control"
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'This remover must be run as administrator.'
}

& $control remove --machine-com
exit $LASTEXITCODE
