param(
    [string]$Module = "",
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.data_availability_tiers")
if (-not $NoPersist) {
    $ArgsList += "--persist"
}
if (-not [string]::IsNullOrWhiteSpace($Module)) {
    $ArgsList += @("--module", $Module)
}

python @ArgsList
exit $LASTEXITCODE

