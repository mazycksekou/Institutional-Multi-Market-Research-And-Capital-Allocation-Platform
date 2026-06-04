param(
    [switch]$Persist,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_historical_pattern_lab")
if ($Persist -or -not $NoPersist) {
    $ArgsList += "--persist"
}

python @ArgsList
exit $LASTEXITCODE
