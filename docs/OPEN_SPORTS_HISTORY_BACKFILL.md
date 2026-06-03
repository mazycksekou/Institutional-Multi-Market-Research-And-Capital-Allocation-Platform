# Open Sports History Backfill

## Purpose

The open sports history backfill control plane collects compact, validated historical sports result rows for model modules where approved no-spend/open data exists. It is the foundation for last-10-year sports history coverage before sportsbook odds, CLV, social sentiment, injury/weather/lineup, dashboard, or paid-data work.

## Why This Exists

The local sports history audit found no usable Tier 0 preview rows with stable event IDs, dates, participants, and final scores/results. Metadata-only checks are not enough for calibration or derived features. The repo needs real compact historical game/match rows before derived sports features can be trusted.

## Strategy

1. Run a smoke test against a tiny local fixture or explicitly approved tiny source sample.
2. Backfill one source and one season.
3. Backfill one source across the last 10 seasons.
4. Schedule resumable sessions until target coverage is complete.
5. Validate, dedupe, compact, and report coverage.
6. Feed validated rows into `derived_feature_backfill_report`.

## Approved First-Wave Sources

The first-wave parser lanes are:

- `retrosheet_mlb` for `baseball_mlb`
- `nflverse_nfl` for `americanfootball_nfl`

Both are approved open historical lanes, disabled by default, and require explicit command input for any download attempt.

## Retrosheet MLB Lane

Retrosheet local CSV imports normalize MLB event IDs, dates, home/away teams, scores, winner, final margin, and total score. Direct download is represented as a source capability, but any missing download URL is reported as `source_download_not_implemented` through the import/backfill status instead of attempting an unsafe fallback.

## nflverse NFL Lane

nflverse local CSV imports normalize NFL game IDs, dates, season/week, home/away teams, scores, winner, final margin, and total points. CSV direct download support is available only when `-AllowDownload` is explicitly passed.

## Soccer, Tennis, And SportsDataverse Lanes

The registry includes second-wave lanes for:

- `football_data_uk_soccer`
- `jeff_sackmann_tennis_atp`
- `jeff_sackmann_tennis_wta`
- `sportsdataverse_ncaaf`
- `sportsdataverse_ncaab`
- `sportsdataverse_ncaaw`
- `sportsdataverse_wnba`
- `sportsdataverse_nhl`
- `sportsdataverse_nba_or_hoopr`

These are disabled by default and marked `needs_tiny_verification` until a tiny parser/source contract is verified.

## UFC/MMA, Boxing, And Golf

`ufc_mma_research_lane`, `boxing_research_lane`, and `golf_research_lane` are research/manual/import lanes. They are not current-phase automated backfill sources until an approved open structured source is confirmed.

## Sports Reference

`sports_reference_manual_export` is manual-export and terms-review only. Automated download and scraping are blocked. Sports Reference must not be scraped or bypassed.

## No-Spend Rules

All sources use neutral budget fields:

- `source_access_type`
- `current_phase_allowed`
- `future_paid_candidate`
- `requires_budget_approval`
- `approval_status`
- `enabled`

No source is globally enabled by default. Paid sources are not enabled.

## Download Rules

No downloads occur by default. Downloads require `-AllowDownload`, an approved current-phase source, and a supported direct-download lane. Missing or unimplemented download paths are explicit blockers, not silent fallbacks.

## Bulk Backfill Rules

Bulk mode requires a passed smoke test for the source or a valid local parser input. It targets the last 10 seasons by default, processes by season, and writes resumable session state.

## Session Ledger

Backfill sessions write:

- `data/data_sources/open_sports_history/backfill_sessions/latest.json`
- `data/data_sources/open_sports_history/backfill_sessions/items/<session_id>.json`
- `data/data_sources/open_sports_history/backfill_sessions/daily/<YYYY-MM-DD>.json`

Sessions include completed seasons, pending seasons, blockers, and next recommended session.

## Compact Row Schema

Validated preview rows contain only:

- `module`
- `source_id`
- `event_id`
- `event_date`
- `season`
- `week_or_round`
- `home_participant`
- `away_participant`
- `neutral_site`
- `home_score`
- `away_score`
- `final_result`
- `winner`
- `final_margin`
- `total_score`
- `validation_status`
- `blocked_reason`
- `source_file_or_ref`
- `source_record_hash`
- `raw_payload_included=false`

Rows missing event ID, date, participants, or scores/results are rejected. Scores and dates are not inferred.

## Preview Rows Vs Outcome Persistence

`PersistPreview` writes only compact local sports-history preview storage. It does not write to `outcome_store`, `paper_ledger`, calibration, providers, execution systems, trading systems, or prediction-market outcome stores.

## Derived Feature Consumption

`derived_feature_backfill_report` reads:

- `data/data_sources/open_sports_history/validated/latest.json`
- `data/data_sources/open_sports_history/validated/by_module/<module>.json`
- `data/data_sources/open_sports_history/validated/by_season/<module>/<season>.json`

Tier 0 features become available when valid result rows exist. Tier 1 rolling/form features require enough chronological history and otherwise report `insufficient_history`.

## Safety Invariants

The control plane keeps these locked:

- `provider_write=false`
- `execution_allowed=false`
- `execution_allowed_count=0`
- `live_execution_enabled=false`
- `auto_execution_enabled=false`
- `kalshi_order_execution_enabled=false`
- `sportsbook_bet_execution_enabled=false`
- `broker_order_execution_enabled=false`
- `crypto_trade_execution_enabled=false`
- `stock_trade_execution_enabled=false`
- `actual_orders_submitted=0`
- `actual_bets_submitted=0`
- `actual_trades_submitted=0`
- `actual_crypto_swaps_submitted=0`
- `raw_payload_included=false`
- `secrets_included=false`
- `enabled_source_count=0`
- `paid_source_enabled_count=0`

## Example Commands

Smoke test local file:

```powershell
.\scripts\backfill_open_sports_history.ps1 -SourceId retrosheet_mlb -Mode smoke_test -InputPath ".\data\data_sources\open_sports_history\imports\retrosheet_mlb\sample.csv" -MaxRecords 25
```

Season backfill:

```powershell
.\scripts\backfill_open_sports_history.ps1 -SourceId nflverse_nfl -Mode season_backfill -Season 2024 -AllowDownload -PersistPreview
```

Bulk 10-year backfill:

```powershell
.\scripts\backfill_open_sports_history.ps1 -SourceId retrosheet_mlb -Mode bulk_backfill -TargetYears 10 -AllowDownload -PersistPreview
```

Coverage only:

```powershell
.\scripts\backfill_open_sports_history.ps1 -Mode coverage_report
```

## Troubleshooting

- `download_not_allowed`: rerun with a local file or explicitly pass `-AllowDownload`.
- `source_download_not_implemented`: use local-file import until a safe approved URL lane is implemented.
- `smoke_test_required`: run `smoke_test` first or provide a valid local parser input.
- `terms_review_required`: do not download or scrape until terms are reviewed.
- `package_not_installed`: use local fixtures or install/verify the optional open-source package in a separate approved lane.
- `insufficient_history`: append more validated chronological rows before Tier 1 derived features.
