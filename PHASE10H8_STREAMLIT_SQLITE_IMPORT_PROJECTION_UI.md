# Phase 10H8 – Streamlit SQLite Import + Projection UI

## What was done

- The operator dashboard can now **import approved local files** (CSV/JSON) into the SQLite historical‑odds store.
- SQLite store contents can be inspected (table counts, sports, leagues, markets, date range).
- **SQLite‑backed historical model projections** can be run and summarised directly from the dashboard.
- Everything remains **paper‑testing only**; no real bets, no downloads, no scraping, no network calls.

## New capabilities

### Import Historical Data menu
- Dropdown of source keys extracted from `historical_data_sources.py` (only KEEP / KEEP_TOOL / DOWNGRADE / EXPLORATION rows are shown).
- Upload box for CSV/JSON files (saved to a local runtime directory via `save_historical_upload_for_import`).
- Text field for a server‑side absolute path.
- Calls `import_historical_file_to_sqlite_for_dashboard` which opens/initialises the SQLite store and runs the correct importer.
- Result is displayed as JSON and a short success/warning message.

### Data Quality Check menu
- Existing file inventory and schema preview remain unchanged.
- A new **SQLite Snapshot** section reads:
  - Total odds rows
  - Filter options (sports, leagues, markets, source_keys, event_date_min/ max)
  - Table counts for every table
  - Validation result (expected tables are present)

### Model Projection menu
- Original source plan and priority sources are still shown.
- A new **SQLite Projection** section contains:
  - Text input for the database path.
  - Filter fields: sport, league, market, source_key, start_date, end_date, row limit, optional model probability override.
  - “Run SQLite‑backed projection” button.
- After execution the dashboard displays a metric row with:
  - rows_loaded, rows_converted, bets, no_bets, P/L, ROI %, max drawdown %, projection_ready status and reason.
- Raw result and filter options can be expanded.

## What was *not* done (no changes to)
- Downloads, scraping, network calls, external dependencies, SQLAlchemy.
- `backtesting_engine`, bankroll math, historical odds validation.
- Existing test suite (all original tests pass).
- Any committed runtime database file – all SQLite files are ephemeral (tested with `tmp_path`).

## Next phases

- **Phase 10H9** – real sample data import run / operator walkthrough.
- A future phase may add download helpers, but only with explicit approval.
- SQLite import / projection can be extended with more filter controls and a richer UI.

## Files changed/created

| File | Status |
|------|--------|
| `automation_scheduler/streamlit_dashboard_data.py` | edited |
| `streamlit_app.py` | edited |
| `tests/test_streamlit_dashboard_data.py` | edited |
| `PHASE10H8_STREAMLIT_SQLITE_IMPORT_PROJECTION_UI.md` | created |

## Testing

All new tests are located in `tests/test_streamlit_dashboard_data.py` and do **not** import Streamlit. They use `tmp_path` and tiny fake CSV/JSON files.

Run with:
```bash
python -m pytest tests/test_streamlit_dashboard_data.py -v
```
