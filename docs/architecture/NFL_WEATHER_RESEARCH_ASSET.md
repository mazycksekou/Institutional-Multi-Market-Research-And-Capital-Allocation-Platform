# NFL Weather Research Asset

This document defines the canonical minimum-schema NFL weather asset implemented in Phase 4.9F.
The permanent asset identifier is `dataset.nfl.weather_snapshots`.

## Purpose

The weather asset records pregame forecast evidence for each NFL event.
It extends the certified schedule, results, and odds backbone; it does not create a second event identity or a separate weather database.
Weather remains pregame evidence for later decision-row generation and backtesting, never postgame actual-condition leakage.

## Canonical Ownership

- weather orchestration: `src.data.nfl_weather_research_asset_population`
- connector family: `src.connectors.market_data`
- raw acquisition cache: `src.data.historical_dataset_acquisition_runtime`
- row validation: `src.data.nfl_p0_foundation` and `src.data.validation`
- asset and dataset certification: `src.data.historical_research_asset_certification_runtime`
- lifecycle and alignment: `src.data.research_asset_lifecycle_runtime`
- storage: `src.storage.local_store`
- coverage planning: `src.market_intelligence.research_asset_coverage_planner`
- dashboard readiness: `src.services.streamlit_dashboard_data`
- market profile: `sports:nfl`

The deterministic forecast path is reusable because the provider capability is modeled explicitly and the raw payload still flows through the shared acquisition and certification owners.
No weather-only storage owner or provider-specific runtime is introduced.

## Minimum Schema

Each canonical weather row supplies or derives:

- `game_id`
- `event_id`
- `season`
- `week`
- `venue_name`
- `venue_city`
- `venue_state`
- derived `location`
- `forecast_time`
- `weather_condition`
- `temperature_f`
- `wind_mph`
- `wind_gust_mph`
- `precipitation_pct`
- `humidity_pct`
- `pressure_hpa`
- `indoor_flag`
- `forecast_freshness`
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

The canonical storage table retains its established venue fields and the research-asset normalization layer exposes a derived `location` alias without creating a duplicate table.

## Acquisition And Certification Flow

`Provider / deterministic forecast fixture -> shared market-data connector metadata -> raw acquisition cache -> integrity validation -> normalization -> schedule + results + odds join validation -> research asset certification -> dataset certification -> lifecycle update -> shared historical storage -> coverage planner -> readiness snapshot`

No source may write directly to `nfl_weather_snapshots` as certified truth.
The raw payload and acquisition metadata must be persisted first.

## Schedule, Results, And Odds Join Gate

A weather row cannot certify unless `dataset.nfl.games`, `dataset.sports.nfl.schedule`, `dataset.sports.nfl.results`, and `dataset.nfl.odds_snapshots` are already certified in the same local repository database.
Each weather row must match the schedule, results, and odds backbone on canonical `game_id`, with the same home team, away team, and event identity.
The weather evidence must remain pregame, meaning forecast, source snapshot, snapshot, and decision timestamps all stay at or before kickoff and do not cross the decision boundary.

The join gate rejects or blocks:

- missing schedule rows
- missing result rows
- missing odds rows
- orphaned weather rows
- home/away mismatches
- post-decision weather captures
- post-kickoff snapshot timestamps
- invalid lineage or provider timestamps
- actual or postgame weather being treated as pregame forecast evidence

## Field-Level Provenance

Every minimum weather field maps to its source field, provider, acquisition timestamp, raw payload reference, lineage identifier, confidence, and quality tier.
Examples include:

- `location`
- `forecast_time`
- `weather_condition`
- `temperature_f`
- `wind_mph`
- `wind_gust_mph`
- `precipitation_pct`
- `humidity_pct`
- `pressure_hpa`
- `indoor_flag`
- `forecast_freshness`

The derived `location` alias remains traceable to `venue_name`, `venue_city`, and `venue_state`.
Dataset-level provider metadata does not replace this field-level evidence.

## Lifecycle And Readiness

The valid phase path is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

`FEATURE_READY` means the weather row can join future certified assets.
It does not mean the NFL minimum backtest schema is complete.
After schedule, results, odds, and weather certification, the coverage planner reports team statistics as the remaining unresolved minimum-schema gap, while the roadmap advances to the injuries phase next.

## Query And Worldview Preparation

The persisted identity, lineage, provider capability, field provenance, certification state, lifecycle state, and schedule/results/odds join status allow a future query layer to answer:

- which weather evidence supports an NFL event
- whether the weather and backbone agree
- which provider supplied each weather field
- when the forecast evidence became available
- why a weather asset is blocked or uncertified
- which evidence package supports later backtesting
- what still prevents the event from becoming backtest-ready

Worldview remains a consumer of certified evidence and is not a data source or certification authority.

## Deferred Work

- Live provider execution remains disabled; tests use deterministic local fixture mode.
- Multi-snapshot forecast horizon handling remains a later expansion after the minimum certified weather slice is stable.
- Verification against actual observed conditions remains a later audit concern and must stay separate from the pregame forecast evidence path.
- Injuries, officials, coaching, team statistics, player statistics, and betting splits remain separate research assets.
