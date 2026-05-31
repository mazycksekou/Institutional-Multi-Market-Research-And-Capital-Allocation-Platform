Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if (Test-Path "requirements-dev.txt") {
    python -m pip install -r requirements-dev.txt
}

Write-Host ""
Write-Host "Developer environment is ready."
Write-Host "Next commands:"
Write-Host "  .\scripts\check_local.ps1"
Write-Host "  .\scripts\check_render.ps1"
Write-Host "  .\scripts\check_cron.ps1"
Write-Host "  .\scripts\check_all.ps1"
Write-Host "  .\scripts\run_tests.ps1 -Mode quick"

