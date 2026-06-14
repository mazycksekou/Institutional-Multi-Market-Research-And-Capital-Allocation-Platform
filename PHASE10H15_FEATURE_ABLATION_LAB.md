## Phase 10H15A – Feature Ablation Lab Streamlit Wiring Check

### Changes

- Added `get_feature_ablation_lab_snapshot_for_dashboard` in `streamlit_dashboard_data.py`.
- Added "Feature Ablation Lab" page/section in `streamlit_app.py`.
- Added wiring tests in `test_streamlit_dashboard_data.py`.

### Behavior

- **Start with all safe fields** – the operator sees all selectable fields active.
- **Remove fields** – operators manually strip away fields via multiselect controls.
- **Mode** – Single Sport (sport/market changes) or All Sports.
- **All Sports** – excludes calibration‑not‑ready sports from ROI; excluded sports are displayed with their reason.
- **UI** – displays included sports, excluded sports, ROI by sport table, overall performance table, active fields list, removed fields list, and warnings.
- **Backend is source of truth** – Streamlit only controls and displays results from `run_feature_ablation_lab`.

### Not added

- No preset experiment profiles.
- No duplicate ablation logic.
- No SQLite schema changes.
- No bankroll or backtesting math changes.
