# Phase 10H9A – Real Sample Import Hardening

## Changes

1. **Updated stale phase text** in `automation_scheduler/historical_data_sources.py` – `get_model_testing_source_plan()` now lists phases 10H4–10H8 as complete and Phase 10H9 as in progress.

2. **Normalised Football-Data event_date** in `automation_scheduler/historical_odds_importers.py` – added `_normalize_football_data_event_date()` helper that converts `dd/mm/YYYY` to `YYYY-MM-DD`.  This fixes the ordering of `event_date_min` and `event_date_max` returned by the SQLite store.

3. **Hardened settlement fields** for Football‑Data CSV rows – the fields `home_score`, `away_score`, `final_result`, and `winner` are already present and correctly derived; no code changes were needed.

4. **No‑leakage rules** – `historical_backtest_bridge.py` already excludes result fields from `features_known_at_decision_time`. No changes required.

5. **Dashboard honesty** – The existing dashboard code already shows a warning when settled_count is 0 (`snapshot` based). No changes required.

6. **Added/updated tests**:
   - `test_football_data_date_normalization` – verifies DD/MM/YYYY conversion.
   - `test_football_data_settlement_fields` – ensures scores, final_result, winner are correct.
   - `test_event_date_min_max_correct_after_format_normalization` – checks SQLite ordering.

All existing tests pass.
