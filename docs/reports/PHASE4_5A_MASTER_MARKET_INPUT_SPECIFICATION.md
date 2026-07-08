# Phase 4.5A Master Market Input Specification

## Summary

Phase 4.5A creates the repository's master market-input specification.
The goal is to define the research platform before any new market-specific implementation work begins.

This phase is architecture and governance only.
It does not ingest historical data.
It does not implement provider integrations.
It does not implement mathematical calculations.
It does not build feature engineering.
It does not build backtests.

## Existing Canonical Owners Reused

- `docs/architecture/MARKET_PROFILE_FRAMEWORK.md`
- `docs/catalogs/COMPLETE_FEATURE_CATALOG.md`
- `docs/catalogs/COMPLETE_METRIC_CATALOG.md`
- `docs/catalogs/FEATURE_DEPENDENCY_GRAPH.md`
- `docs/catalogs/FEATURE_USAGE_BY_MARKET.md`
- `src.data.model_data_field_catalog`
- `src.market_intelligence.feature_packs`
- `src.backtesting.backtest_schema`
- `src.services.streamlit_dashboard_data`
- `src.data.validation`
- `src.providers`
- `src.connectors`

## Discovery Result

The repository already had reusable catalogs for features, metrics, providers, and market profiles.
What it lacked was a single governing specification that says how those catalogs relate to each other and how each new market input must mature.

This phase fills that gap by defining:

- the universal market input domains
- the metric lifecycle
- the market coverage expectation
- the canonical reuse rule
- the owner boundaries for inputs, signals, targets, confidence values, connectors, and engines

## Audit Matrix

| File or owner | Tests | Recommended canonical owner | Priority | Current status |
| --- | --- | --- | --- | --- |
| `docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md` | `tests/test_master_market_input_specification_docs.py` | `docs/architecture` | High | Current truth |
| `docs/catalogs/COMPLETE_METRIC_CATALOG.md` | `tests/test_master_market_input_specification_docs.py` | `src.data.model_data_field_catalog` | High | Documentation only |
| `docs/catalogs/COMPLETE_FEATURE_CATALOG.md` | `tests/test_master_market_input_specification_docs.py` | `src.market_intelligence.feature_packs` | High | Documentation only |
| `docs/catalogs/FEATURE_DEPENDENCY_GRAPH.md` | `tests/test_master_market_input_specification_docs.py` | `src.data.model_data_field_catalog` and `src.market_intelligence.feature_packs` | Medium | Documentation only |
| `src.data.model_data_field_catalog` | `tests/test_project_status_governance.py`, `tests/test_minimum_backtest_row_contract_docs.py` | `src.data` | High | Exists partially |
| `src.market_intelligence.feature_packs` | `tests/test_master_market_input_specification_docs.py` | `src.market_intelligence` | High | Exists partially |
| `src.data.validation` | `tests/test_document_lifecycle_governance.py` | `src.data` | High | Production ready |
| `src.services.streamlit_dashboard_data` | `tests/test_historical_research_database.py` | `src.services` | Medium | Production ready |
| `src.storage.local_store` | `tests/test_historical_research_database.py` | `src.storage` | High | Production ready |
| `src.providers` and `src.connectors` | `tests/test_master_market_input_specification_docs.py` | `src.providers` and `src.connectors` | High | Exists partially |
| `src.backtesting.backtest_schema` | `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md` | `src.backtesting` | High | Exists partially |

## Metric Lifecycle Summary

The metric lifecycle is now governed by the master specification:

Defined -> Schema Ready -> Source Identified -> Connector Ready -> Historical Data Ready -> Math Implemented -> Signal Ready -> Backtested -> Production Ready

The main architectural value of this phase is that the repository now has a permanent rule for how any future metric or engine should mature.

## Senior Systems Engineer Review

The architecture is moving in the right direction.
The main strengths are:

- reuse of canonical owners instead of parallel planning systems
- a clear market-input lifecycle
- a shared pattern that works for sports, prediction markets, and options
- a clean separation between current truth and historical reports

The main recommendation is to keep the spec concise and authoritative.
If future phases need more detail, they should extend the existing catalog owners rather than creating another market-input document.

## Worldview Intelligence Review

This phase helps the future Worldview layer by making inputs and lifecycle states explicit.
That improves:

- experiment generation
- evidence quality
- lineage
- reproducibility
- future mathematical implementation

The important design win is that Worldview will be able to ask which metric family or engine state is ready without inventing a second truth source.

## Next Phase

Phase 4.5B should define the universal feature registry on top of this specification.
That registry will translate the abstract market-input inventory into canonical feature ownership.
