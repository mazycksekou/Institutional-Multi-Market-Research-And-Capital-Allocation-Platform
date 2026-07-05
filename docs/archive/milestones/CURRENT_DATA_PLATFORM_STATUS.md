# Current Data Platform Status

## Summary

The canonical local data platform is implemented on top of the existing repo plumbing instead of beside it.

It reuses:

- historical odds storage helpers
- line-movement storage helpers
- validation helpers
- metadata helpers
- lineage helpers
- provider contracts / metadata helpers
- feature-pack helpers
- backtest bridge helpers
- dashboard data helpers
- local data-path helpers

## Canonical ownership

- Storage engine: `src.storage.local_store`
- Local platform coordinator: `src.data.local_platform`
- Dashboard adapter: `src.services.streamlit_dashboard_data`

## Implemented behavior

- SQLite-backed local storage
- import-safe optional DuckDB detection
- dataset registration
- dataset versioning
- validation storage
- normalized/raw record storage
- feature snapshot storage
- lineage edge storage
- synthetic fixture generation
- dashboard snapshot readback

## Validation status

- `python -m compileall src tests`: passed
- import sweep across canonical packages: passed
- `pytest -m smoke -q`: passed
- `python scripts/ops_check.py --mode local --output text --skip-network`: passed
- full gate: blocked by unrelated stale documentation-assumption tests that still expect missing root-level phase report files from earlier migration phases

## Notable implementation details

- The synthetic fixture is multi-market and multi-asset-class, but intentionally leaves the top-level dataset sport blank so the validator does not misclassify the mixed fixture as a single-sport dataset.
- Validation records now store `status = validated` or `rejected`, so the dashboard snapshot can summarize the actual validation outcome.
- DuckDB is not installed in the current environment, so DuckDB support is correctly reported as unavailable rather than failing at import time.

## Current blocker

The remaining blocker is repo-wide and unrelated to the local data platform itself: a large set of pre-existing full-gate tests still expect root-level documentation artifacts that are absent in the current cleaned-up repository state.

## Tracking note

`src.data.local_platform.py` is valid runtime code, but it is currently matched by the repository's broad `*data` ignore rule. It will need a force-add or a narrower ignore exception before any future commit can include it.
