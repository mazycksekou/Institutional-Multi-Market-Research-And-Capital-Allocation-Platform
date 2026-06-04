param(
    [string]$BaseDataDir = "",
    [switch]$NoPersist,
    [switch]$AllowStructuredSeed,
    [switch]$AllowManualImport,
    [int]$MaxEntities = 32,
    [int]$MaxRequests = 96
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_completion_backfill")
if (-not [string]::IsNullOrWhiteSpace($BaseDataDir)) { $ArgsList += @("--base-data-dir", $BaseDataDir) }
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if ($AllowManualImport) { $ArgsList += "--allow-manual-import" }
if ($PSBoundParameters.ContainsKey("MaxEntities")) { $ArgsList += @("--max-entities", "$MaxEntities") }
if ($PSBoundParameters.ContainsKey("MaxRequests")) { $ArgsList += @("--max-requests", "$MaxRequests") }
if (-not $NoPersist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
