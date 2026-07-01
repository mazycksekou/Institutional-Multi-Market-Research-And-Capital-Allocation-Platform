# Compatibility Removal Proof

Compatibility surfaces preserved because they still have active runtime or test usage:
- `src/backtesting/engine.py`
- `src/backtesting/backtest_dataset_builder.py`
- `src/market_intelligence/market_state_graph.py`
- `src/services/automation_scheduler_facade.py`
- `src/services/streamlit_dashboard_facade.py`

These are intentional facades, not duplicate ownership.
