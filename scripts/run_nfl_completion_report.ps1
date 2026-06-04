param(
    [string]$BaseDataDir = "",
    [string]$RunMode = "open_free_mode",
    [string]$CommitHash = "",
    [string]$TestsRun = "",
    [string]$TestsPassed = "",
    [switch]$Persist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_completion_report", "--run-mode", $RunMode)
if (-not [string]::IsNullOrWhiteSpace($BaseDataDir)) { $ArgsList += @("--base-data-dir", $BaseDataDir) }
if (-not [string]::IsNullOrWhiteSpace($CommitHash)) { $ArgsList += @("--commit-hash", $CommitHash) }
if (-not [string]::IsNullOrWhiteSpace($TestsRun)) { $ArgsList += @("--tests-run", $TestsRun) }
if (-not [string]::IsNullOrWhiteSpace($TestsPassed)) { $ArgsList += @("--tests-passed", $TestsPassed) }
if ($Persist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
