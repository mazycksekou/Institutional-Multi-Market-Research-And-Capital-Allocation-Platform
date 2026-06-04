param(
    [string]$SourceId = "",
    [string]$Mode = "coverage_report",
    [string]$Season = "2025",
    [int]$MaxRecords = 25,
    [switch]$AllowDownload,
    [int]$MaxFullAssets = 0,
    [string]$StartSeason = "",
    [string]$EndSeason = "",
    [string]$SessionId = "",
    [switch]$Resume,
    [switch]$NoPersist,
    [switch]$AllowStructuredSeed,
    [switch]$AllowManualImport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.mlb_open_data_backfill", "--mode", $Mode, "--season", $Season, "--max-records", "$MaxRecords")
if (-not [string]::IsNullOrWhiteSpace($SourceId)) { $ArgsList += @("--source-id", $SourceId) }
if ($AllowDownload) { $ArgsList += "--allow-download" }
if ($MaxFullAssets -gt 0) { $ArgsList += @("--max-full-assets", "$MaxFullAssets") }
if (-not [string]::IsNullOrWhiteSpace($StartSeason)) { $ArgsList += @("--start-season", $StartSeason) }
if (-not [string]::IsNullOrWhiteSpace($EndSeason)) { $ArgsList += @("--end-season", $EndSeason) }
if (-not [string]::IsNullOrWhiteSpace($SessionId)) { $ArgsList += @("--session-id", $SessionId) }
if ($Resume) { $ArgsList += "--resume" }
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if ($AllowManualImport) { $ArgsList += "--allow-manual-import" }
if (-not $NoPersist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
