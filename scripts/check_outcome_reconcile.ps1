param(
    [string]$BaseUrl = $env:APP_BASE_URL
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

python scripts/ops_check.py --mode outcome-reconcile --base-url $BaseUrl --output text --write-report
exit $LASTEXITCODE
