# Phase 10H12A: Line Volatility Expression

## Summary

- Added line volatility expression.
- Line volatility is high‑low range over snapshots.
- Shows up movement, down movement, total range.
- Works with `line_value` when available.
- Falls back to odds volatility when only odds are available.
- Decision‑only data has limited volatility value.
- Next phase remains Phase 10H13 Sport Feature Packs.

## Details

### Part 0 – Fix existing readiness bug

The `calculate_line_movement_readiness` function now correctly treats any dict with at least one of the summary keys as a pre‑computed summary. Missing counts default to 0.

### Part 1 – New helpers in `historical_line_movement.py`

- `group_line_snapshots_for_volatility(rows) -> dict[str,list[dict]]` – groups snapshots by event_id, market, selection, player_name, team_name, bookmaker.
- `calculate_line_volatility_for_group(rows) -> dict` – computes line/odds highs, lows, ranges, move‑up/down, volatility score, level.
- `calculate_line_volatility_summary(rows) -> dict` – aggregates per‑group results into a summary with counts.
- `get_line_volatility_summary_from_sqlite(conn, limit=10000) -> dict` – reads from the `historical_line_snapshots` table.

Thresholds:
- line_total_range >= 2.0 → "high"
- line_total_range >= 0.5 → "medium"
- odds_total_range >= 50 → "high"
- odds_total_range >= 15 → "medium"
- otherwise → "low" (or "unknown" if no data)

### Part 2 – Dashboard helper in `streamlit_dashboard_data.py`

`get_line_volatility_snapshot_for_dashboard(db_path) -> dict` – opens SQLite store, initialises schema, calls `get_line_volatility_summary_from_sqlite`, returns keys safe for JSON serialisation.

### Part 3 – Streamlit Data Explorer

Added a new “Line Volatility” sub‑section under Data Explorer that displays:
- counts per volatility level
- a table of per‑group volatility metrics
- plain‑language explanations

### Part 4 – Updated tests

- Existing `test_calculate_line_movement_readiness` passes unchanged.
- New tests for `calculate_line_volatility_for_group`, `calculate_line_volatility_summary`, `get_line_volatility_summary_from_sqlite`.
- New tests in `test_streamlit_dashboard_data.py` for the dashboard helper and for Streamlit page text.
