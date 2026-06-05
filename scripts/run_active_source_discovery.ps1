param(
    [string]$Sport = "all",
    [string]$Lane = "",
    [string]$SeasonStart = "",
    [string]$SeasonEnd = "",
    [switch]$DiscoveryOnly,
    [switch]$NoNetwork,
    [switch]$DryRun,
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

$ArgsList = @("-m", "automation_scheduler.nfl_mlb_active_discovery", "--sport", $Sport)
if ($AllowOxylabs -and -not $NoNetwork) { $ArgsList += "--allow-oxylabs" }
if ($AllowPaidRetrieval -and -not $NoNetwork) { $ArgsList += "--allow-paid-retrieval" }
if ($Persist -and -not $DryRun) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE

