# Master Market Input Specification

This document is the governing specification for the repository's market-input layer.
It defines the canonical inventory of inputs, features, signals, targets, confidence metrics, validation metrics, connectors, and engines that future implementations must trace back to.

It sits above the supporting catalogs in `docs/catalogs/` and below the reusable market-profile framework.
The purpose is to keep every future market moving through one canonical specification instead of inventing a separate planning path for each market.

## What This Spec Owns

The repository already has reusable catalog and runtime owners.
This specification explains how they fit together and what lifecycle each market-input family must follow.

The canonical supporting owners are:

- `docs/architecture/MARKET_PROFILE_FRAMEWORK.md`
- `docs/catalogs/COMPLETE_FEATURE_CATALOG.md`
- `docs/catalogs/COMPLETE_METRIC_CATALOG.md`
- `docs/catalogs/FEATURE_DEPENDENCY_GRAPH.md`
- `docs/catalogs/FEATURE_USAGE_BY_MARKET.md`
- `docs/catalogs/COMPLETE_PROVIDER_CATALOG.md`
- `src.data.model_data_field_catalog`
- `src.market_intelligence.feature_packs`
- `src.backtesting.backtest_schema`
- `src.services.streamlit_dashboard_data`
- `src.data.validation`
- `src.providers`
- `src.connectors`

This spec does not replace those owners.
It defines the relationship between them and the lifecycle rules they must satisfy.

## Universal Market Input Domains

| Domain | What it covers | Current state | Recommended canonical owner | Recommended storage location | Tests | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| Market input catalog | Event, market, selection, decision, and lineage inputs | Exists partially | `src.data.model_data_field_catalog` | `docs/contracts/` plus `src.data` runtime contracts | `tests/test_project_status_governance.py`, `tests/test_minimum_backtest_row_contract_docs.py`, `tests/test_master_market_input_specification_docs.py` | High |
| Feature catalog | Canonical feature families and pack definitions | Exists partially | `src.market_intelligence.feature_packs` | `docs/catalogs/` plus `src.market_intelligence` runtime packs | `tests/test_master_market_input_specification_docs.py` | High |
| Signal catalog | Probability, edge, CLV, EV, calibration, and movement signals | Exists partially | `src.market_intelligence` and `src.analytics` | `docs/catalogs/COMPLETE_METRIC_CATALOG.md` | `tests/test_master_market_input_specification_docs.py` | High |
| Target catalog | Outcome, settlement, result, win/loss/push, and profit/loss targets | Exists partially | `src.backtesting` and `src.data` | `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md` | `tests/test_minimum_backtest_row_contract_docs.py`, `tests/test_master_market_input_specification_docs.py` | High |
| Confidence catalog | Calibration, uncertainty, and confidence measures | Exists partially | `src.analytics` and `src.research` | `docs/catalogs/COMPLETE_METRIC_CATALOG.md` | `tests/test_master_market_input_specification_docs.py` | Medium |
| Validation catalog | Point-in-time safety, leakage, schema, and lineage checks | Production ready | `src.data.validation` and `scripts/check_document_lifecycle.py` | `docs/contracts/VALIDATION_FRAMEWORK.md` | `tests/test_document_lifecycle_governance.py`, `tests/test_master_market_input_specification_docs.py` | High |
| Connector catalog | Provider adapters, fixture loaders, and source reconciliation | Exists partially | `src.providers`, `src.connectors`, `src.data.source_event_links` | `docs/contracts/PROVIDER_ADAPTER_CONTRACTS_V1.md` | `tests/test_master_market_input_specification_docs.py` | High |
| Engine catalog | Storage, certification, feature, backtest, research, dashboard, and analytics engines | Exists partially | `src.storage`, `src.data`, `src.backtesting`, `src.research`, `src.services`, `src.analytics` | `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` | `tests/test_master_market_input_specification_docs.py` | High |

## Metric Lifecycle Tracking

Every metric in the repository should be able to report its lifecycle state.
No metric should jump directly to production without the earlier states being satisfied.

| State | Meaning |
| --- | --- |
| Defined | The metric has a canonical name and purpose. |
| Schema Ready | The expected fields and shapes are documented. |
| Source Identified | At least one usable source or source family is known. |
| Connector Ready | A canonical acquisition or adapter path exists. |
| Historical Data Ready | Certified historical rows can supply the metric. |
| Math Implemented | The calculation is implemented in the canonical runtime owner. |
| Signal Ready | The metric can be consumed as a reusable signal or feature. |
| Backtested | The metric has been evaluated against historical evidence. |
| Production Ready | The metric is usable in the current canonical workflow. |

The lifecycle tracking rule is:

Defined -> Schema Ready -> Source Identified -> Connector Ready -> Historical Data Ready -> Math Implemented -> Signal Ready -> Backtested -> Production Ready

## Market Coverage

| Market family | Status | Notes |
| --- | --- | --- |
| Universal | Exists partially | Governing rules apply to every market family. |
| Sports | Exists partially | NFL is the first validated sports instance. |
| Prediction Markets | Scaffold only | Framework ready; market-specific runtime remains future work. |
| Options / 0DTE | Scaffold only | Framework ready; market-specific runtime remains future work. |
| Futures | Documentation only | Roadmap-level future market. |
| Crypto | Documentation only | Roadmap-level future market. |
| Macro | Documentation only | Roadmap-level future market. |

## Audit Summary

The current repository already has canonical owners for:

- market profile contracts
- shared storage
- shared validation
- dashboard readiness reporting
- backtest boundary contracts
- provider and connector ownership
- feature catalogs
- metric catalogs

The current repository still treats several families as partial because the architecture exists before every market-specific implementation does.
That is intentional.

The specification rule is:

1. Search for an existing canonical owner first.
2. Extend that owner if it already exists.
3. Create a new owner only when no canonical owner exists.
4. Keep storage, validation, and lineage shared across markets.

## Reuse Rule

Future work must trace every new input, metric, signal, target, confidence value, validation rule, connector, and engine back to this specification.
If a future implementation needs a new planning document, the first question is whether this spec already covers the responsibility.

## Out Of Scope

This specification does not:

- ingest data
- implement provider integrations
- implement mathematical formulas
- build feature pipelines
- build backtests
- build dashboards

It only defines the canonical inventory and lifecycle that later phases must follow.

## Naming Review

This document still uses the historical name `MASTER_MARKET_INPUT_SPECIFICATION.md`, but its scope now spans inputs, features, signals, targets, confidence metrics, validation metrics, connectors, and engines.
If later phases continue to broaden the scope, a future rename to `MASTER_RESEARCH_ENGINE_SPECIFICATION.md` may be appropriate.
Do not perform that rename during Phase 4.5B.
