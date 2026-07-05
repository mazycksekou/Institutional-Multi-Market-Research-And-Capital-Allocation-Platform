# Phase 10H12 – Line Movement Schema + Odds Snapshot Store

## Overview

This phase adds a safe line‑movement foundation so the operator can track **opening**, **decision**, **current**, and **closing** odds snapshots across all market families (moneyline, spread/runline, totals, team totals, player props).

## What was added

### New file: `automation_scheduler/historical_line_movement.py`

- **Constants**  
  `LINE_MOVEMENT_SCHEMA_VERSION = "10H12"`

- **New SQLite table:** `historical_line_snapshots`  
  Columns defined in the module, supporting every market family.  
  Includes indexes on `event_id`, `(sport, market)`, `source_key`, `snapshot_label`, `snapshot_time`, `player_name`.

- **Schema initialisation**  
  `initialize_line_movement_schema(conn)` – idempotent, works alongside existing `historical_odds` tables.

- **Conversion helpers**  
  - `canonical_row_to_line_snapshots(row)` – always creates a **decision** snapshot from `odds_at_decision_time`.  
  - If `opening_odds` / `opening_line` exist, an **opening** snapshot is created.  
  - If `closing_odds` / `closing_line` exist, a **closing** snapshot is created.  
  - If `current_odds` exist, a **current** snapshot is created.  
  - `market_family` is classified using a local copy of `classify_market_family`.

- **Upsert / query**  
  - `upsert_line_snapshots(conn, snapshots)` – idempotent `INSERT … ON CONFLICT DO UPDATE`.  
  - `upsert_line_snapshots_for_canonical_rows(conn, rows)` – convenience wrapper.  
  - `query_line_snapshots(conn, …)` – filter by sport, league, market, source_key, snapshot_label, player_name, date range.

- **Summary / readiness**  
  - `summarize_line_movement_store(conn)` – returns totals, counts per label, distinct values, and `line_movement_ready` / `clv_ready` booleans.  
  - `calculate_line_movement_readiness(summary_or_rows)` – standalone helper.  

- **Backfill**  
  - `backfill_line_snapshots_from_historical_odds(conn)` – reads existing canonical rows from the historical odds SQLite store and creates matching decision snapshots.

### Updated file: `automation_scheduler/streamlit_dashboard_data.py`

- `import_historical_file_to_sqlite_for_dashboard` now also calls `upsert_line_snapshots_for_canonical_rows` after importing canonical rows.  
  Failures are logged as warnings only, never block the import.

- New helper:  
  `get_line_movement_snapshot_for_dashboard(db_path)` – opens/init DB, initialises line movement schema, returns summary.  

### Updated file: `streamlit_app.py`

- Data Explorer page now includes a **“Line Movement Readiness”** section showing:
  - total snapshots
  - opening / decision / current / closing snapshot counts
  - `line_movement_ready` and `clv_ready` booleans
  - missing fields explanation
  - Plain‑language note: *“Baseline testing can run with decision odds only. Line movement and CLV require opening/closing snapshots.”*

### New test file: `tests/test_historical_line_movement.py`

Covers:
1. Schema creation.
2. Decision snapshot from `odds_at_decision_time`.
3. Opening + closing snapshots when extra fields exist.
4. Idempotent upsert.
5. Query filtering.
6. Summary counts.
7. Readiness flags.
8. Backfill from existing Football‑Data rows.

### Updated test file: `tests/test_streamlit_dashboard_data.py`

- Added test for `get_line_movement_snapshot_for_dashboard`.
- Added source‑text tests verifying the “Line Movement Readiness” header and the explanation sentence appear in `streamlit_app.py`.

## Design decisions

- **No new dependencies.**  
  Uses only stdlib `sqlite3`, `hashlib`, `datetime`.

- **Idempotent schema.**  
  `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` – existing databases are never broken.

- **Backwards compatible.**  
  Existing `historical_odds` tables and functions are unchanged.   All existing tests pass.

- **No leakage.**  
  Snapshot values are stored as they are; the Feature Control Lab continues to block leakage fields for pre‑decision features.

- **Decision‑only baseline still works.**  
  If the data has only `odds_at_decision_time` (Football‑Data style), a decision snapshot is created, `line_movement_ready` is `False`, and the dashboard clearly communicates the limitation.

- **CLV concept added.**  
  When both opening and closing snapshots exist, the store can (in future) compute closing‑line value. The readiness flag `clv_ready` signals that the raw data is present.

## Next step

**Phase 10H13 – Sport Feature Packs.**  
Expand feature groups for sport‑specific fields (pace, offensive rating, injuries, etc.) and integrate them into the regression engine.
