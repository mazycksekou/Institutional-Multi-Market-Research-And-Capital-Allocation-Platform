# NFL Schedule Research Asset

This document defines the first minimum-schema research asset populated in Phase 4.9A and now serviced by the first production connector path in Phase 4.9C.
The canonical asset is `dataset.sports.nfl.schedule`.

## Purpose

The NFL schedule is the first event-centric asset in the sports research pipeline.
It establishes the reusable join backbone for later research assets such as results, odds, weather, injuries, officials, coaching, team statistics, and player statistics.

## Canonical Ownership

- runtime owner: `src.data.nfl_schedule_research_asset_population`
- connector owner: `src.connectors.feeds.nfl_schedule`
- acquisition owner: `src.data.historical_dataset_acquisition_runtime`
- certification owner: `src.data.historical_research_asset_certification_runtime`
- lifecycle owner: `src.data.research_asset_lifecycle_runtime`
- storage owner: `src.storage.local_store`
- dashboard readiness owner: `src.services.streamlit_dashboard_data`
- profile owner: `sports:nfl`

## Required Identity

The schedule asset must preserve a stable identity across lifecycle transitions:

- `asset_id`
- `asset_family`
- `market_profile`
- `market`
- `league`
- `sport`
- `season`
- `week_or_date`
- `event_id`
- `game_id`
- `provider`
- `connector`
- `schema_version`
- `lineage_version`
- `asset_name`
- `asset_type`
- `market_type`

## Required Schedule Fields

The minimum certified schedule slice uses the canonical NFL event fields that allow future joins and evidence packages:

- season
- week
- game_id
- event_id
- league
- home_team
- away_team
- neutral_site
- event_start_time
- venue
- timezone
- game_status
- source and provider metadata
- acquisition timestamp
- raw payload lineage
- schema version
- dataset version
- lineage id
- lifecycle state
- certification status

## Lifecycle Path

The schedule asset moves through the shared canonical lifecycle:

`DISCOVERED -> SOURCE_IDENTIFIED -> CONNECTOR_MAPPED -> RAW_ACQUIRED -> INTEGRITY_VERIFIED -> NORMALIZED -> RESEARCH_ASSET_CERTIFIED -> DATASET_CERTIFIED -> FEATURE_READY`

The asset may not skip states, and the previous state must be persisted before promotion.

## Raw Acquisition Cache

The schedule asset must pass through the shared raw acquisition cache before it can be normalized or certified.
The first production connector path uses `src.connectors.feeds.nfl_schedule` and may still fall back to deterministic local fixture mode for offline tests.
The raw payload, provider/source metadata, acquisition timestamp, checksum, connector metadata, and lineage id remain available for auditability.

## Connector Path

The canonical schedule connector path is read-only and reusable:

- connector id: `connector.feeds.nfl_schedule`
- provider id: `nflverse`
- provider role: `primary_acquisition`
- source access type: `open_github_release`
- execution mode: `deterministic_fixture` for offline verification and production-ready adapter shape for later live use

The connector feeds the shared acquisition runtime rather than writing directly to certified tables.

## Time And Entity Alignment

The schedule asset is only trusted when the following values line up:

- sport
- league
- season
- week
- game_id
- home_team
- away_team
- event_start_time
- source timestamp
- provider/source
- lineage record

Rows with mismatched teams, impossible week/season values, missing event times, or malformed provider timestamps must be rejected or flagged for review.

## Query And Worldview Preparation

This asset is intentionally designed to support future Research Query Engine and Worldview questions such as:

- find NFL games by season
- filter by week
- filter by team
- filter by event date
- join schedule to results later
- join schedule to odds later
- join schedule to weather later
- join schedule to injuries later
- return certified evidence packages
- return lifecycle and certification state
- explain why a schedule asset is blocked or uncertified

## Non-Goals

- results
- odds
- weather
- injuries
- officials
- coaching
- team statistics
- player statistics
- props
- betting splits
- advanced metrics

## Reuse Notes

This asset reuses the canonical acquisition runtime, certification runtime, lifecycle runtime, shared storage engine, and dashboard readiness owner rather than introducing a separate NFL schedule database.
