# Duplicate / Overlap Groups

| Group | Files | Symbols / Surface | Canonical owner | Action |
| --- | --- | --- | --- | --- |
| DO-01 | `src/backtesting/backtesting_engine.py`, `src/backtesting/engine.py` | backtest replay, runner, report helpers | `src.backtesting.backtesting_engine` | Keep `engine.py` as facade |
| DO-02 | `src/backtesting/dataset_builder.py`, `src/backtesting/backtest_dataset_builder.py` | paper-only fixture validation, dataset building | `src.backtesting.dataset_builder` | Keep legacy filename as facade |
| DO-03 | `src/data/historical_sources.py`, `src/data/historical_data_sources.py` | historical source registry | `src.data.historical_sources` | Delete duplicate shim |
| DO-04 | `src/data/source_event_links.py`, `src/data/source_event_link_resolver.py` | source-event linking / resolver helpers | `src.data.source_event_links` | Delete duplicate shim |
| DO-05 | `src/research/history.py`, `src/research/experiment_history_store.py` | experiment history store | `src.research.history` | Delete duplicate shim |
| DO-06 | `src/market_intelligence/manifold.py`, `src/market_intelligence/market_state_graph.py` | market-state graph helpers | `src.market_intelligence.manifold` | Keep legacy filename as facade |
| DO-07 | `src/providers/core.py`, `src/providers/compat.py` | provider core compatibility alias | `src.providers.core` | Delete duplicate shim |

No group requires a second implementation to remain canonical.

