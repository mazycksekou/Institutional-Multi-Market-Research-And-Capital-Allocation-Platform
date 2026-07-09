# Phase 4.9A - NFL Schedule Research Asset Population

## Summary

Phase 4.9A populates the first minimum-schema NFL research asset: `dataset.sports.nfl.schedule`.
The phase uses a deterministic local source path so the runtime can prove the acquisition, cache, normalization, certification, lifecycle, and dashboard readiness flow without uncontrolled live provider calls.

## Existing Abstractions Discovered

- `src.data.historical_dataset_acquisition_runtime`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.data.nfl_p0_foundation`
- `src.data.validation`
- `src.storage.local_store`
- `src.services.streamlit_dashboard_data`
- `src.data.market_profile_contracts`
- `src.data.market_profile_registry`

## Existing Abstractions Reused

- shared raw acquisition cache owner
- shared integrity validation helpers
- shared research asset certification runtime
- shared research asset lifecycle runtime
- shared market profile registry
- shared local storage engine
- shared dashboard readiness adapter
- shared NFL P0 normalization and validation flow

## Research Asset Populated

- asset_id: `dataset.sports.nfl.schedule`
- profile: `sports:nfl`
- source role: deterministic local fixture
- source path: raw acquisition cache -> normalization -> research asset certification -> dataset certification -> lifecycle recording

## Raw Acquisition Cache

- raw schedule rows are staged through the shared raw acquisition cache
- raw payloads retain source metadata, acquisition timestamps, checksum values, and lineage ids
- the repository stores the original raw evidence before certification

## Integrity Validation

- required schedule fields are checked before promotion
- time/entity alignment is enforced for sport, league, season, week, game id, home and away teams, and event start time
- missing or malformed source timestamps block certification

## Normalization

- schedule rows are normalized into the canonical event-centric `nfl_schedule` table
- normalization preserves join keys for future results, odds, weather, injury, official, and team-stat joins

## Lifecycle And Certification

- lifecycle states are advanced in order
- the asset becomes `research_asset_certified` only after normalized rows and validation evidence exist
- the dataset becomes `certified` only after the schedule asset passes certification

## Dashboard And Readiness

- readiness snapshots expose asset id, lifecycle state, certification status, row count, coverage seasons, missing required fields, alignment failures, source role, and readiness percentage
- the dashboard path remains shared rather than introducing a schedule-only dashboard

## Query And Worldview Readiness

- the schedule asset preserves enough metadata to support future Research Query Engine and Worldview evidence packages
- future queries can join this asset to results, odds, weather, injuries, and team statistics without redesigning the repository
- certification and lifecycle metadata remain available for blocked or uncertified evidence requests

## Engineering Improvements Implemented

- deterministic local source path for the first research asset
- raw acquisition cache usage proven before certification
- schedule asset certificate and dataset certificate both persisted through shared owners
- lifecycle state transitions recorded through the canonical lifecycle runtime

## Engineering Improvements Deferred

- additional NFL assets such as results, odds, weather, injuries, rest/travel, officials, coaching, and team statistics
- broader market expansion beyond the NFL schedule slice
- Research Query Engine implementation
- Worldview implementation

## Senior Systems Engineer Review

The implementation is reusable because it stays on shared owners and keeps NFL-specific logic narrow.
The main engineering advantage is that the repository now proves the full schedule-asset path without creating a parallel NFL database.

Recommendation: keep the next phase equally narrow and use the same runtime path for results before broadening the schema.

## Worldview / Research Query Engine Review

The schedule asset is queryable later because it preserves stable identifiers, lifecycle state, certification state, timestamps, and lineage metadata.
That is enough for future evidence packages, blocked-asset explanations, and joins to later research assets.

## Readiness for Phase 4.9B

The repository is ready for Phase 4.9B, which should populate the NFL results research asset using the same shared runtime path.
