param(
    [switch]$TinyConnectivityCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @(
    "-m",
    "automation_scheduler.kalshi_readonly_readiness",
    "--project-root",
    $RepoRoot
)

if ($TinyConnectivityCheck) {
    $ArgsList += "--tiny-connectivity-check"
}

python @ArgsList
exit $LASTEXITCODE
