# Duplicate / Overlap Current Scan

Current repo scan completed against the live tree after the wrapper collapse pass.

Summary:
- Delete-backed duplicate/overlap groups resolved: `4`
- Intentional facades kept: `3`
- False-positive stem collisions reviewed: `multiple domain-specific modules`
- Remaining unresolved duplicate ownership: `0`

The scan focused on:
- AST-visible public symbols
- direct runtime imports
- direct test imports
- direct internal imports
- file-path reads that target executable modules

The following groups were confirmed and handled:
1. `src.backtesting.backtest_dataset_builder` vs `src.backtesting.dataset_builder`
2. `src.backtesting.engine` vs `src.backtesting.backtesting_engine`
3. `src.data.historical_data_sources` vs `src.data.historical_sources`
4. `src.data.source_event_link_resolver` vs `src.data.source_event_links`
5. `src.research.experiment_history_store` vs `src.research.history`
6. `src.market_intelligence.market_state_graph` vs `src.market_intelligence.manifold`
7. `src.providers.compat` vs `src.providers.core`

Only the intentional facades remain on disk where they are still required by compatibility or source-text tests.
