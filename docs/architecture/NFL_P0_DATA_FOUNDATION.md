# NFL P0 Data Foundation

The NFL P0 data foundation is the first reusable, point-in-time-safe data layer for the NFL vertical slice.
It extends the existing canonical `src.data` / `src.storage` architecture rather than introducing a parallel system.
It now feeds the event-centric historical research database described in `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`.

## Canonical ownership

- `src/storage/local_store.py` owns the physical SQLite/DuckDB table definitions.
- `src/data/nfl_p0_foundation.py` owns NFL P0 row contracts, fixture generation, normalization, validation, and readiness reporting.
- `src/services/streamlit_dashboard_data.py` owns the dashboard-facing adapter for readiness reporting.
- `src/data/historical_research_database.py` owns the event-centric historical acquisition and readiness orchestration that reuses the NFL P0 foundation.

## Tables

The foundation now has canonical table support for:

- `nfl_games`
- `nfl_schedule`
- `nfl_results`
- `nfl_odds_snapshots`
- `nfl_weather_snapshots`
- `nfl_team_stats_snapshots`

Each table carries:

- schema version
- dataset version
- snapshot time
- lineage ID
- source metadata
- quality metadata
- point-in-time guard fields

The snapshot tables also retain a shared NFL game context so schedule, results, odds, weather, and team-efficiency rows can be joined on the same canonical game identifiers.

## Validation flow

Validation is performed in `src/data/nfl_p0_foundation.py` and checks:

- required fields
- schema version consistency
- lineage / snapshot / version metadata
- source metadata presence
- point-in-time safety
- numeric field hygiene

Validation treats zero-valued fields as valid data and only flags truly missing values. The odds contract allows `line_value` to remain empty for markets such as moneyline snapshots where no spread or total line exists.

## Normalization flow

Normalization converts canonical NFL P0 rows into the storage-ready shape:

- stable row identifiers
- dataset versioning
- source signatures
- JSON payload capture for provenance
- completeness and quality metadata

## Streamlit readiness reporting

The dashboard helper exposes a readiness snapshot for the NFL P0 foundation without owning the underlying storage.
The dashboard layer stays thin and only reports readiness.

## Deferred work

The following remain intentionally deferred:

- real provider ingestion
- paid sources
- player props
- route participation
- advanced player tracking
- backtesting
- model training
- live execution

## Remaining blockers

The foundation is structurally ready, but the repository still needs future phases to:

- acquire the minimum certified historical dataset in Phase 4.6
- certify historical datasets in Phase 4.7
- populate reusable historical feature snapshots in Phase 4.8
- implement reusable mathematical engines in Phase 4.9
- build decision rows in Phase 5.0
- expand beyond the P0 team/game foundation when the data layer is proven stable
