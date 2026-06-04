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

## Blocked Lanes

The registry tracks terms/research blockers explicitly. Sports Reference derivative lanes remain blocked. FTN charting remains blocked until terms are reviewed. Coaching remains blocked until an approved open structured no-auth source is verified.

The coverage matrix tracks these feature families until source support is verified:

- roster_continuity
- injury_lineup_profile
- market_price_or_odds
- pace_or_advanced_efficiency
