# Phase 10H23H – Current Data Source Read-Only Panel

## Changes

- **Current Data Source** replaced rebuild-style wording (Advanced Maintenance / Rebuild Dataset) inside the Feature Ablation Lab sidebar.

- SQLite is now clearly identified as the canonical source of testing data for the operator dashboard.

- The new panel is **read-only / status-first**:
  - Shows database path and whether the path exists.
  - Displays status: Connected or Missing.
  - Provides explanatory text that data is loaded automatically and no rebuild is required.

- Normal dashboard users **cannot** switch data sources from the UI.  
  Changing data sources remains **backend configuration / import tooling** (not exposed in the normal workflow).

- A **Refresh Source Status** button is provided, but it only checks the configured SQLite path; it does **not** import data, rebuild model data, scrape, or call APIs.

- No connector, scraper, model math, bankroll math, or schema changes were made.

- Phase 10H24 remains blocked until UI review is complete.

## Files changed

- `streamlit_app.py` – replaced Advanced Maintenance sidebar expander with Current Data Source panel.
- `tests/test_streamlit_dashboard_data.py` – added source-text tests verifying the new panel text.
- `PHASE10H23H_CURRENT_DATA_SOURCE_READ_ONLY_PANEL.md` – created this report.
