param(
    [string]$BaseDataDir = "",
    [string]$RunMode = "open_free_mode",
    [switch]$AllowOxylabs,
    [switch]$AllowPaidRetrieval,
    [string]$Season = "",
    [string]$CutoffDate = "",
    [string]$Team = "",
    [string]$PlayerId = "",
    [switch]$IncludePostseason,
    [switch]$AllowCutoffSensitiveFields,
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

$ArgsList = @("-m", "automation_scheduler.mlb_completion_report", "--run-mode", $RunMode)
if (-not [string]::IsNullOrWhiteSpace($BaseDataDir)) { $ArgsList += @("--base-data-dir", $BaseDataDir) }
if ($AllowOxylabs) { $ArgsList += "--allow-oxylabs" }
if ($AllowPaidRetrieval) { $ArgsList += "--allow-paid-retrieval" }
if (-not [string]::IsNullOrWhiteSpace($Season)) { $ArgsList += @("--season", $Season) }
if (-not [string]::IsNullOrWhiteSpace($CutoffDate)) { $ArgsList += @("--cutoff-date", $CutoffDate) }
if (-not [string]::IsNullOrWhiteSpace($Team)) { $ArgsList += @("--team", $Team) }
if (-not [string]::IsNullOrWhiteSpace($PlayerId)) { $ArgsList += @("--player-id", $PlayerId) }
if ($IncludePostseason) { $ArgsList += "--include-postseason" }
if ($AllowCutoffSensitiveFields) { $ArgsList += "--allow-cutoff-sensitive-fields" }
if (-not [string]::IsNullOrWhiteSpace($CommitHash)) { $ArgsList += @("--commit-hash", $CommitHash) }
if (-not [string]::IsNullOrWhiteSpace($TestsRun)) { $ArgsList += @("--tests-run", $TestsRun) }
if (-not [string]::IsNullOrWhiteSpace($TestsPassed)) { $ArgsList += @("--tests-passed", $TestsPassed) }
if ($Persist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
