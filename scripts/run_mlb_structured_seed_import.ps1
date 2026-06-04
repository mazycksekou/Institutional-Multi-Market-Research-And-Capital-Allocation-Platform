param(
    [string]$SourceId = "wikidata_mlb_seed",
    [string]$Gate = "structured_seed_import",
    [switch]$AllowStructuredSeed,
    [int]$MaxRecords = 25,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.mlb_structured_seed_adapters", "--source-id", $SourceId, "--gate", $Gate, "--max-records", "$MaxRecords")
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if (-not $NoPersist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
