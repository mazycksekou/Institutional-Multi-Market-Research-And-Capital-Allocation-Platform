param(
    [switch]$ConfirmPersist,
    [string]$BaseUrl = $env:APP_BASE_URL,
    [string]$CollectorToken = $env:COLLECTOR_CRON_TOKEN
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $ConfirmPersist) {
    throw "Refusing to persist without -ConfirmPersist."
}
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    throw "APP_BASE_URL is required for Render persist import."
}
if ([string]::IsNullOrWhiteSpace($CollectorToken)) {
    throw "COLLECTOR_CRON_TOKEN is required for persist import."
}

$PackagePath = "data\outcomes\migration\kalshi_local_outcomes_migration.latest.json"
if (-not (Test-Path $PackagePath)) {
    throw "Migration package not found: $PackagePath. Run scripts\export_kalshi_local_outcomes.ps1 first."
}

$Package = Get-Content $PackagePath -Raw | ConvertFrom-Json
$Request = [ordered]@{
    dry_run = $false
    persist = $true
    source = "local_repo_migration"
    migration_version = $Package.migration_version
    records = @($Package.records)
    supporting_paper_decisions = @($Package.supporting_paper_decisions)
}
$Headers = @{ "X-Collector-Token" = $CollectorToken }
$Uri = "$($BaseUrl.TrimEnd('/'))/api/automation/outcomes/import-local-settlements"
$Response = Invoke-RestMethod -Uri $Uri -Method Post -Headers $Headers -Body ($Request | ConvertTo-Json -Depth 20) -ContentType "application/json" -TimeoutSec 60
$Response | ConvertTo-Json -Depth 12
