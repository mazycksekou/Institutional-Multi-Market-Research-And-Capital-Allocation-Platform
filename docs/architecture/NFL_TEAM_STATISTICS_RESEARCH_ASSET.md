# NFL Team Statistics Research Asset

This document defines the canonical minimum-schema NFL team-statistics asset implemented in Phase 4.9H.
The permanent asset identifier is `dataset.nfl.team_stats_snapshots`.

## Purpose

The team-statistics asset records predecision team-level efficiency and context snapshots for each NFL event.
It extends the certified schedule, results, odds, weather, and injuries backbone; it does not create a second event identity, a second lifecycle owner, or a separate statistics pipeline.
Only prior-game, season-to-date-excluding-target, rolling-excluding-target, or frozen pregame provider snapshots may certify as predecision evidence.
Target-event live or final statistics are not valid inputs for this asset.

## Canonical Ownership

- team-statistics orchestration: `src.data.nfl_team_statistics_research_asset_population`
- connector metadata and deterministic fixture path: `src.data.nfl_team_statistics_research_asset_population`
- raw acquisition cache: `src.data.historical_dataset_acquisition_runtime`
- row validation: `src.data.nfl_p0_foundation` and `src.data.validation`
- asset and dataset certification: `src.data.historical_research_asset_certification_runtime`
- lifecycle and alignment: `src.data.research_asset_lifecycle_runtime`
- storage: `src.storage.local_store`
- coverage planning: `src.market_intelligence.research_asset_coverage_planner`
- dashboard readiness: `src.services.streamlit_dashboard_data`
- market profile: `sports:nfl`

The phase stays local-first and deterministic.
No team-statistics-only acquisition framework, storage owner, lifecycle owner, or dashboard owner is introduced.

## Minimum Schema

Each canonical team-statistics row supplies or derives:

- `game_id`
- `event_id`
- `season`
- `week`
- `team_id`
- `team_name`
- `opponent_team_id`
- `team_side`
- `source_record_id`
- `source_retrieved_at`
- `source_snapshot_time`
- `snapshot_time`
- `decision_time`
- `team_stats_cutoff_time`
- `kickoff_time`
- `measurement_period`
- `statistic_context`
- `statistic_window_type`
- `window_start_time`
- `window_excludes_current_event`
- canonical metric fields and metric units
- provider and source metadata
- field-level provenance
- schema version
- dataset version
- lineage id
- lifecycle state
- certification state

The canonical local table is `nfl_team_stats_snapshots`.
The contract remains typed and queryable rather than storing one opaque statistics blob.

## Point-In-Time Safety

Certified predecision evidence may come from:

- prior-game realized statistics
- season-to-date statistics that exclude the target event
- rolling windows that exclude the target event
- frozen pregame provider snapshots

The certification path blocks:

- same-event live statistics
- same-event final box-score statistics
- post-decision or post-kickoff snapshot timestamps
- rolling windows that include the target event
- season aggregates that include the target event
- orphaned event or team identities
- unsupported metric units
- duplicate unstable identities

Row-level alignment evidence is stored separately per team snapshot so multi-row slices do not collapse into one misleading representative alignment contract.

## Acquisition And Certification Flow

`Provider / deterministic team-statistics fixture -> shared connector metadata -> raw acquisition cache -> integrity validation -> normalization -> schedule + results + odds + weather + optional injuries join validation -> row-level time/entity alignment certification -> research asset certification -> dataset certification -> lifecycle update -> shared historical storage -> coverage planner -> dashboard / readiness snapshot`

No source may write directly to `nfl_team_stats_snapshots` as certified truth.
The raw payload and acquisition metadata must be persisted first.

## Backbone Join And Leakage Gate

A team-statistics row cannot certify unless `dataset.nfl.games`, `dataset.sports.nfl.schedule`, `dataset.sports.nfl.results`, `dataset.nfl.odds_snapshots`, and `dataset.nfl.weather_snapshots` are already certified in the same local repository database.
`dataset.nfl.injury_snapshots` may be joined as optional context, but the asset does not depend on injuries to remain minimum-schema complete.
Each row must match the canonical `game_id`, team identity, opponent identity, and home/away context of the certified backbone.

The join and leakage gate rejects or blocks:

- missing schedule rows
- missing result rows
- missing odds rows
- missing weather rows
- orphaned team-statistics rows
- team or opponent mismatches
- contradictory home/away assignments
- same-event final or live statistics
- snapshot timestamps after the decision cutoff
- rolling-window leakage
- unsupported metric units
- invalid lineage or source timestamps

## Field-Level Provenance

Every minimum team-statistics field retains source mapping, provider, acquisition timestamp, raw payload reference, lineage id, and quality metadata where available.
Examples include:

- `offensive_efficiency`
- `defensive_efficiency`
- `pace`
- `turnover_margin`
- `injury_adjusted_availability`
- `team_stats_cutoff_time`
- `measurement_period`
- `statistic_window_type`

Dataset-level provider metadata does not replace this field-level evidence.

## Lifecycle And Readiness

The valid phase path is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

`FEATURE_READY` means the team-statistics rows are queryable for future dataset population and feature engineering.
It does not mean the repository has started mathematical engines, signals, decision rows, or backtesting.
After schedule, results, odds, weather, injuries, and team-statistics certification, the coverage planner reports no remaining required minimum-schema asset gaps and clears the first-production-connector target.
The next active phase therefore advances to the historical dataset population layer rather than reopening future enrichment assets as blockers.

## Query And Worldview Preparation

The persisted identity, lineage, provider capability, field provenance, certification state, lifecycle state, join status, and row-level alignment evidence allow a future query layer to answer:

- which team-statistics evidence supports an NFL event
- which metric values were available before the decision cutoff
- whether the target event was excluded from the metric window
- which provider supplied each metric field
- why a team-statistics row is blocked or uncertified
- which evidence package supports later dataset population and backtesting
- what still prevents the NFL lane from advancing beyond certified-asset readiness

Worldview remains a consumer of certified evidence and is not a data source or certification authority.

## Deferred Work

- Live provider execution remains disabled; tests use deterministic local fixture mode only.
- Player statistics, betting splits, officials, coaching, and depth-chart context remain separate future or enrichment assets.
- Paid or broader historical ingestion remains a later controlled-ingest phase after the minimum-schema dataset layer is stable.
