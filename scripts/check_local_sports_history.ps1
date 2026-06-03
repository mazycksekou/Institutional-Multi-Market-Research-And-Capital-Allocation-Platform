param(
    [string[]]$ScanRoot = @(),
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.local_sports_history_audit")
if (-not $NoPersist) {
    $ArgsList += "--persist"
}
foreach ($Root in $ScanRoot) {
    if (-not [string]::IsNullOrWhiteSpace($Root)) {
        $ArgsList += @("--scan-root", $Root)
    }
}

python @ArgsList
exit $LASTEXITCODE
