param(
    [switch]$ConfirmPersist,
    [string]$BaseUrl = $env:APP_BASE_URL,
    [string]$CollectorToken = $env:COLLECTOR_CRON_TOKEN
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $ConfirmPersist) {
    throw "Refusing to persist without -ConfirmPersist."
}

python scripts/persist_import_kalshi_outcomes.py --confirm-persist --base-url $BaseUrl --collector-token $CollectorToken
exit $LASTEXITCODE
