# Duplicate / Overlap Migration Map

Resolved delete-backed groups:
- `src/data/historical_data_sources.py` -> `src/data/historical_sources.py`
- `src/data/source_event_link_resolver.py` -> `src/data/source_event_links.py`
- `src/research/experiment_history_store.py` -> `src/research/history.py`
- `src/providers/compat.py` -> `src/providers/core.py`

Intentional facades kept:
- `src/backtesting/engine.py` -> `src/backtesting/backtesting_engine.py`
- `src/backtesting/backtest_dataset_builder.py` -> `src/backtesting.dataset_builder`
- `src/market_intelligence/market_state_graph.py` -> `src/market_intelligence.manifold`

The migration moved behavior to the canonical owner first, then removed the duplicate shim when safe.
