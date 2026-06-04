param(
    [string]$BaseDataDir = "",
    [string]$RunMode = "open_free_mode",
    [switch]$AllowOxylabs,
    [switch]$AllowPaidRetrieval,
    [switch]$AllowStructuredSeed,
    [switch]$AllowManualImport,
    [string]$Season = "",
    [string]$CutoffDate = "",
    [string]$Team = "",
    [string]$PlayerId = "",
    [switch]$IncludePostseason,
    [switch]$AllowCutoffSensitiveFields,
    [int]$MaxEntities = 32,
    [int]$MaxRequests = 96,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.mlb_completion_backfill", "--run-mode", $RunMode)
if (-not [string]::IsNullOrWhiteSpace($BaseDataDir)) { $ArgsList += @("--base-data-dir", $BaseDataDir) }
if ($AllowOxylabs) { $ArgsList += "--allow-oxylabs" }
if ($AllowPaidRetrieval) { $ArgsList += "--allow-paid-retrieval" }
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if ($AllowManualImport) { $ArgsList += "--allow-manual-import" }
if (-not [string]::IsNullOrWhiteSpace($Season)) { $ArgsList += @("--season", $Season) }
if (-not [string]::IsNullOrWhiteSpace($CutoffDate)) { $ArgsList += @("--cutoff-date", $CutoffDate) }
if (-not [string]::IsNullOrWhiteSpace($Team)) { $ArgsList += @("--team", $Team) }
if (-not [string]::IsNullOrWhiteSpace($PlayerId)) { $ArgsList += @("--player-id", $PlayerId) }
if ($IncludePostseason) { $ArgsList += "--include-postseason" }
if ($AllowCutoffSensitiveFields) { $ArgsList += "--allow-cutoff-sensitive-fields" }
if ($PSBoundParameters.ContainsKey("MaxEntities")) { $ArgsList += @("--max-entities", "$MaxEntities") }
if ($PSBoundParameters.ContainsKey("MaxRequests")) { $ArgsList += @("--max-requests", "$MaxRequests") }
if ($NoPersist) { $ArgsList += "--no-persist" }

python @ArgsList
exit $LASTEXITCODE
