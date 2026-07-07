# Phase 4.4 Event-Centric Historical Acquisition

## Summary

Phase 4.4 converts the repository from an isolated-row mindset into an event-centric historical research database.
The repository now stores certified events as the shared historical ownership unit, and markets / selections inherit context from those events.
Decision rows are intentionally deferred until Phase 4.6.

## Sources Evaluated

The phase reuses the existing source inventory and open-source history mapping already documented in the repository:

- `src/data/data_source_registry.py`
- `src/data/open_sports_history_sources.py`
- `src/data/historical_sources.py`
- existing NFL P0 fixture and storage contracts

Candidate source families identified for later acquisition work include:

- open NFL data families already present in the registry
- local historical fixtures for deterministic bootstrap and validation
- historical odds and schedule sources already cataloged by the repository

## Sources Selected for This Phase

Selected for the Phase 4.4 foundation:

- local fixture bootstrap only
- canonical NFL P0 fixture as the deterministic starting point
- shared source-to-event reconciliation
- shared local storage and validation layers

This phase does not activate live provider ingestion.

## Event Model

Events now own the shared historical context once per game:

- schedule
- venue
- weather
- officials
- injuries
- coaching
- rest / travel
- team statistics
- event timestamps
- lineage
- provenance

## Market Model

Each event may own multiple markets.
Markets are stored as event-owned records rather than isolated independent rows.
Examples:

- spread
- moneyline
- total
- team total
- first half
- first quarter

## Selection Model

Each market may own multiple selections.
Selections inherit the event and market context and remain linkable through the canonical historical research database.

## Shared Modules Reused

- `src/storage/local_store.py`
- `src.data.validation`
- `src.data.market_profile_registry`
- `src.data.market_profile_contracts`
- `src.data.source_event_links`
- `src.services.streamlit_dashboard_data`
- `src.market_intelligence.market_profiles`

## Duplicate Logic Avoided

- no new provider framework was created
- no market-specific storage engine was created
- no duplicate validation system was created
- no duplicate dashboard readiness system was created
- no decision-row storage primitive was introduced

## Validation Flow

The Phase 4.4 database validates:

- required identifiers
- required timestamps
- lineage metadata
- source metadata
- point-in-time safety
- schema version consistency
- readiness / certification state

## Remaining Gaps

- feature population remains the next phase
- decision-row construction remains deferred to Phase 4.6
- provider ingestion remains intentionally separate from the repository-owned historical database
- additional market families will need their own certified source mappings when they are added

## Recommendation

Keep Phase 4.4 focused on event-centric historical acquisition and certification.
Do not add decision-row storage yet.
Use the same pattern for future markets so MLB, NBA, prediction markets, and options / 0DTE can reuse the same repository-owned historical database shape.
