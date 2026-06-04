param(
    [Parameter(Mandatory = $true)][int]$Season,
    [Parameter(Mandatory = $true)][int]$CutoffWeek,
    [string]$Team,
    [string]$PlayerId,
    [switch]$IncludePostseason,
    [switch]$AllowCutoffSensitiveFields,
    [string]$SourceLanes,
    [int]$MaxRecords,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @(
    "-m", "automation_scheduler.nfl_cutoff_week_features",
    "--season", "$Season",
    "--cutoff-week", "$CutoffWeek"
)
if ($Team) { $ArgsList += @("--team", $Team) }
if ($PlayerId) { $ArgsList += @("--player-id", $PlayerId) }
if ($IncludePostseason) { $ArgsList += "--include-postseason" }
if ($AllowCutoffSensitiveFields) { $ArgsList += "--allow-cutoff-sensitive-fields" }
if ($SourceLanes) { $ArgsList += @("--source-lanes", $SourceLanes) }
if ($PSBoundParameters.ContainsKey("MaxRecords")) { $ArgsList += @("--max-records", "$MaxRecords") }
if (-not $NoPersist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
