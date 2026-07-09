# Research Asset Lifecycle Runtime

This document defines the canonical runtime owner for research asset lifecycle state and time/entity alignment certification.
It is architecture only. It does not implement connectors, provider authentication, data downloads, feature engineering, mathematical calculations, signals, targets, or backtesting.

The runtime exists so every research asset can move through one shared lifecycle while preserving immutable identity, alignment evidence, provenance, and readiness reporting.

## Purpose

The runtime answers two questions:

1. What is the current lifecycle state of a governed research asset?
2. Does the asset align correctly in time and entity scope before it is allowed to advance?

It keeps the following responsibilities on one canonical path:

- immutable research asset identity
- lifecycle state management
- lifecycle transition history
- time and entity alignment certification
- alignment failure classification
- dataset-gating handoff
- dashboard readiness reporting
- Worldview-ready evidence exposure

## Canonical Ownership

The runtime reuses the existing canonical owners rather than introducing a duplicate lifecycle stack:

- `src.data.research_asset_lifecycle_runtime` owns lifecycle identity, lifecycle state, alignment certification, and lifecycle readiness summaries.
- `src.data.historical_research_asset_certification_runtime` owns asset-level certification and dataset-gating certification evidence.
- `src.storage.local_store` owns the physical lifecycle and alignment tables.
- `src.data.validation` owns reusable row-level validation helpers.
- `src.services.streamlit_dashboard_data` owns the dashboard-facing readiness adapter.

The runtime does not own provider integrations.
Providers remain acquisition mechanisms only.

## Canonical Lifecycle

The reusable lifecycle progression is:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY -> MATH_READY -> SIGNAL_READY -> BACKTEST_READY -> PRODUCTION_READY`

Lifecycle meaning:

- `DISCOVERED`: the asset is known and cataloged.
- `SOURCE_IDENTIFIED`: at least one usable source family is known.
- `CONNECTOR_MAPPED`: the canonical acquisition path exists.
- `RAW_ACQUIRED`: immutable source payloads have been staged.
- `INTEGRITY_VERIFIED`: checksum, schema, and timestamp checks passed.
- `NORMALIZED`: the raw payload has been normalized into governed shape.
- `RESEARCH_ASSET_CERTIFIED`: the asset passed the asset-level certification gate.
- `DATASET_CERTIFIED`: the dataset built from required assets has been certified.
- `FEATURE_READY`: the asset is ready for feature population.
- `MATH_READY`: the asset is ready for governed mathematical engines.
- `SIGNAL_READY`: the asset is ready for reusable signals.
- `BACKTEST_READY`: the asset is allowed into the minimum certified backtest path.
- `PRODUCTION_READY`: the asset is usable in the canonical production workflow.

## Immutable Research Asset Identity

Every research asset must support one permanent identity.
Lifecycle state changes over time, but the identity itself does not mutate.

Minimum identity fields:

- `asset_id`
- `asset_family`
- `market_profile`
- `market`
- `league`
- `sport`
- `season`
- `week_or_date`
- `event_id`
- `market_id`
- `selection`
- `provider`
- `connector`
- `schema_version`
- `lineage_version`
- `asset_name`
- `asset_type`
- `participant_id`
- `team_id`
- `game_id`
- `market_type`

Rules:

- the identity must remain stable across lifecycle updates
- only lifecycle state, evidence, and readiness metadata may change
- metadata may be appended, but the identity core must remain immutable

## Time & Entity Alignment Certification

Alignment certification verifies that the asset still refers to the same market, selection, event, and timing context that was expected at certification time.

Validated alignment dimensions:

- `market_profile`
- `league`
- `season`
- `week_or_date`
- `event_id`
- `game_id`
- `team_id`
- `participant_id`
- `market_type`
- `selection`
- `decision_time`
- `snapshot_time`
- `provider_timestamp`
- `result_timestamp`

Alignment failure reasons:

- `ENTITY_MISMATCH`
- `TEAM_MISMATCH`
- `EVENT_MISMATCH`
- `GAME_MISMATCH`
- `LEAGUE_MISMATCH`
- `MARKET_MISMATCH`
- `SELECTION_MISMATCH`
- `SEASON_MISMATCH`
- `WEEK_MISMATCH`
- `DECISION_TIME_MISMATCH`
- `SNAPSHOT_AFTER_DECISION`
- `RESULT_BEFORE_DECISION`
- `SOURCE_TIMESTAMP_MISSING`
- `POINT_IN_TIME_VIOLATION`

## Certification States

The canonical lifecycle and alignment evidence can report these states:

- `UNKNOWN`
- `DISCOVERED`
- `SOURCE_IDENTIFIED`
- `CONNECTOR_MAPPED`
- `RAW_ACQUIRED`
- `INTEGRITY_VERIFIED`
- `NORMALIZED`
- `RESEARCH_ASSET_CERTIFIED`
- `DATASET_CERTIFIED`
- `FEATURE_READY`
- `MATH_READY`
- `SIGNAL_READY`
- `BACKTEST_READY`
- `PRODUCTION_READY`

## Multi-Provider Support

The runtime assumes one certified asset or dataset may combine multiple providers.

Supported acquisition roles:

- primary source
- secondary source
- verification source
- fallback source
- enrichment source

The repository stores one certified truth while preserving source evidence for review and replay.

## Readiness Reporting

The runtime exposes the following readiness concepts to dashboard and governance consumers:

- lifecycle state
- alignment certification state
- alignment failures
- certification scores
- blocked assets
- missing assets
- dataset readiness

## Reuse Expectations

This runtime is reusable for:

- sports
- prediction markets
- options / 0DTE
- futures
- crypto
- macro

The reuse contract is:

provider -> raw acquisition cache -> integrity validation -> normalization -> research asset certification -> dataset certification -> historical research database -> lifecycle runtime

## Phase Boundary

Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification.
Phase 4.9A populates the NFL schedule research asset.
Phase 4.9B builds the research asset coverage planner and provider selection framework.
Phase 4.9C implements the first production connector for the NFL schedule research asset.

## Out Of Scope

This runtime does not:

- download data directly into the historical research database
- authenticate with providers
- implement provider-specific APIs
- calculate features
- build backtests
- build models
- execute trades

It only defines the reusable runtime relationship between governed lifecycle state and alignment certification.

## Worldview Compatibility

This runtime improves future Worldview compatibility by making lifecycle state, alignment evidence, and immutable identity explicit.

Future Worldview requests should be able to ask:

- which research assets are still discovered
- which research assets are source identified
- which research assets are connector mapped
- which research assets are blocked by time/entity mismatches
- which research assets are ready for dataset certification
- which evidence package corresponds to a given lifecycle state
