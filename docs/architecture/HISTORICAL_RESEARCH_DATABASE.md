# Historical Research Database

This document describes the canonical event-centric historical research database that Phase 4.4 establishes.
It is a reusable repository asset for NFL first and future markets later.

## Purpose

The repository now stores certified historical events as the shared historical ownership unit.
Markets and selections inherit context from the event instead of duplicating shared information across many rows.
Decision rows are derived later from the certified event data and are not the storage primitive.

## Canonical Ownership

- `src/storage/local_store.py` owns the physical tables.
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
5. `historical_certifications`

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

provider -> acquisition -> archive -> normalization -> certification -> event -> market -> selection -> feature snapshot -> decision row

## Phase Boundary

Phase 4.4 creates the historical acquisition foundation.
Phase 4.5 will populate reusable historical feature snapshots.
Phase 4.6 will construct decision rows from certified historical data.

## Readiness Contract

A historical dataset is ready for future research work when:

- its events are certified,
- its markets and selections are event-linked,
- its timestamps are point-in-time safe,
- its lineage is explicit,
- and its storage is owned by the repository rather than by a provider.
