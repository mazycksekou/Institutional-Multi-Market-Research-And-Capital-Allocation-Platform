param(
    [switch]$DryRun,
    [switch]$PredictionMarketOutcomeCheck,
    [switch]$AllowTinyProviderCalls,
    [int]$MaxProviderCalls = 0,
    [int]$MaxRecords = 0,
    [string]$Module = "",
    [string]$SourceId = "",
    [switch]$NoDeepSeek
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $PSBoundParameters.ContainsKey("DryRun")) {
    $DryRun = $true
}

if (-not [bool]$DryRun) {
    Write-Error "deepseek_data_pull_check.ps1 only supports dry-run mode. Re-run with -DryRun."
    exit 2
}

if ($MaxProviderCalls -lt 0) {
    $MaxProviderCalls = 0
}
if ($MaxRecords -lt 0) {
    $MaxRecords = 0
}
if ($MaxProviderCalls -gt 3) {
    Write-Host "Capping MaxProviderCalls at 3."
    $MaxProviderCalls = 3
}
if ($MaxRecords -gt 5) {
    Write-Host "Capping MaxRecords at 5."
    $MaxRecords = 5
}
if (-not $AllowTinyProviderCalls) {
    $MaxProviderCalls = 0
    $MaxRecords = 0
}

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

if ([string]::IsNullOrWhiteSpace($env:APP_BASE_URL)) {
    $env:APP_BASE_URL = "https://betting-stock-api-code-integration.onrender.com"
}

Write-Host "Running local compact safety check."
& ".\scripts\check_local.ps1"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Running Render compact safety check."
& ".\scripts\check_render.ps1" -BaseUrl $env:APP_BASE_URL
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Running data availability tier check."
$TierArgs = @()
if (-not [string]::IsNullOrWhiteSpace($Module)) {
    $TierArgs += @("-Module", $Module)
}
& ".\scripts\check_data_availability_tiers.ps1" @TierArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$HelperArgs = @(
    "-m",
    "automation_scheduler.deepseek_data_pull_check",
    "--persist",
    "--dry-run",
    "--app-base-url",
    $env:APP_BASE_URL,
    "--max-provider-calls",
    [string]$MaxProviderCalls,
    "--max-records",
    [string]$MaxRecords
)

if ($PredictionMarketOutcomeCheck) {
    $HelperArgs += "--prediction-market-outcome-check"
}
if ($AllowTinyProviderCalls) {
    $HelperArgs += "--allow-tiny-provider-calls"
}
if ($NoDeepSeek) {
    $HelperArgs += "--no-deepseek"
}
if (-not [string]::IsNullOrWhiteSpace($Module)) {
    $HelperArgs += @("--module", $Module)
}
if (-not [string]::IsNullOrWhiteSpace($SourceId)) {
    $HelperArgs += @("--source-id", $SourceId)
}

python @HelperArgs
exit $LASTEXITCODE
