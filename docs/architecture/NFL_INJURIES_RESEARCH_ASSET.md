# NFL Injuries Research Asset

This document defines the canonical minimum-schema NFL injuries asset implemented in Phase 4.9G.
The permanent asset identifier is `dataset.nfl.injury_snapshots`.

## Purpose

The injuries asset records pregame injury and availability evidence for each NFL event.
It extends the certified schedule, results, odds, and forecast-weather backbone; it does not create a second event identity or a separate injury database.
Injury rows remain report-time evidence for later decision-row generation and backtesting, never post-decision availability leakage.

Forecast weather and realized weather remain separated.
The injuries phase joins only to the certified forecast-only `dataset.nfl.weather_snapshots` asset and does not introduce observed-weather fields into the pregame evidence path.

## Canonical Ownership

- injury orchestration: `src.data.nfl_injuries_research_asset_population`
- connector metadata and deterministic fixture/manual-evidence path: `src.data.nfl_injuries_research_asset_population`
- raw acquisition cache: `src.data.historical_dataset_acquisition_runtime`
- row validation: `src.data.nfl_p0_foundation` and `src.data.validation`
- asset and dataset certification: `src.data.historical_research_asset_certification_runtime`
- lifecycle and alignment: `src.data.research_asset_lifecycle_runtime`
- storage: `src.storage.local_store`
- coverage planning: `src.market_intelligence.research_asset_coverage_planner`
- dashboard readiness: `src.services.streamlit_dashboard_data`
- market profile: `sports:nfl`

The minimum slice remains local-first because the provider capability and manual-evidence fallback are modeled explicitly while the raw payload still flows through the shared acquisition, certification, lifecycle, and readiness owners.
No injuries-only storage owner or provider-specific lifecycle owner is introduced.

## Minimum Schema

Each canonical injury row supplies or derives:

- `game_id`
- `event_id`
- `season`
- `week`
- `team_id`
- `team_name`
- `opponent_team_id`
- `player_id`
- `player_name`
- `position`
- `report_status`
- `availability_status`
- `practice_status`
- `report_primary_injury`
- `injury_category`
- `report_time`
- `timing_confidence`
- `report_source`
- `kickoff_time`
- `source_snapshot_time`
- `snapshot_time`
- `decision_time`
- provider and source metadata
- acquisition timestamp
- raw payload lineage
- schema version
- dataset version
- lineage id
- lifecycle state
- certification status

## Acquisition And Certification Flow

`Provider / deterministic injury fixture or approved manual evidence -> shared injuries connector metadata -> raw acquisition cache -> integrity validation -> normalization -> schedule + results + odds + weather join validation -> research asset certification -> dataset certification -> lifecycle update -> shared historical storage -> coverage planner -> readiness snapshot`

No source may write directly to `nfl_injury_snapshots` as certified truth.
The raw payload and acquisition metadata must be persisted first.

## Schedule, Results, Odds, And Weather Join Gate

An injury row cannot certify unless `dataset.nfl.games`, `dataset.sports.nfl.schedule`, `dataset.sports.nfl.results`, `dataset.nfl.odds_snapshots`, and `dataset.nfl.weather_snapshots` are already certified in the same local repository database.
Each injury row must match the schedule, results, odds, and weather backbone on canonical `game_id`, with the same team context and event identity.
The injury evidence must remain pregame, meaning report, source snapshot, snapshot, and decision timestamps all stay at or before kickoff and do not cross the decision boundary.

The join gate rejects or blocks:

- missing schedule rows
- missing result rows
- missing odds rows
- missing weather rows
- orphaned injury rows
- team mismatches
- post-decision injury updates
- post-kickoff report timestamps
- invalid lineage or provider timestamps
- realized-weather leakage into the forecast-only weather backbone

## Field-Level Provenance

Every minimum injury field maps to its source field, provider, acquisition timestamp, raw payload reference, lineage identifier, confidence, and quality tier.
Examples include:

- `report_status`
- `availability_status`
- `practice_status`
- `report_primary_injury`
- `injury_category`
- `report_time`
- `report_source`
- `timing_confidence`

Dataset-level provider metadata does not replace this field-level evidence.

## Lifecycle And Readiness

The valid phase path is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

`FEATURE_READY` means the injury row can join future certified assets.
It does not mean the NFL minimum backtest schema is complete.
After schedule, results, odds, weather, and injuries certification, the coverage planner reports team statistics as the remaining unresolved minimum-schema gap and the roadmap advances to the team-statistics phase next.

## Query And Worldview Preparation

The persisted identity, lineage, provider capability, field provenance, certification state, lifecycle state, and schedule/results/odds/weather join status allow a future query layer to answer:

- which injury evidence supports an NFL event
- whether the injury and backbone agree
- which provider supplied each injury field
- when the injury evidence became available
- why an injury asset is blocked or uncertified
- which evidence package supports later backtesting
- what still prevents the event from becoming backtest-ready

Worldview remains a consumer of certified evidence and is not a data source or certification authority.

## Deferred Work

- Live provider execution remains disabled; tests use deterministic local fixture mode and a documented manual-evidence fallback.
- Multi-update injury revision handling remains a later expansion after the minimum certified injury slice is stable.
- Network acquisition for official team or league pages remains a later connector phase and must preserve terms review plus report timestamps.
- Team statistics, player statistics, officials, coaching, and betting splits remain separate research assets.
