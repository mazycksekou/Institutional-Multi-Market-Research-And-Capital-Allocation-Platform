param(
    [ValidateSet("metadata_check", "tiny_sample", "structured_seed_import", "crawl_staff_pages", "crawl_press_releases", "wikidata_seed", "wikipedia_seed", "manual_import", "coverage_report")]
    [string]$Mode = "coverage_report",
    [string]$SourceId,
    [string]$InputCsv,
    [switch]$AllowDownload,
    [switch]$AllowStructuredSeed,
    [switch]$AllowCrawl,
    [switch]$AllowManualImport,
    [int]$MaxPagesPerDomain,
    [int]$CrawlDelaySeconds,
    [int]$MaxRecords,
    [int]$SeasonStart,
    [int]$SeasonEnd,
    [switch]$PersistPreview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$ArgsList = @("-m", "automation_scheduler.nfl_coaching_feature_builders", "--mode", $Mode)
if ($SourceId) { $ArgsList += @("--source-id", $SourceId) }
if ($InputCsv) { $ArgsList += @("--input-csv", $InputCsv) }
if ($AllowDownload) { $ArgsList += "--allow-download" }
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if ($AllowCrawl) { $ArgsList += "--allow-crawl" }
if ($AllowManualImport) { $ArgsList += "--allow-manual-import" }
if ($PSBoundParameters.ContainsKey("MaxPagesPerDomain")) { $ArgsList += @("--max-pages-per-domain", "$MaxPagesPerDomain") }
if ($PSBoundParameters.ContainsKey("CrawlDelaySeconds")) { $ArgsList += @("--crawl-delay-seconds", "$CrawlDelaySeconds") }
if ($PSBoundParameters.ContainsKey("MaxRecords")) { $ArgsList += @("--max-records", "$MaxRecords") }
if ($PSBoundParameters.ContainsKey("SeasonStart")) { $ArgsList += @("--season-start", "$SeasonStart") }
if ($PSBoundParameters.ContainsKey("SeasonEnd")) { $ArgsList += @("--season-end", "$SeasonEnd") }
if ($PersistPreview) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
