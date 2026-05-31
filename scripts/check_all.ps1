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

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    $BaseUrl = "https://betting-stock-api-code-integration.onrender.com"
}

python scripts/ops_check.py --mode full --base-url $BaseUrl --output text --write-report
exit $LASTEXITCODE

