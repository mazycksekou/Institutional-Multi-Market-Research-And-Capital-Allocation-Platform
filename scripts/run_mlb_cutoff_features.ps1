param(
    [string]$Season = "2025",
    [string]$CutoffDate = "2025-06-01",
    [string]$Team = "",
    [string]$PlayerId = "",
    [switch]$AllowCutoffSensitiveFields,
    [switch]$IncludePostseason,
    [switch]$NoPersist
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.mlb_cutoff_date_features", "--season", $Season, "--cutoff-date", $CutoffDate)
if (-not [string]::IsNullOrWhiteSpace($Team)) { $ArgsList += @("--team", $Team) }
if (-not [string]::IsNullOrWhiteSpace($PlayerId)) { $ArgsList += @("--player-id", $PlayerId) }
if ($AllowCutoffSensitiveFields) { $ArgsList += "--allow-cutoff-sensitive-fields" }
if ($IncludePostseason) { $ArgsList += "--include-postseason" }
if (-not $NoPersist) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
