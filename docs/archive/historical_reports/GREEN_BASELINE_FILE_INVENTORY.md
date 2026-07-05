# Green Baseline File Inventory

## Snapshot Method

This inventory was recorded from:

- `git status --short`
- `git diff --stat`
- `git diff --name-status`

## High-Level Counts

- Tracked deletions: `315`
- Tracked modifications: `167`
- Tracked additions before staging: `0`
- Untracked files before staging: `290`

## Payload Shape

- `src/automation_scheduler_legacy/`
  - large tracked deletion set from the retirement payload
- `src/*`
  - canonical ownership files added and updated across `services`, `market_intelligence`, `data`, `backtesting`, `analytics`, `research`, `providers`, `security`, `core`, `brokerage`, and `ai`
- `tests/*`
  - broad test redirection and stale-assumption cleanup aligned to canonical `src.*` ownership
- root documentation / proof artifacts
  - migration and validation evidence accumulated during the retirement work

## Representative Changed Paths

- Deleted legacy bridge examples:
  - `src/automation_scheduler_legacy/advanced_red_team_provider_policy.py`
  - `src/automation_scheduler_legacy/asof_line_movement_query.py`
  - `src/automation_scheduler_legacy/streamlit_dashboard_data.py`
- Modified canonical runtime examples:
  - `src/services/automation_scheduler_facade.py`
  - `src/services/streamlit_dashboard_facade.py`
  - `src/services/runtime_shared.py`
  - `src/market_intelligence/manifold.py`
  - `src/market_intelligence/sports.py`
  - `src/data/line_movement.py`
- Added canonical ownership examples before staging:
  - `src/services/streamlit_dashboard_data.py`
  - `src/providers/kalshi_adapter_contract.py`
  - `src/analytics/advanced_shape_diagnostics.py`
  - `src/research/feature_ablation_lab.py`

## Checkpoint Reading

The exact staged inventory is preserved by the checkpoint commit itself. This document exists to describe the shape of the tree at the moment the green baseline was captured.
