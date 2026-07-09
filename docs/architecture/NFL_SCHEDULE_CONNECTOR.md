# NFL Schedule Connector

This document defines the canonical connector-backed path for the NFL schedule research asset.
The connector is the first production connector path for `dataset.sports.nfl.schedule`.

## Purpose

The connector bridges the shared acquisition runtime to a provider capability without creating NFL-specific storage or certification ownership.
It exists to keep the schedule asset reproducible, auditable, and reusable for future sports markets.

## Canonical Ownership

- connector module: `src.connectors.feeds.nfl_schedule`
- acquisition runtime: `src.data.historical_dataset_acquisition_runtime`
- certification runtime: `src.data.historical_research_asset_certification_runtime`
- lifecycle runtime: `src.data.research_asset_lifecycle_runtime`
- storage owner: `src.storage.local_store`
- dashboard readiness owner: `src.services.streamlit_dashboard_data`
- coverage planner owner: `src.market_intelligence.research_asset_coverage_planner`

## Provider Capability Discovery

The connector exposes provider metadata so the coverage planner can reason about acquisition options without making runtime assumptions:

- provider id
- connector id
- provider name
- provider role
- supported assets
- supported fields
- supported markets
- historical depth
- update frequency
- point-in-time safety
- licensing notes
- cost class
- certification readiness
- quality score

## Field-Level Provenance

The connector preserves field-level provenance for the minimum schedule fields:

- season
- week
- game_id
- event_id
- league
- home_team
- away_team
- event_start_time
- venue
- timezone
- neutral_site
- game_status

Each field preserves:

- source provider
- source field name
- acquisition timestamp
- raw payload reference
- lineage id
- confidence or quality metadata when available

## Acquisition Flow

Provider or local fixture
-> Connector
-> Raw Acquisition Cache
-> Integrity Validation
-> Normalization
-> Research Asset Certification
-> Dataset Certification
-> Lifecycle Update
-> Historical Research Database
-> Coverage Planner
-> Dashboard / Readiness Snapshot

## Offline Mode

The connector supports deterministic fixture mode for offline validation.
That keeps the runtime shape production-ready without requiring live credentials or uncontrolled network calls during tests.

## Non-Goals

- results
- odds
- weather
- injuries
- team statistics
- player statistics
- mathematical engines
- signals
- backtesting

## Reuse Notes

The connector feeds the shared acquisition runtime and raw cache rather than writing directly to certified tables.
That keeps the schedule asset aligned with the same reusable path future markets will use.
