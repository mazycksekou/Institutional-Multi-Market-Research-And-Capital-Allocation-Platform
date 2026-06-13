# Phase 10H6 – SQLite Historical Odds Store

## Status

Completed.  This phase adds a local SQLite storage layer that receives
**validated canonical historical‑odds rows** produced by Phase 10H5
(``automation_scheduler/historical_odds_importers.py``).

No downloading, no scraping, no model backtesting, no Streamlit changes yet.

## What this phase includes

- **`automation_scheduler/historical_odds_sqlite.py`** – the core module that
  provides:
  - **Constants**: ``SQLITE_SCHEMA_VERSION = "10H6"``,
    ``HISTORICAL_ODDS_SQLITE_TABLES``, ``DEFAULT_QUERY_LIMIT = 1000``.
  - **Id helpers**: ``utc_now_iso()``, ``stable_hash_id(prefix, parts)``,
    ``make_event_id(row)``, ``make_odds_id(row, event_id)``.
  - **Connection & schema**: ``connect_historical_odds_db(db_path)``,
    ``initialize_historical_odds_db(conn)`` (idempotent).
  - **Inspection**: ``get_sqlite_table_counts(conn)``.
  - **Insert / upsert**: ``upsert_canonical_historical_odds_rows(conn, rows)``
    validates each row, upserts into four tables:
    1. ``source_imports`` – records each import batch.
    2. ``historical_events`` – unique events identified by source + date + teams.
    3. ``historical_odds`` – one row per outcome, uses UPSERT to stay idempotent.
    4. ``historical_results`` – final match results (linked by event).
  - **File import convenience**: ``import_historical_odds_file_to_sqlite(conn, source_key, path)``.
  - **Query**: ``query_historical_odds_rows(conn, …)`` with filters for sport,
    league, market, source_key, date range; returns ``list[dict]``.
  - **Summary**: ``summarize_historical_odds_db(conn)``.
  - **Validation**: ``validate_sqlite_store(conn)`` checks that all required
    tables exist.

- **`tests/test_historical_odds_sqlite.py`** – 9 test cases covering:
  - Table creation.
  - Insert of valid row.
  - Idempotent re‑insert.
  - Rejection of invalid rows.
  - Query filters (sport, league, market, source_key, date range).
  - Summary report.
  - End‑to‑end import of a tiny Football‑Data CSV.
  - Store validation.
  - Deterministic identifiers.

## Design principles

- **SQLite after importers.**  Phase 10H5 converts raw files; Phase 10H6 stores
  only the canonical rows that have been validated.
- **No downloads / scraping.**  Importers operate on local files.
- **No model backtesting yet.**  The store is a passive data repository.
- **No Streamlit changes.**  UI integration is reserved for later phases.

## Upcoming phases

| Phase | Goal |
|-------|------|
| 10H7  | Wire SQLite rows into model backtesting. |
| 10H8  | Wire SQLite‑backed dropdowns into Streamlit. |
