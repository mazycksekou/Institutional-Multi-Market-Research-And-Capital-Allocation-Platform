param(
    [string]$BaseDataDir = "",
    [switch]$AllowOxylabs,
    [switch]$AllowPaidRetrieval,
    [switch]$Persist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_mlb_active_discovery", "--sport", "all")
if ($AllowOxylabs) { $ArgsList += "--allow-oxylabs" }
if ($AllowPaidRetrieval) { $ArgsList += "--allow-paid-retrieval" }
if ($Persist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE

