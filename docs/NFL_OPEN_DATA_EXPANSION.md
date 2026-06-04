# NFL Open Data Expansion

This workflow catalogs and validates free/open NFL source lanes without enabling any source for live execution. It uses Python-controlled GitHub release metadata and approved open-data downloads only. It does not scrape HTML, automate a browser, scrape Sports Reference, use paid APIs, or persist raw provider payloads.

## Safety Contract

- `provider_write=false`
- `execution_allowed=false`
- `execution_allowed_count=0`
- `live_execution_enabled=false`
- `auto_execution_enabled=false`
- `kalshi_order_execution_enabled=false`
- `sportsbook_bet_execution_enabled=false`
- `broker_order_execution_enabled=false`
- `stock_trade_execution_enabled=false`
- `crypto_trade_execution_enabled=false`
- `actual_orders_submitted=0`
- `actual_bets_submitted=0`
- `actual_trades_submitted=0`
- `actual_crypto_swaps_submitted=0`
- `raw_payload_included=false`
- `secrets_included=false`
- `enabled_source_count=0`
- `paid_source_enabled_count=0`

## Source Registry

Run:

```powershell
.\scripts\check_nfl_open_data_sources.ps1
```

The registry lives under `data/data_sources/nfl_open_data/sources/` at runtime. It includes these required categories:

1. schedules_results
2. play_by_play
3. team_stats
4. player_stats
5. rosters
6. weekly_rosters
7. snap_counts
8. participation
9. depth_charts
10. injuries
11. transactions
12. draft
13. combine
14. coaching
15. officials
16. stadiums
17. weather
18. betting_lines_or_market_odds
19. advanced_efficiency
20. pace_or_play_volume
21. roster_continuity

Every source defaults to `enabled=false`. Lanes requiring terms review stay blocked and are not downloaded.

## Field Catalog

Run:

```powershell
.\scripts\run_nfl_open_data_field_catalog.ps1
```

The catalog writes:

- `data/data_sources/nfl_open_data/field_catalog/latest.json`
- `data/data_sources/nfl_open_data/field_catalog/latest.md`
- `data/data_sources/nfl_open_data/field_catalog/items/<run_id>.json`
- `data/data_sources/nfl_open_data/field_catalog/items/<run_id>.md`

Fields are marked `verified` only after a validated sample/backfill report exposes them. Candidate fields remain `source_status=unverified` and `implementation_status=research_required`.

## Backfill Gates

Run metadata/coverage only:

```powershell
.\scripts\run_nfl_open_data_backfill.ps1 -Mode coverage_report
```

Run one source with downloads explicitly allowed:

```powershell
.\scripts\run_nfl_open_data_backfill.ps1 -SourceId nflverse_play_by_play -Mode all -Season 2024 -AllowDownload -MaxRecords 25 -MaxFullAssets 2
```

Run all approved lanes:

```powershell
.\scripts\run_nfl_open_data_backfill.ps1 -Mode all -Season 2024 -AllowDownload -MaxRecords 25 -MaxFullAssets 2
```

Gate order:

1. metadata_check
2. tiny_sample
3. one_season_import
4. full_available_backfill

Tiny samples require explicit `-AllowDownload`. One-season imports require a passed tiny sample unless the controller is using its explicit safe override mode. Full available backfills require a passed one-season gate. Large sources use bounded resumable sessions and report the next safe session.

## Outputs

Validated compact reports are written under:

- `data/data_sources/nfl_open_data/validated/<source_id>/latest.json`
- `data/data_sources/nfl_open_data/validated/<source_id>/latest.md`
- `data/data_sources/nfl_open_data/validated/<source_id>/items/<run_id>.json`
- `data/data_sources/nfl_open_data/validated/<source_id>/by_season/<season>.json`
- `data/data_sources/nfl_open_data/validated/<source_id>/by_team/<team>.json`
- `data/data_sources/nfl_open_data/validated/<source_id>/by_player/<player_id>.json`

Session ledgers are written under:

- `data/data_sources/nfl_open_data/backfill_sessions/latest.json`
- `data/data_sources/nfl_open_data/backfill_sessions/items/<session_id>.json`
- `data/data_sources/nfl_open_data/backfill_sessions/daily/<YYYY-MM-DD>.json`

Coverage matrix reports are written under:

- `data/data_sources/nfl_open_data/coverage_matrix/latest.json`
- `data/data_sources/nfl_open_data/coverage_matrix/latest.md`
- `data/data_sources/nfl_open_data/coverage_matrix/items/<run_id>.json`
- `data/data_sources/nfl_open_data/coverage_matrix/items/<run_id>.md`

The workflow never writes `outcome_store`, `paper_ledger`, calibration stores, execution ledgers, provider-write ledgers, `.env`, cookies, tokens, secrets, raw provider responses, or downloaded raw datasets.

## Feature Readiness (availability only)

After lanes are backfilled, the field catalog is re-seeded from the compact
validated outputs and every verified field is classified with `feature_family`,
`cutoff_required`, `leakage_risk`, `target_leakage_safe`,
`allowed_for_regular_season_snapshot`, `allowed_for_postseason_target`, and
`derived_/pattern_/validation_feature_candidate` flags. Fields are never marked
verified unless they exist in a completed compact output.

Source-supported feature builders are reported (availability + provenance only,
no values computed and nothing fabricated) by
`automation_scheduler/nfl_open_data_feature_builders.py` for: team game play
volume, team game efficiency candidates, player usage (snap/participation),
roster continuity, injury availability, depth-chart stability, and next-gen
efficiency candidates. Each builder carries `source_id`, `source_fields_used`,
`seasons_supported`, `granularity`, `cutoff_required`, and `leakage_risk`, and
returns a blocked feature with a reason when required source fields are missing.

The combined readiness report
(`automation_scheduler/nfl_open_data_feature_readiness.py`, script
`scripts/run_nfl_open_data_feature_readiness.ps1`) diffs the field catalog
before/after, surfaces derived-feature availability flags, pattern-lab expanded
readiness, and the holdout validation guard summary. The holdout validation
guard classifies every candidate before use: regular-season snapshot similarity
features are the only validation-allowed inputs, while injury / roster / snap /
depth / market / next-gen feature builders are blocked by default (by leakage or
cutoff sensitivity). Market-odds fields are cutoff-sensitive by default and
postseason labels remain target-only. No predictive claims are made and no
betting/trading/execution outputs are produced.

Feature readiness and feature builder reports are written under
`data/data_sources/nfl_open_data/feature_builders/` and
`data/data_sources/nfl_open_data/feature_readiness/` and are not committed.

## Source Exhaustion, Coaching, and Cutoff-Week Snapshots

`automation_scheduler/nfl_open_data_source_exhaustion.py` audits remaining
candidate NFL source families (nflverse/nflfastR, SportsDataverse, official
NFL/team endpoints, public web, open GitHub datasets, public open data, open
market archives, coaching/staff) as a no-call, metadata-only registry. It
performs no provider calls, no downloads, no HTML scraping, and no user-agent
spoofing. Candidates are classified and blocked when spoofing/bypass is
required, terms/robots are unclear for raw-HTML scraping, the source is
paid/freemium, auth/API key is required, or it is a Sports Reference / Pro
Football Reference derivative. Redundant sources (already covered by nflverse)
are skipped. The field-difference engine in `nfl_open_data_field_catalog.py`
(`build_existing_nfl_field_index`, `compare_candidate_fields_to_existing_catalog`,
`classify_candidate_field_novelty`, `build_source_field_diff_report`) marks each
candidate field as exact/canonical duplicate, equivalent, or genuinely new
(field, granularity, join key, season, or entity coverage) so only
non-redundant fields advance to ingestion gates.

Coaching/staff sources (`nfl_coaching_sources.py`, `nfl_coaching_adapters.py`)
are disabled by default and compliance-gated. The adapter never scrapes, never
spoofs (truthful `betting-stock-api-research-bot/0.1` user-agent), enforces a
crawl delay of at least 3 seconds and a bounded page budget if crawling were
ever permitted, persists no raw HTML, and stores only compact normalized facts.
With no confirmed open/terms-safe coaching release, the lane stays blocked with
a precise reason rather than failing.

`automation_scheduler/nfl_cutoff_week_features.py` (script
`scripts/run_nfl_cutoff_features.ps1`) computes point-in-time feature snapshots
from already-validated compact rows using only data through an explicit
`(season, cutoff_week)`. Future weeks are excluded, postseason is excluded by
default, cutoff-sensitive groups (roster continuity, injury availability, depth
chart stability, market odds) are blocked unless
`allow_cutoff_sensitive_fields` is explicitly enabled, and every value carries
provenance (`source_id`, `source_fields_used`, `season`, `max_week_used`,
`cutoff_week`, `cutoff_passed`, `leakage_risk`, `cutoff_required`). No target
labels are used as features, no predictive claims are made, and no values are
fabricated. Source-exhaustion, coaching, and cutoff reports are written under
`data/data_sources/nfl_open_data/{source_exhaustion,coaching_sources,cutoff_features}/`
and are not committed.

## Coaching/Staff Acquisition (compliance-gated, disabled by default)

`automation_scheduler/nfl_coaching_sources.py` registers ten coaching/staff
source families: official team staff pages, official team press releases,
official NFL staff/news pages, team sitemaps, Wikidata seed (CC0), Wikipedia
seed (CC BY-SA, API), open GitHub dataset, manual CSV import, and the blocked
Pro Football Reference and FTN lanes. Every source is disabled by default.
Public HTML lanes are blocked unless robots.txt and terms clearly allow
automated collection (none currently do); Wikidata/Wikipedia structured seeds
and manual CSV import are the only ingestion-approved paths, and even those stay
disabled until an explicit enable / `-AllowManualImport`.

`automation_scheduler/nfl_coaching_adapters.py` implements compliance-gated
adapters (`OfficialTeamStaffPageCrawler`, `OfficialTeamPressReleaseCrawler`,
`WikidataCoachingSeedAdapter`, `WikipediaCoachingSeedAdapter`,
`OpenLicensedDatasetAdapter`, `ManualCsvCoachingImportAdapter`,
`BlockedReferenceSourceAdapter`). The crawler never spoofs a browser
user-agent (truthful `betting-stock-api-research-bot/0.1`), never uses browser
automation, enforces a crawl delay of at least 3 seconds and a bounded page
budget, checks robots/terms before any crawl, and never persists raw HTML or
raw payloads. No page fetch occurs in this phase because no HTML lane passes the
gate. Coaching facts are normalized into compact rows (canonical role groups:
head_coach, offensive/defensive/special_teams_coordinator, position_coach,
assistant, analyst, executive, unknown) with provenance and license, and
ambiguous roles map to `unknown`.

The manual CSV importer reads `data/manual_imports/nfl_coaching/*.csv`
(requires `-AllowManualImport`), validates each row (team, season, staff_name,
staff_role, source_license required), rejects invalid rows with a reason, and
writes only compact normalized facts. `nfl_coaching_feature_builders.py`
provides head-coach / coordinator / staff by team-season, plus coaching,
coordinator, and staff-turnover continuity candidates — continuity is computed
only when adjacent seasons are source-supported and never inferred from missing
data. The acquisition report and coverage matrix are written under
`data/data_sources/nfl_open_data/coaching/` and are not committed. Coaching
readiness flags are exposed in the derived feature report and the pattern lab.
The script is `scripts/run_nfl_coaching_import.ps1`.

## Blocked Lanes

The registry tracks terms/research blockers explicitly. Sports Reference derivative lanes remain blocked. FTN charting remains blocked until terms are reviewed. Coaching remains blocked until an approved open structured no-auth source is verified.

The coverage matrix tracks these feature families until source support is verified:

- roster_continuity
- injury_lineup_profile
- market_price_or_odds
- pace_or_advanced_efficiency
