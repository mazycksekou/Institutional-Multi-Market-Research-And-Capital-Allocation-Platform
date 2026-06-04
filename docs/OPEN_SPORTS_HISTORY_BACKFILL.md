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

When downloads are allowed, the lane resolves the official `schedules` release through the GitHub API at `https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules` and selects the official `games.csv` release asset. If that release asset cannot be resolved, the only fallback is the official nflverse raw CSV at `https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`. The report stores compact source metadata such as release tag, asset name, host, and verifier fields; it does not persist raw API payloads or downloaded CSV payloads.

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

No downloads occur by default. Downloads require `-AllowDownload`, an approved current-phase source, and a supported direct-download lane. Missing or unimplemented download paths are explicit blockers, not silent fallbacks. Downloaded datasets and CSV files are ignored by git through the repository ignore rules.

For `nflverse_nfl` one-season downloads, the backfill uses the source hard cap when no explicit `-MaxRecords` value is supplied so a full real season can be validated in one run.

## All Available Completed NFL Seasons

The `nflverse_nfl` coverage target is `all_available_completed_seasons`. The official `games.csv` release is inspected during explicit `-AllowDownload` runs and summarized as compact source availability metadata:

- `earliest_available_season`
- `latest_available_completed_season`
- `all_available_completed_seasons`
- `validated_completed_seasons`
- `missing_completed_seasons`
- `incomplete_or_future_seasons`
- `source_completion_status`

Coverage reports use this compact metadata when present and do not persist raw release payloads or downloaded CSV payloads.

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
- `data_kind`
- `is_synthetic`
- `source_url_kind`
- `source_verified_at`
- `raw_payload_included=false`

Rows missing event ID, date, participants, or scores/results are rejected. Scores and dates are not inferred.

`data_kind=real_open_data` is used only for verified official downloads or explicit non-import user files. Rows from local `data_sources/open_sports_history/imports/...` fixtures are `data_kind=synthetic_fixture` and `is_synthetic=true`.

## Preview Rows Vs Outcome Persistence

`PersistPreview` writes only compact local sports-history preview storage. It does not write to `outcome_store`, `paper_ledger`, calibration, providers, execution systems, trading systems, or prediction-market outcome stores.

## Derived Feature Consumption

`derived_feature_backfill_report` reads:

- `data/data_sources/open_sports_history/validated/latest.json`
- `data/data_sources/open_sports_history/validated/by_module/<module>.json`
- `data/data_sources/open_sports_history/validated/by_season/<module>/<season>.json`

Tier 0 features become available when valid real result rows exist. Tier 1 rolling/form features require enough chronological real history and otherwise report `insufficient_history`.

Synthetic fixture rows are counted separately in coverage and derived-feature reports. They do not count toward real coverage, Tier 0 production readiness, or Tier 1 derived-feature readiness.

## NFL Historical Pattern Lab

`automation_scheduler/nfl_historical_pattern_lab.py` builds deterministic compact NFL historical profiles from validated `real_open_data` nflverse rows only. It creates:

- `team_season_profiles`
- `team_game_profiles`
- `matchup_profiles`
- `pattern_candidate_profiles`
- `similarity_feature_catalog`
- `backtest_readiness_report` fields

The lab uses only safely derived schedule/result fields such as wins, losses, points for/against, margin, home/away record, close-game record, blowout rate, scoring volatility, defensive volatility, late-season form, simple team rating, and schedule-strength proxy. Postseason and Super Bowl flags are used only when `game_type` is present in the source row. Roster, injury/lineup, market, and advanced pace/efficiency features are blocked until approved sources exist.

Run:

```powershell
.\scripts\run_nfl_pattern_lab.ps1 -Persist
```

This script performs no provider calls, downloads, outcome writes, calibration writes, provider writes, or execution actions.

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
