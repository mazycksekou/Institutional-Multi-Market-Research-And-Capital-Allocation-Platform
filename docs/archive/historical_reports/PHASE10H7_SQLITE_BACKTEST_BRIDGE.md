# Phase 10H7 – SQLite Backtesting Bridge

## Status

Completed.  This phase adds a lightweight **bridge** that reads validated
historical‑odds rows from the Phase 10H6 SQLite store, converts them to the
canonical backtest row format, and feeds them to the existing backtesting
engine (``automation_scheduler.backtesting_engine.run_backtest``).

## What this phase includes

- **`automation_scheduler/historical_backtest_bridge.py`** – the core module
  that provides:
  - **Constants**: ``HISTORICAL_BACKTEST_BRIDGE_VERSION = "10H7"``,
    ``DEFAULT_HISTORICAL_MODEL_ID``, ``DEFAULT_SQLITE_BACKTEST_LIMIT``.
  - **Conversion helpers**:
    - ``sqlite_odds_row_to_backtest_row(row, …)`` – single row conversion.
    - ``sqlite_odds_rows_to_backtest_rows(rows, …)`` – batch conversion.
  - **Query adapter**: ``query_sqlite_backtest_rows(conn, …)`` – wraps
    ``query_historical_odds_rows`` and converts the result.
  - **Bridge runner**: ``run_sqlite_historical_backtest(conn, …)`` – queries
    SQLite, converts rows, and calls ``run_backtest``.  Returns a dict with
    ``ok``, ``bridge_version``, ``model_id``, ``query``, ``rows_loaded``,
    ``rows_converted``, ``backtest_result``, and ``projection_summary``.
  - **Summary**: ``summarize_sqlite_historical_backtest(result)`` – compact
    report with bets, ROI, drawdown, sports/leagues/markets/sources, and
    ``projection_ready`` flag.
  - **Filter options**: ``get_sqlite_backtest_filter_options(conn)`` – reads
    available sports, leagues, markets, source keys, date range, and total
    odds count, ready for Streamlit dropdowns in Phase 10H8.

- **`tests/test_historical_backtest_bridge.py`** – 7 test cases covering:
  1. Single row conversion contains required fields.
  2. ``features_known_at_decision_time`` excludes forbidden leakage fields.
  3. Batch conversion returns correct number of rows.
  4. ``get_sqlite_backtest_filter_options`` returns expected structure.
  5. ``run_sqlite_historical_backtest`` returns ``ok=True`` and includes
     ``projection_summary``.
  6. ``summarize_sqlite_historical_backtest`` always returns stable keys.
  7. Query filters (sport, league, market, source_key, date range) work.

## Design principles

- **Read‑only on SQLite.**  The bridge never writes to the SQLite store.
- **No changes to the backtesting engine.**  The bridge is a pure data
  adapter; the engine remains the canonical owner of backtest logic.
- **No bankroll‑math rewrite.**  Existing simulation code is untouched.
- **No Streamlit changes yet.**  UI integration is reserved for the next phase.
- **Safe feature snapshots.**  The bridge constructs
  ``features_known_at_decision_time`` from a whitelist of pre‑decision fields,
  explicitly excluding final result, scores, profit/loss, closing line, and
  CLV.

## Next phase (Phase 10H8)

Add Streamlit‑backed SQLite dropdowns, import controls, and projection
controls.  The bridge's ``get_sqlite_backtest_filter_options`` and
``run_sqlite_historical_backtest`` are the two main API endpoints that the
Streamlit layer will call.
