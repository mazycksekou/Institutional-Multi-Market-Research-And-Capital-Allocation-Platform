# Phase 10H19 – Historical Line Movement Readiness Layer

## Purpose

Phase 10H19 adds a **readiness inspection layer** for the local
`historical_line_snapshots` SQLite table.  The layer:

- checks whether the required table exists
- verifies all required schema columns are present
- produces coverage metrics (snapshots, linked/unlinked events, sports, market
  families, bookmakers, timestamp ranges)
- determines whether the store is **ready** for time‑series line movement
  analysis

## What This Phase Does NOT Do

- ❌ Connect to any vendor API
- ❌ Import paid line movement data
- ❌ Scrape any website
- ❌ Alter the existing `historical_odds` or `historical_results` schema
- ❌ Run model projections or backtests
- ❌ Add presets or risk rules

Every function is safe for missing or empty databases; they never raise
uncaught exceptions.

## Roadmap Checkpoint

The project **must stop at Phase 10H23** (Line Movement Data Quality Dashboard)
before any real vendor, API, or scraper connector is built.  Phase 10H19 is
the vendor‑neutral readiness layer; a commercial connector or two‑source import
will plug into the same readiness path later.

## Next Phase

**Phase 10H20 – Vendor‑Neutral Line Movement Import Contract**  
Define import contracts (no paid data, no scraping) that can be fulfilled by
future commercial packages or dual‑source SQLite imports.

## File Created

- `automation_scheduler/line_movement_readiness.py`

## Files Modified

- `automation_scheduler/streamlit_dashboard_data.py` — added bridge function
- `streamlit_app.py` — added non‑final readiness section under Data Explorer
- `tests/test_line_movement_readiness.py` — new test suite
- `tests/test_streamlit_dashboard_data.py` — added bridge and source‑text tests
