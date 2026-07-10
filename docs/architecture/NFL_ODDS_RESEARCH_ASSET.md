# NFL Odds Research Asset

This document defines the canonical minimum-schema NFL odds asset implemented in Phase 4.9E.
The permanent asset identifier is `dataset.nfl.odds_snapshots`.

## Purpose

The odds asset records pregame market evidence for spread, moneyline, and totals at a decision time.
It extends the certified schedule and results backbone; it does not create a second event identity or a separate odds database.
Odds are the pregame evidence layer for later decision-row generation and backtesting, never postgame features.

## Canonical Ownership

- odds orchestration: `src.data.nfl_odds_research_asset_population`
- connector family: `src.connectors.odds_data`
- raw acquisition cache: `src.data.historical_dataset_acquisition_runtime`
- row validation: `src.data.nfl_p0_foundation` and `src.data.validation`
- asset and dataset certification: `src.data.historical_research_asset_certification_runtime`
- lifecycle and alignment: `src.data.research_asset_lifecycle_runtime`
- storage: `src.storage.local_store`
- coverage planning: `src.market_intelligence.research_asset_coverage_planner`
- dashboard readiness: `src.services.streamlit_dashboard_data`
- market profile: `sports:nfl`

The deterministic odds connector path is reusable because the provider capability is modeled explicitly and the raw payload still flows through the shared acquisition and certification owners.
No odds-only storage owner is introduced.

## Minimum Schema

Each canonical odds row supplies or derives:

- `game_id`
- `event_id`
- `season`
- `week`
- `home_team`
- `away_team`
- `book`
- `market`
- `selection`
- `line_value`
- `american_odds`
- `decimal_odds`
- `implied_probability`
- `market_label`
- `freshness_score`
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

The canonical storage table retains its established fields and the research-asset normalization layer exposes the contract aliases above without creating a duplicate table.

## Acquisition And Certification Flow

`Provider / deterministic fixture -> connector -> raw acquisition cache -> integrity validation -> normalization -> schedule + results join validation -> research asset certification -> dataset certification -> lifecycle update -> shared historical storage -> coverage planner -> readiness snapshot`

No connector may write directly to `nfl_odds_snapshots` as certified truth.
The raw payload and acquisition metadata must be persisted first.

## Schedule And Results Join Gate

An odds row cannot certify unless `dataset.nfl.games`, `dataset.sports.nfl.schedule`, and `dataset.sports.nfl.results` are already certified in the same local repository database.
Each odds row must match the schedule and results backbone on canonical `game_id`, with the same home team, away team, and event identity.
The row must also remain decision-time safe, meaning the snapshot and decision timestamps occur at or before kickoff.

The join gate rejects or blocks:

- missing schedule rows
- missing result rows
- missing or uncertified games/schedule/results backbones
- home/away mismatches
- event-time mismatches
- decision-time snapshots after kickoff
- duplicate or missing odds identities
- invalid lineage or provider timestamps
- unsupported postgame evidence being treated as pregame evidence

## Field-Level Provenance

Every minimum odds field maps to its source field, provider, acquisition timestamp, raw payload reference, lineage identifier, confidence, and quality tier.
Examples include:

- `book`
- `market`
- `selection`
- `line_value`
- `american_odds`
- `decimal_odds`
- `implied_probability`
- `market_label`
- `freshness_score`

Dataset-level provider metadata does not replace this field-level evidence.

## Lifecycle And Readiness

The valid phase path is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

`FEATURE_READY` means the odds row can join future certified assets. It does not mean the NFL minimum backtest schema is complete.
After schedule, results, and odds certification, the coverage planner reports the next unresolved minimum-schema target as weather.

## Query And Worldview Preparation

The persisted identity, lineage, provider capability, field provenance, certification state, lifecycle state, and schedule/results join status allow a future query layer to answer:

- which odds evidence supports an NFL event
- whether the odds and backbone agree
- which provider supplied each odds field
- when the odds became available
- why an odds asset is blocked or uncertified
- which evidence package supports settlement and later backtesting
- what still prevents the event from becoming backtest-ready

Worldview remains a consumer of certified evidence and is not a data source or certification authority.

## Deferred Work

- Live provider execution remains disabled; tests use deterministic local fixture mode.
- Multi-event population needs an asset-instance identity contract so immutable dataset identity is not conflated with event identity.
- Cross-provider score conflict resolution remains a later multi-provider implementation concern.
- Weather, injuries, officials, coaching, team statistics, player statistics, and betting splits remain separate research assets.
