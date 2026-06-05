param(
    [string]$BaseDataDir = "",
    [switch]$Persist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

python -m automation_scheduler.nfl_mlb_active_discovery --sport all $(if ($Persist) { "--persist" })
exit $LASTEXITCODE

