param(
    [Parameter(Mandatory = $true)]
    [string]$SourceId,
    [string]$Season = "",
    [string]$InputPath = "",
    [int]$MaxRecords = 25,
    [bool]$DryRun = $true,
    [switch]$AllowDownload,
    [switch]$PersistPreview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.open_sports_history_import", "--source-id", $SourceId, "--max-records", "$MaxRecords")
if (-not [string]::IsNullOrWhiteSpace($Season)) {
    $ArgsList += @("--season", $Season)
}
if (-not [string]::IsNullOrWhiteSpace($InputPath)) {
    $ArgsList += @("--input-path", $InputPath)
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

python @ArgsList
exit $LASTEXITCODE
