# NFL Results Research Asset

This document defines the canonical minimum-schema NFL results asset implemented in Phase 4.9D.
The permanent asset identifier is `dataset.sports.nfl.results`.

## Purpose

The results asset records settled event outcomes after an NFL game completes.
It extends the certified schedule backbone; it does not create a second event identity or a separate results database.
Results are outcome evidence for later odds settlement, decision-row generation, and backtesting, never pre-event features.

## Canonical Ownership

- results orchestration: `src.data.nfl_results_research_asset_population`
- connector family: `src.connectors.feeds.nfl_schedule`
- raw acquisition cache: `src.data.historical_dataset_acquisition_runtime`
- row validation: `src.data.nfl_p0_foundation` and `src.data.validation`
- asset and dataset certification: `src.data.historical_research_asset_certification_runtime`
- lifecycle and alignment: `src.data.research_asset_lifecycle_runtime`
- storage: `src.storage.local_store`
- coverage planning: `src.market_intelligence.research_asset_coverage_planner`
- dashboard readiness: `src.services.streamlit_dashboard_data`
- market profile: `sports:nfl`

The existing NFL schedule/results connector family is reused because the selected open source family publishes both schedule and final-result evidence. No results-only connector registry or storage owner is introduced.

## Minimum Schema

Each canonical result row supplies or derives:

- `game_id`
- `event_id`
- `season`
- `week`
- `home_team`
- `away_team`
- `final_home_score`
- `final_away_score`
- `winning_team`
- `losing_team`
- `tie_indicator`
- `game_completed`
- `completion_timestamp`
- `overtime_indicator`
- `postseason_indicator`
- provider and source metadata
- acquisition and source timestamps
- schema and dataset versions
- lineage and certification metadata

The canonical storage table retains its established fields such as `final_score_home`, `final_score_away`, `winner_team`, and `final_scored_at`. The research-asset normalization layer exposes the contract aliases above without creating a duplicate table.

## Acquisition And Certification Flow

`Provider metadata / deterministic fixture -> existing NFL schedule/results connector -> raw acquisition cache -> integrity validation -> results normalization -> schedule join validation -> research asset certification -> dataset certification -> lifecycle update -> shared historical storage -> coverage planner -> readiness snapshot`

No connector may write directly to `nfl_results` as certified truth. The raw payload and acquisition metadata must be persisted first.

## Schedule Join Gate

A result cannot certify unless both `dataset.nfl.games` and `dataset.sports.nfl.schedule` are already certified in the same local repository database.
Each result must match a schedule row on canonical `game_id`, with the same home team, away team, and scheduled event time.

The join gate rejects or blocks:

- missing schedule rows
- missing or uncertified games/schedule backbones
- home/away mismatches
- event-time mismatches
- duplicate or missing result identities
- invalid lineage or provider timestamps
- completion timestamps before scheduled event time

## Field-Level Provenance

Every minimum result field maps to its source field, provider, acquisition timestamp, raw payload reference, lineage identifier, confidence, and quality tier.
Derived aliases identify their calculation source explicitly. Examples include:

- `final_home_score` from `final_score_home`
- `final_away_score` from `final_score_away`
- `winning_team` from `winner_team`
- `losing_team` from the winner and event participants
- `tie_indicator` from both final scores
- `game_completed` from settlement/finalization status
- `postseason_indicator` from season type

Dataset-level provider metadata does not replace this field-level evidence.

## Lifecycle And Readiness

The valid phase path is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

`FEATURE_READY` means the result can join future certified assets. It does not mean the NFL minimum backtest schema is complete.
After schedule and results certification, the coverage planner reports three of six required P0 assets certified and selects odds as the next missing minimum-schema asset.

## Query And Worldview Preparation

The persisted identity, lineage, provider capability, field provenance, certification state, lifecycle state, and schedule join status allow a future query layer to answer:

- which result supports an NFL event
- whether the result and schedule agree
- which provider supplied each result field
- when the result became available
- why a result is blocked or uncertified
- which evidence package supports settlement
- what still prevents the event from becoming backtest-ready

Worldview remains a consumer of certified evidence and is not a data source or certification authority.

## Deferred Work

- Live provider execution remains disabled; tests use deterministic local fixture mode.
- Multi-event population needs an asset-instance identity contract so immutable dataset identity is not conflated with event identity.
- Cross-provider score conflict resolution remains a later multi-provider implementation concern.
- Odds, weather, injuries, officials, team statistics, player statistics, and betting splits remain separate research assets.

