$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project virtual environment not found. Create it with: python -m venv .venv"
}

$env:PYTHONPATH = Join-Path $projectRoot "src"

Push-Location $projectRoot
try {
    & $python -m uvicorn projectblur.web.app:app --reload
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $exitCode
