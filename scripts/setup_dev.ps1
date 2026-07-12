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
Write-Host "Canonical quality gate:"
Write-Host "  ./.venv/bin/python scripts/run_quality_gates.py --install"
Write-Host "PowerShell alternative:"
Write-Host "  .\.venv\Scripts\python.exe scripts/run_quality_gates.py --install"

