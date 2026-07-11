# Historical Research Database

This document describes the canonical event-centric historical research database that Phase 4.4 establishes.
It is a reusable repository asset for NFL first and future markets later.
The raw acquisition cache and integrity validation stages are handled by the reusable historical dataset acquisition runtime before certification reaches this database.

## Purpose

The repository now stores certified historical events as the shared historical ownership unit.
Markets and selections inherit context from the event instead of duplicating shared information across many rows.
Decision rows are derived later from the certified event data and are not the storage primitive.

## Canonical Ownership

- `src/storage/local_store.py` owns the physical tables.
- `src/data/local_platform.py` owns the reusable dataset contract, dataset registry, dataset versioning, raw/normalized record lifecycle, validation handoff, and dataset-level readiness reporting.
- `src/data/historical_dataset_acquisition_runtime.py` owns raw acquisition cache staging, integrity validation, and the normalization/certification handoff into this database.
- `src.data.historical_research_asset_certification_runtime.py` owns research asset certification and the asset-level gate before dataset certification.
- `src/data/historical_research_database.py` owns event-centric historical acquisition, normalization, certification, bootstrap, and readiness orchestration.
- `src/data/source_event_links.py` owns source-to-event reconciliation.
- `src.data.validation` owns reusable row validation.
- `src.services.streamlit_dashboard_data.py` owns the dashboard-facing readiness adapter.

## Historical Stages

The canonical historical research database is organized around these stages:

1. `historical_acquisition_batches`
2. `historical_events`
3. `historical_markets`
4. `historical_selections`
5. `historical_research_asset_certifications`
6. `historical_certifications`

The stages live in the shared local storage engine and can be reused by future sports, prediction markets, and options / 0DTE implementations.

## Event-Centric Shape

Events own the shared historical context:

- schedule
- venue
- weather
- officials
- injuries
- coaching
- rest / travel
- team statistics
- timestamps
- lineage
- provenance

Markets belong to events.
Selections belong to markets.
Feature snapshots can be layered on top later.
Decision rows are generated later for backtesting.

## Profile Awareness

The historical research database resolves through the canonical market profile registry and validates against `sports:nfl` first.
That keeps the implementation aligned with the universal sports profile framework while still allowing future market families to adopt the same pattern.

## Reuse Expectations

This architecture should remain reusable for:

- MLB
- NBA
- prediction markets
- options / 0DTE

The reuse contract is:

provider -> raw acquisition cache -> integrity validation -> normalization -> research asset certification -> dataset certification -> event -> market -> selection -> feature snapshot -> decision row

## Phase Boundary

Phase 4.4 creates the historical acquisition foundation.
Phase 4.5A defines the master research engine specification.
Phase 4.5B defines the universal feature registry.
Phase 4.5C defines the universal math engine contracts.
Phase 4.5D establishes the research asset runtime framework.
Phase 4.5E completes the canonical engineering specification rename and keeps the runtime framework aligned with the broader research-engine ownership model.
Phase 4.6 defines the minimum certified historical dataset acquisition framework.
Phase 4.7B builds the reusable historical dataset acquisition runtime with raw acquisition cache and integrity validation.
Phase 4.7C completes the historical research asset certification runtime and gates dataset certification on the required research assets.
Phase 4.8 implements the research asset lifecycle runtime and time/entity alignment certification.
Phase 4.9A populates the NFL schedule research asset.
Phase 4.9B builds the research asset coverage planner and provider selection framework.
Phase 5.0 materializes the historical dataset population layer from certified historical research assets.
Phase 5.1B completed the reusable feature snapshot population layer from the certified historical dataset layer and certified event context.

## Readiness Contract

A historical dataset is ready for future research work when:

- its events are certified,
- its markets and selections are event-linked,
- its timestamps are point-in-time safe,
- its lineage is explicit,
- and its storage is owned by the repository rather than by a provider.
