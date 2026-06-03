param(
    [string]$SourceId = "",
    [string]$Mode = "coverage_report",
    [string]$Season = "",
    [int]$TargetYears = 10,
    [string]$InputPath = "",
    [int]$MaxRecords = 0,
    [bool]$DryRun = $true,
    [switch]$AllowDownload,
    [switch]$PersistPreview,
    [bool]$Resume = $true,
    [string]$SessionId = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.open_sports_history_backfill", "--mode", $Mode, "--target-years", "$TargetYears")
if (-not [string]::IsNullOrWhiteSpace($SourceId)) {
    $ArgsList += @("--source-id", $SourceId)
}
if (-not [string]::IsNullOrWhiteSpace($Season)) {
    $ArgsList += @("--season", $Season)
}
if (-not [string]::IsNullOrWhiteSpace($InputPath)) {
    $ArgsList += @("--input-path", $InputPath)
}
if ($MaxRecords -gt 0) {
    $ArgsList += @("--max-records", "$MaxRecords")
}
if ($DryRun) {
    $ArgsList += "--dry-run"
} else {
    $ArgsList += "--no-dry-run"
}
if ($AllowDownload) {
    $ArgsList += "--allow-download"
}
if ($PersistPreview) {
    $ArgsList += "--persist-preview"
}
if ($Resume) {
    $ArgsList += "--resume"
} else {
    $ArgsList += "--no-resume"
}
if (-not [string]::IsNullOrWhiteSpace($SessionId)) {
    $ArgsList += @("--session-id", $SessionId)
}

python @ArgsList
exit $LASTEXITCODE
