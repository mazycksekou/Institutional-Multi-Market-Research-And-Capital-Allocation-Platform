# Open Sports History Sources

## Purpose

This foundation registers and validates free/open historical sports result sources so the project can create compact local preview rows for derived feature backfill readiness.

The pipeline is:

open historical source -> no-spend source registry -> optional local import or explicitly approved tiny download -> compact normalized sports history rows -> derived feature report consumption -> Tier 0/Tier 1 readiness.

This is not betting, trading, prediction-market calibration, model scoring, or outcome persistence.

## Why This Exists

The local sports history audit found no usable Tier 0 sports preview rows because the repository did not contain compact real sports result rows with event IDs, dates, participants, and scores/results. Open historical result rows fill that data-foundation gap without paid APIs or provider writes.

## Approved/Open Sources

- `retrosheet_mlb`: Retrosheet MLB, approved open historical source, registered disabled.
- `nflverse_nfl`: nflverse NFL, approved open historical source, registered disabled.
- `sportsdataverse_ncaaf`: metadata-ready verification lane, registered disabled.
- `sportsdataverse_ncaab`: metadata-ready verification lane, registered disabled.
- `sportsdataverse_ncaaw`: metadata-ready verification lane, registered disabled.
- `sportsdataverse_wnba`: metadata-ready verification lane, registered disabled.
- `sports_reference_manual_export`: manual-export / terms-review only, registered disabled.

All sources have `enabled=false`.

## Retrosheet MLB Usage

Use local CSV files by default:

```powershell
.\scripts\import_open_sports_history.ps1 -SourceId retrosheet_mlb -InputPath ".\data\data_sources\open_sports_history\imports\retrosheet_mlb\sample.csv" -MaxRecords 25
```

Supported aliases include `event_id`, `game_id`, `GAME_ID`, `GAME_DT`, `home_team`, `HOME_TEAM_ID`, `away_team`, `AWAY_TEAM_ID`, `home_runs`, `HOME_SCORE_CT`, `away_runs`, and `AWAY_SCORE_CT`.

## nflverse NFL Usage

Use local CSV files by default:

```powershell
.\scripts\import_open_sports_history.ps1 -SourceId nflverse_nfl -InputPath ".\data\data_sources\open_sports_history\imports\nflverse_nfl\sample.csv" -MaxRecords 25
```

Supported aliases include `game_id`, `old_game_id`, `gsis_id`, `gameday`, `game_date`, `home_team`, `away_team`, `home_score`, `home_points`, `away_score`, `away_points`, `week`, and `season`.

## SportsDataverse / CFBD Planned Lane

SportsDataverse and CFBD-related sources are registry and metadata-ready lanes. They are disabled and marked `needs_tiny_verification`.

Do not call CFBD or SportsDataverse endpoints by default. Use fixture/local-file parser tests until an approved no-spend tiny path is reviewed.

## Sports Reference Manual Export

Sports Reference is manual-export / terms-review only. Automated scraping and direct download are blocked.

Do not bypass source terms. Do not add scraper code for Sports Reference.

## No-Spend Rules

The registry uses neutral future-proof fields:

- `source_access_type`
- `current_phase_allowed`
- `future_paid_candidate`
- `requires_budget_approval`
- `approval_status`
- `enabled`

The code does not use names such as `zero_dollar_sources` or `strictly_zero_dollars`.

## Download Rules

No downloads happen by default. Direct downloads require explicit `-AllowDownload`.

```powershell
.\scripts\import_open_sports_history.ps1 -SourceId nflverse_nfl -Season 2024 -MaxRecords 25 -AllowDownload
```

`-AllowDownload` does not enable the source globally and does not write provider payloads.

## Local-File Import Rules

Local imports are dry-run by default and capped:

- Default max records: `25`
- Hard cap: `500`
- CSV support is required.
- JSON/JSONL support is available for compact fixtures.
- Parquet is optional and only works if local dependencies already support it.

## Preview Rows vs Outcome Persistence

Validated preview rows are compact sports result rows. They are not prediction-market outcomes.

The importer never writes:

- `outcome_store`
- `paper_ledger`
- Kalshi calibration reports
- provider systems
- execution systems

`-PersistPreview` writes only under:

```text
data/data_sources/open_sports_history/validated/
```

## Derived Feature Consumption

`derived_feature_backfill_report` reads:

```text
data/data_sources/open_sports_history/validated/latest.json
```

Only rows with `validation_status=available` are consumed. Retrosheet rows can make `baseball_mlb` Tier 0 ready. nflverse rows can make `americanfootball_nfl` Tier 0 ready. Tier 1 rolling features require enough chronological history.

Missing advanced metrics do not block Tier 0/Tier 1 readiness.

## Safety Invariants

The reports preserve:

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

Check source readiness:

```powershell
.\scripts\check_open_sports_history_sources.ps1
```

Dry-run local Retrosheet import:

```powershell
.\scripts\import_open_sports_history.ps1 -SourceId retrosheet_mlb -InputPath ".\data\data_sources\open_sports_history\imports\retrosheet_mlb\sample.csv" -MaxRecords 25
```

Persist compact preview rows:

```powershell
.\scripts\import_open_sports_history.ps1 -SourceId nflverse_nfl -InputPath ".\data\data_sources\open_sports_history\imports\nflverse_nfl\sample.csv" -MaxRecords 25 -PersistPreview
```

Rebuild derived feature report:

```powershell
.\scripts\check_derived_features.ps1
```

## Troubleshooting

- `download_not_allowed`: pass a local `-InputPath`, or explicitly use `-AllowDownload` for supported sources.
- `missing_event_date`: provide a parseable date field; dates are not inferred from filenames.
- `missing_participants`: include home/away participant fields.
- `missing_scores_or_results`: include numeric scores or an explicit result/winner.
- `nonnumeric_score`: score fields must parse as numbers.
- `raw_payload_risk`: remove raw provider payload fields before import.
- `secret_risk`: remove secret-like keys before import.
- `insufficient_history`: Tier 0 may be ready, but Tier 1 rolling features need more validated rows.
