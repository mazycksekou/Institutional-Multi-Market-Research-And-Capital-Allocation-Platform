# Phase 10H23C – Feature Ablation Lab Results & Settings Clarity

## Changes made

- **Feature Ablation Lab results** were restructured to be decision‑first:
  - Plain‑English verdict at the top.
  - Readable KPI cards (Decisions, Net Result, ROI %, Win Rate, Ready Status, Rows tested).
  - Active Fields and Removed Fields shown as counts with collapsible expanders.
  - Detailed view organized into tabs (Summary, Field Impact, Performance Curves, Comparison, Raw Data).
- **Long Active Fields output** was moved behind expanders; only the count is shown by default.
- **Risk preset** belongs in Bankroll Settings; removed as a primary control from Feature Ablation Lab.  
  A read‑only context label is shown instead.
- **Regression tactic** and **Let tactic replace old model chance** moved under a collapsed **Advanced Model Method** expander.
- **Custom feature weights** moved under a collapsed **Experimental Field Weights** expander.
- **Rebuild dataset** moved under a collapsed **Advanced Maintenance** expander.
- **Require core fields** remains a readiness filter; its explanation is shown in a collapsed **Readiness Filter** expander.
- **Synthetic Line Movement Sandbox** is clearly labeled as demo‑only and not model evidence.
- **No vendor/API/scraper connector** was added.
- Phase 10H24 remains blocked until UI review is complete.

## Tests added/updated

- Added source‑text tests to `test_streamlit_dashboard_data.py` verifying the exact operator‑facing strings required in the specification.

## Files changed

- `streamlit_app.py`
- `tests/test_streamlit_dashboard_data.py`
- Created `PHASE10H23C_FEATURE_ABLATION_RESULTS_AND_SETTINGS_CLARITY.md`
