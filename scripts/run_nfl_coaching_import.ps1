param(
    [ValidateSet("metadata_check", "tiny_sample", "structured_seed_import", "structured_seed_import_scheduled", "team_qid_manifest_check", "entity_tiny_sample", "entity_seed_import", "dump_metadata_check", "dump_tiny_scan", "dump_structured_seed_import", "wikipedia_table_import", "generate_templates", "crawl_staff_pages", "crawl_press_releases", "wikidata_seed", "wikipedia_seed", "manual_import", "coverage_report")]
    [string]$Mode = "coverage_report",
    [string]$SourceId,
    [string]$InputCsv,
    [string]$WikidataDumpPath,
    [switch]$AllowDownload,
    [switch]$AllowStructuredSeed,
    [switch]$AllowLocalDump,
    [switch]$AllowCrawl,
    [switch]$AllowManualImport,
    [int]$MaxPagesPerDomain,
    [int]$CrawlDelaySeconds,
    [int]$MaxRecords,
    [int]$MaxEntities,
    [int]$MaxRequests,
    [int]$RequestIntervalSeconds = 65,
    [switch]$StopOn429,
    [switch]$Resume,
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
if ($WikidataDumpPath) { $ArgsList += @("--wikidata-dump-path", $WikidataDumpPath) }
if ($AllowDownload) { $ArgsList += "--allow-download" }
if ($AllowStructuredSeed) { $ArgsList += "--allow-structured-seed" }
if ($AllowLocalDump) { $ArgsList += "--allow-local-dump" }
if ($AllowCrawl) { $ArgsList += "--allow-crawl" }
if ($AllowManualImport) { $ArgsList += "--allow-manual-import" }
if ($StopOn429) { $ArgsList += "--stop-on-429" }
if ($Resume) { $ArgsList += "--resume" }
if ($PSBoundParameters.ContainsKey("MaxPagesPerDomain")) { $ArgsList += @("--max-pages-per-domain", "$MaxPagesPerDomain") }
if ($PSBoundParameters.ContainsKey("CrawlDelaySeconds")) { $ArgsList += @("--crawl-delay-seconds", "$CrawlDelaySeconds") }
if ($PSBoundParameters.ContainsKey("MaxRecords")) { $ArgsList += @("--max-records", "$MaxRecords") }
if ($PSBoundParameters.ContainsKey("MaxEntities")) { $ArgsList += @("--max-entities", "$MaxEntities") }
if ($PSBoundParameters.ContainsKey("MaxRequests")) { $ArgsList += @("--max-requests", "$MaxRequests") }
if ($PSBoundParameters.ContainsKey("RequestIntervalSeconds")) { $ArgsList += @("--request-interval-seconds", "$RequestIntervalSeconds") }
if ($PSBoundParameters.ContainsKey("SeasonStart")) { $ArgsList += @("--season-start", "$SeasonStart") }
if ($PSBoundParameters.ContainsKey("SeasonEnd")) { $ArgsList += @("--season-end", "$SeasonEnd") }
if ($PersistPreview) { $ArgsList += "--persist" }

python @ArgsList
exit $LASTEXITCODE
