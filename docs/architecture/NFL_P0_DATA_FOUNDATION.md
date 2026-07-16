# NFL P0 Data Foundation

The NFL P0 data foundation is the first reusable, point-in-time-safe data layer for the NFL vertical slice.
It extends the existing canonical `src.data` / `src.storage` architecture rather than introducing a parallel system.
It now feeds the event-centric historical research database described in `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`.

## Canonical ownership

- `src/storage/local_store.py` owns the physical SQLite/DuckDB table definitions.
- `src/data/nfl_p0_foundation.py` owns NFL P0 row contracts, fixture generation, normalization, validation, and readiness reporting.
- `src/services/streamlit_dashboard_data.py` owns the dashboard-facing adapter for readiness reporting.
- `src/data/local_platform.py` owns the reusable dataset registry, versioning, and dataset-level readiness contracts that the acquisition framework reuses.
- `src/data/historical_research_database.py` owns the event-centric historical acquisition, certification, and readiness orchestration that reuses the NFL P0 foundation.

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
That readiness snapshot now also includes the feature-layer rollup exposed by Phase 5.1B, the math-layer rollup exposed by Phase 5.2, the signal and decision rollups from Phases 5.3 and 5.4, the baseline-backtest-layer rollup exposed by Phase 5.5, and the pipeline-validation-layer rollup exposed by Phase 5.6 so the P0 view can report when the certified research path is ready for Research Intelligence.

## Deferred work

The following remain intentionally deferred:

- real provider ingestion
- paid sources
- player props
- route participation
- advanced player tracking
- model training
- live execution

## Remaining blockers

The foundation now includes the completed historical dataset population layer.
The remaining governed phases are:

- reusable feature snapshots are complete in Phase 5.1B
- reusable mathematical engines are complete in Phase 5.2
- reusable signals are complete in Phase 5.3
- decision rows are complete in Phase 5.4
- baseline backtesting is complete in Phase 5.5
- pipeline validation and hardening are complete in Phase 5.6
- begin Research Intelligence in Phase 5.7 on top of the certified and hardened P0 team/game foundation
