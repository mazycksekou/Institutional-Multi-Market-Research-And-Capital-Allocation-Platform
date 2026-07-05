# Phase 10H11 – Feature Control Lab + Dashboard Instructions Page

## Overview
This phase adds:

- **Instructions page** explaining every dashboard tab and the overall operator workflow.
- **Feature Control Lab** inside the Data Explorer tab, allowing the operator to add/remove field groups and data points.
- **Feature Profile selector** on the Model Projection page, giving the operator control over which fields are used as model features.
- **Blocked leakage fields** that can never end up inside the pre‑decision feature snapshot (final_result, winner, closing_odds, CLV, profit_loss, etc.).

## What changed

### `automation_scheduler/streamlit_dashboard_data.py`
- Added constants `FEATURE_CONTROL_VERSION` and `DEFAULT_FEATURE_CONTROL_PROFILE`.
- Added functions:
  - `get_feature_control_profiles()` – returns five profile options: Available Baseline, Odds Only, Remove Line Movement, Settlement Check, Custom.
  - `get_feature_group_definitions()` – returns the same groups used by Data Explorer (core_event, line_core, line_movement, settlement, team_stats, player_stats, projection_control).
  - `get_never_feature_fields()` – returns the list of leakage/grading fields that cannot be used as model features.
  - `build_feature_control_config()` – builds a config dictionary from profile name, include/exclude groups, include/exclude fields.
  - `apply_feature_control_to_row()` – returns a deep‑copied row with `features_known_at_decision_time` filtered according to the config.
  - `summarize_feature_control_impact()` – computes available / missing / removed field counts and returns human‑readable interpretation.
  - `get_dashboard_tab_instructions()` – returns instructions for each dashboard tab.
  - `get_overall_operator_workflow_steps()` – returns an ordered list of 10 workflow steps.
- All new code respects the “never mutate input” rule and never includes leakage fields.

### `streamlit_app.py`
- Added **Instructions** menu entry and full page.
- Added **Feature Control Lab** section inside the Data Explorer page (profile selector, include/exclude group multiselect, impact summary).
- Added **Feature Profile** selection section on the Model Projection page, shown before the “Run Projection” button.
- Added warning: “Never use final results, winner, closing line, CLV, or profit/loss as pre‑decision model features.”
- Added explanation: “Missing data does not stop testing. It tells us which model version we are testing.”

### `tests/test_streamlit_dashboard_data.py`
- Added seven tests validating:
  - profile list contains expected values.
  - never feature fields contain leakage items.
  - `apply_feature_control_to_row` removes leakage from the snapshot but preserves top‑level grading fields.
  - input row is not mutated.
  - `summarize_feature_control_impact` returns all expected keys.
  - operator interpretation string contains baseline text.
  - tab instructions include Instructions, Data Explorer, Model Projection, Data Quality Check.
  - workflow steps are ordered.

## Design decisions
- Leakage fields are hard‑blocked in `apply_feature_control_to_row` regardless of the profile.
- Group definitions mirror the Data Explorer coverage so operators see consistent field families.
- Feature profiles are safe defaults that help the operator test with what is available, not pretend missing fields exist.
- The phase does **not** change SQLite schema, backtesting engine, bankroll math, or add any network calls / dependencies.

## Next step
**Phase 10H12** – Line Movement Schema + Odds Snapshot Store.
