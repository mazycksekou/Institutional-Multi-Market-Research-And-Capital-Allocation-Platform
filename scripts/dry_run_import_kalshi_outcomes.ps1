param(
    [string]$BaseUrl = $env:APP_BASE_URL
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

python scripts/dry_run_import_kalshi_outcomes.py --base-url $BaseUrl
exit $LASTEXITCODE
