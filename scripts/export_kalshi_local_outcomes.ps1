$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

python scripts/export_kalshi_local_outcomes.py
exit $LASTEXITCODE
