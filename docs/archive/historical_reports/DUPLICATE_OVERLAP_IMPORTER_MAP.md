# Duplicate / Overlap Importer Map

## DO-01 `engine.py`
- Runtime importers: `src/services/streamlit_dashboard_data.py`, `src/services/scheduler_runner.py`
- Test importers: `tests/test_backtesting.py`, `tests/test_backtesting_engine.py`, `tests/test_historical_replay.py`, `tests/test_phase10k8zl9b_internal_scheduler_self_import_break.py`
- Internal callers: none remaining beyond the facade surface

## DO-02 `backtest_dataset_builder.py`
- Runtime importers: none direct
- Test importers: source-text phase tests and fixture helper tests
- Internal callers: none

## DO-03 `historical_data_sources.py`
- Runtime importers: none direct
- Test importers: none direct
- Internal callers: none

## DO-04 `source_event_link_resolver.py`
- Runtime importers: none direct
- Test importers: none direct
- Internal callers: none

## DO-05 `experiment_history_store.py`
- Runtime importers: none direct
- Test importers: none direct
- Internal callers: none

## DO-06 `market_state_graph.py`
- Runtime importers: none direct after `graph_relationship_mapper.py` moved to `manifold.py`
- Test importers: `tests/test_phase10k8zl6_market_intelligence_runtime_test_redirection.py`
- Internal callers: none

## DO-07 `providers/compat.py`
- Runtime importers: none direct
- Test importers: none direct
- Internal callers: none

