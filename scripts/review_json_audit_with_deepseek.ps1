$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

python scripts/review_json_audit_with_deepseek.py @args
exit $LASTEXITCODE
