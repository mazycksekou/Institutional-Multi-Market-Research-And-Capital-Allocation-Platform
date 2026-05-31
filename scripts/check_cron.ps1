param(
    [switch]$WithRender,
    [string]$BaseUrl = $env:APP_BASE_URL
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

python scripts/ops_check.py --mode cron --output text --write-report
$CronExit = $LASTEXITCODE
if ($CronExit -ne 0) {
    exit $CronExit
}

if ($WithRender) {
    if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
        $BaseUrl = "https://betting-stock-api-code-integration.onrender.com"
    }
    python scripts/ops_check.py --mode render --base-url $BaseUrl --output text --write-report
    exit $LASTEXITCODE
}

exit 0

