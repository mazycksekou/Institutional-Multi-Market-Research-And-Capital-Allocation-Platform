# Phase 10H23G: Product UI Simplification – One Main Testing Page + Bottom Helper

## What changed

- **Test One Sport** and **Test All Sports** were removed from the sidebar main menu.
- Their functionality was folded into the **Feature Ablation Lab** page as run modes (True Code Baseline, One Sport, All Ready Sports, Custom Ablation Test).
- Main menu now exposes only **Feature Ablation Lab**, **Bankroll Settings**, and **Instructions**.
- **Plain‑English Helper** (formerly `show_easy_dictionary()`) was moved to the bottom of the Feature Ablation Lab page, behind a collapsed expander.
- The run mode radio was relabeled from `["Single Sport", "All Sports"]` to `["One Sport", "All Ready Sports"]`.
- No model math, bankroll math, historical schema, or connector logic was changed.
- Phase 10H24 remains blocked until the simplified UI is reviewed.

## Files edited

- `streamlit_app.py` – sidebar menu, mode labels, helper placement.
- `tests/test_streamlit_dashboard_data.py` – updated menu‑content checks and added new UI‑text tests.
- `PHASE10H23G_PRODUCT_UI_SIMPLIFICATION.md` – this report.
