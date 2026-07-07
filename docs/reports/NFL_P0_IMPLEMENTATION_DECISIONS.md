# NFL P0 Implementation Decisions

This report records the implementation choices made for Phase 4.3.

## What we implemented

- canonical SQLite/DuckDB table support for the NFL P0 data layer
- deterministic NFL fixture generation for a small reusable baseline
- normalization helpers that attach source metadata, version metadata, lineage IDs, snapshot times, and quality metadata
- validation helpers that enforce point-in-time safety
- dashboard-facing readiness reporting

## Storage ownership

The physical tables are owned by `src/storage/local_store.py`.
The NFL-specific semantics are owned by `src/data/nfl_p0_foundation.py`.
The dashboard surface is a thin adapter in `src/services/streamlit_dashboard_data.py`.

## Validation flow

Validation happens before storage writes and again when readiness is reported.
The checks focus on:

- required fields
- schema version consistency
- source metadata presence
- lineage / version metadata
- snapshot timing before kickoff for pregame tables
- result timing after kickoff for results tables

Two implementation details were hardened during the phase:

- zero-valued fields such as `indoor_flag = 0` are treated as valid data rather than missing values
- moneyline odds snapshots do not require a `line_value` field because that market has no spread/total line

## Why a deterministic fixture

This phase intentionally avoids real ingestion and provider work.
The deterministic fixture proves the storage and validation contracts end-to-end while keeping the implementation local, reproducible, and portable.

## Remaining blockers

- no live or open-data ingestion is connected yet
- the NFL P0 foundation is still a local bootstrap path, not a complete historical ingest pipeline
- baseline backtesting still depends on later phases

## Deferred work

- historical source integration
- injury snapshots
- player-level feature engineering
- backtesting and calibration
- model training
- paper trading
- live deployment
