# PHASE10K8ZFE1 Universal Product Language Alignment

## Executive Summary
10K8ZFE1 aligns user-facing product language before AI integration and before backtesting. The dashboard now shows `Aggressive` instead of `Aggressive paper only`, while backward-compatible alias handling remains available for saved configs. The report also separates risk preset language from scenario-based backtest language.

This phase does not change risk math, bankroll sizing behavior, or backtest execution behavior.

## Current HEAD
Current HEAD before patch: `6e83e1f304ca5be3026cd676949f93958cfbb70d`

## Purpose
Align universal product language so operators can distinguish a risk preset from a scenario mode.

## Scope
- Update Streamlit/dashboard labels
- Preserve compatibility aliases for old saved values
- Document risk preset and scenario terminology
- Add focused regression tests

## Non-Goals
- no AI integration
- no ML training
- no backtest runner
- no broker execution
- no real trade execution
- no files deleted

## Streamlit Risk Preset Language
The risk preset controls sizing and simulated money management, not missing-data handling and not scenario selection.

The current user-facing risk preset list is:
- None - no risk preset adjustment
- Tiny Risk Demo
- Conservative
- Moderate
- Aggressive
- Custom

The old wording `Aggressive paper only` remains only as a compatibility alias for saved configs. It is not shown in the dropdown.

## Scenario-Based Backtest Language
Scenario mode controls missing-data handling for backtests.
Scenario mode controls missing-data handling.
scenario mode controls missing-data handling

The scenario labels are:
- Baseline / Imputed
- Strict / Complete Cases Only
- Stress / Adverse Missing-Data Fill

This is a separate concept from the risk preset.

## Compatibility Handling
Backward compatibility is preserved by mapping `Aggressive paper only` -> `Aggressive` for saved config values.

The implementation keeps the old label available as an internal alias while presenting only the new label to users.

## Files Changed
- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`
- `tests/test_streamlit_dashboard_data.py`
- `tests/test_phase10k8zfe1_universal_product_language_alignment.py`
- `PHASE10K8ZFE1_UNIVERSAL_PRODUCT_LANGUAGE_ALIGNMENT.md`

## Tests Run
- `pytest tests/test_phase10k8zfe1_universal_product_language_alignment.py -q`

## Acceptance Results
- old aggressive label removed from UI: yes
- new aggressive label present: yes
- scenario language documented: yes
- compatibility preserved: yes
- no AI integration: yes
- no ML training: yes
- no backtest runner: yes
- no broker execution: yes
- no real trade execution: yes
- no files deleted: yes

## Next Phase Recommendation
Proceed to 10K8ZFE Duplicate Code / Math / Metrics / Signal Evidence Scan.
