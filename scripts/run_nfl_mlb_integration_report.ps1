param(
    [string]$BaseDataDir = "",
    [string]$NflReportPath = "",
    [string]$MlbReportPath = "",
    [string]$NflStatus = "COMPLETE",
    [string]$MlbStatus = "COMPLETE_WITH_POLICY_BLOCKED_SOURCES",
    [string]$IntegrationCommitHash = "",
    [string]$TestsRun = "",
    [string]$TestsPassed = "",
    [string]$TestsFailed = "",
    [switch]$Persist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_mlb_integration_report", "--nfl-status", $NflStatus, "--mlb-status", $MlbStatus)
if (-not [string]::IsNullOrWhiteSpace($BaseDataDir)) { $ArgsList += @("--base-data-dir", $BaseDataDir) }
if (-not [string]::IsNullOrWhiteSpace($NflReportPath)) { $ArgsList += @("--nfl-report-path", $NflReportPath) }
if (-not [string]::IsNullOrWhiteSpace($MlbReportPath)) { $ArgsList += @("--mlb-report-path", $MlbReportPath) }
if (-not [string]::IsNullOrWhiteSpace($IntegrationCommitHash)) { $ArgsList += @("--integration-commit-hash", $IntegrationCommitHash) }
if (-not [string]::IsNullOrWhiteSpace($TestsRun)) { $ArgsList += @("--tests-run", $TestsRun) }
if (-not [string]::IsNullOrWhiteSpace($TestsPassed)) { $ArgsList += @("--tests-passed", $TestsPassed) }
if (-not [string]::IsNullOrWhiteSpace($TestsFailed)) { $ArgsList += @("--tests-failed", $TestsFailed) }
if ($Persist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
