param(
    [string]$SourceId = "",
    [string]$Mode = "coverage_report",
    [string]$Season = "2024",
    [int]$MaxRecords = 25,
    [switch]$AllowDownload,
    [int]$MaxFullAssets = 0,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_open_data_backfill", "--mode", $Mode, "--season", $Season, "--max-records", "$MaxRecords")
if (-not [string]::IsNullOrWhiteSpace($SourceId)) {
    $ArgsList += @("--source-id", $SourceId)
}
if ($AllowDownload) {
    $ArgsList += "--allow-download"
}
if ($MaxFullAssets -gt 0) {
    $ArgsList += @("--max-full-assets", "$MaxFullAssets")
}
if (-not $NoPersist) {
    $ArgsList += "--persist"
}

python @ArgsList
exit $LASTEXITCODE
