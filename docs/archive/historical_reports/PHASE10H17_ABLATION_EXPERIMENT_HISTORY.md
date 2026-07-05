# Phase 10H17 – Ablation Experiment History

## Overview

Phase 10H17 persists Feature Ablation Lab and Calibration‑Ready Strategy Filter
run results so operators can compare experiments over time.

Streamlit refreshes no longer erase useful model‑testing experiments.

### What it does

- Saves the full output of `run_feature_ablation_lab` and
  `run_calibration_strategy_filter` to a dedicated SQLite table
  (`experiment_history_runs`).
- Extracts stable numeric metrics (total rows, included/excluded row counts,
  settled count, wins/losses, net result, ROI, win rate, etc.).
- Stores JSON‑serialized active fields, removed fields, included/excluded
  sports, included/excluded market families, performance breakdown, warnings,
  and the raw result.
- Supports comparison against a baseline run with deltas for ROI, win rate,
  and included row count.

### What it does NOT do

- Create preset experiment profiles.
- Change historical odds, settlement, or line movement schemas.
- Rewrite backtesting_engine or bankroll math.
- Add network calls, scraping, or dependencies.
- Expose leakage/result/settlement fields (`final_result`, `winner`,
  `profit_loss`, `closing_odds`, `closing_line`, `clv`) as active
  pre‑decision fields. The `sanitize_experiment_history_result` function
  removes them and adds a warning.

### Architecture

- **Backend** (`automation_scheduler/experiment_history_store.py`) owns all
  persistence and comparison logic.
- **Dashboard bridge** in `automation_scheduler/streamlit_dashboard_data.py`
  provides three helper functions:
  - `get_experiment_history_snapshot_for_dashboard`
  - `save_experiment_history_run_for_dashboard`
  - `compare_experiment_history_runs_for_dashboard`
- **Streamlit UI** in `streamlit_app.py` calls only these helpers.
  It never writes SQL directly.

### Storage

A new table `experiment_history_runs` is created on first use with the
following columns (modelled after the Phase 10H17 specification):

```sql
CREATE TABLE experiment_history_runs (
    run_id TEXT PRIMARY KEY NOT NULL,
    created_at TEXT NOT NULL,
    run_type TEXT NOT NULL,
    run_label TEXT,
    notes TEXT,
    mode TEXT,
    sport_key TEXT,
    market_family TEXT,
    selected_groups_json TEXT,
    selected_fields_json TEXT,
    removed_fields_json TEXT,
    active_fields_json TEXT,
    included_sports_json TEXT,
    excluded_sports_json TEXT,
    included_market_families_json TEXT,
    excluded_market_families_json TEXT,
    performance_json TEXT,
    roi_by_sport_json TEXT,
    roi_by_market_family_json TEXT,
    warnings_json TEXT,
    config_json TEXT,
    result_json TEXT,
    total_rows INTEGER,
    included_row_count INTEGER,
    excluded_row_count INTEGER,
    eligible_rows INTEGER,
    skipped_rows INTEGER,
    settled_count INTEGER,
    wins INTEGER,
    losses INTEGER,
    pushes INTEGER,
    net_result REAL,
    roi_percent REAL,
    win_rate_percent REAL
);
```

### User‑Facing Wording

Where winner markets are explained, the dashboard uses “2‑Way / 3‑Way Moneyline”.
The legacy alias `moneyline_or_1x2` is never shown as the preferred label.

### Files Changed

| File | Change |
|------|--------|
| `automation_scheduler/experiment_history_store.py` | New file (back‑end persistence & comparison) |
| `tests/test_experiment_history_store.py` | New file (unit tests) |
| `automation_scheduler/streamlit_dashboard_data.py` | Added three bridge functions and import |
| `streamlit_app.py` | Added “Experiment History” menu, save buttons, listing, comparison, and run detail |
| `tests/test_streamlit_dashboard_data.py` | Added five new tests for bridge functions and streamlit text |
| `PHASE10H17_ABLATION_EXPERIMENT_HISTORY.md` | This report |

### Next Phase

**Phase 10H18 – Calibration Report Export / Operator Review Pack**.
Will provide a one‑click export of a selected run as a human‑readable
Markdown/PDF file for offline review.

### Version

`EXPERIMENT_HISTORY_STORE_VERSION = "10H17"`
