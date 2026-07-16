[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$nativeRoot = Join-Path $projectRoot 'native\virtual_camera'
$packagesConfig = Join-Path $nativeRoot 'media_source\packages.config'
$packagesDirectory = Join-Path $nativeRoot 'packages'

$nuget = Get-Command 'nuget.exe' -ErrorAction SilentlyContinue
if ($null -eq $nuget) {
    $wingetPackages = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages'
    $nuget = Get-ChildItem -LiteralPath $wingetPackages -Filter 'nuget.exe' -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1
}
if ($null -eq $nuget) {
    throw 'NuGet CLI was not found. Install Microsoft.NuGet with WinGet or place nuget.exe on PATH.'
}
$nugetPath = if ($nuget.Path) { $nuget.Path } else { $nuget.FullName }

$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (-not (Test-Path -LiteralPath $vswhere -PathType Leaf)) {
    throw 'vswhere.exe was not found. Install Visual Studio 2022 Build Tools with Desktop development with C++.'
}
$msbuild = & $vswhere -latest -products '*' -requires Microsoft.Component.MSBuild -find 'MSBuild\**\Bin\MSBuild.exe' |
    Select-Object -First 1
if (-not $msbuild) {
    throw 'MSBuild was not found in a Visual Studio 2022 installation.'
}

& $nugetPath install $packagesConfig -OutputDirectory $packagesDirectory -NonInteractive
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$projects = @(
    (Join-Path $nativeRoot 'media_source\ProjectBlurMediaSource.vcxproj'),
    (Join-Path $nativeRoot 'control\ProjectBlurCameraControl.vcxproj')
)
foreach ($project in $projects) {
    & $msbuild $project /m "/p:Configuration=$Configuration" /p:Platform=x64 /v:minimal
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$buildDirectory = Join-Path $nativeRoot "build\$Configuration"
Write-Output "build_directory=$buildDirectory"
