# Streamlit Dashboard Test Redirection Map After 10K8ZMI

Legacy to canonical mappings used for `tests/test_streamlit_dashboard_data.py`:

- `automation_scheduler.streamlit_dashboard_data` -> `src.services.streamlit_dashboard_facade`
- `automation_scheduler.historical_odds_sqlite` -> `src.data.historical_odds`
- `automation_scheduler.line_movement_readiness` -> `src.data.line_movement`
- `automation_scheduler.historical_line_movement` -> `src.data.line_movement`
- `automation_scheduler.experiment_history_store` -> `src.research.history`

Canonical helper additions made for this phase:
- `src.backtesting.strategy_profiles`
- `src.data.field_catalog`
- `src.data.historical_odds`
- `src.data.line_movement`
- `src.market_intelligence.feature_packs`
- `src.research.feature_control`
- `src.research.history`
- `src.services.ops_workflow`

The facade now resolves these symbols from canonical `src.*` modules without needing the legacy scheduler namespace.
