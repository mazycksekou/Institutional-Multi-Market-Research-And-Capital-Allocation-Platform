# Phase 3B Repository Discovery

## Scope

This discovery pass focused on the existing canonical runtime surfaces that already own odds, line movement, dashboards, validation, lineage, metadata, provider contracts, feature packs, and backtesting helpers.

The goal was reuse-first local platform implementation, not a parallel data stack.

## Reused canonical owners

- `src.data.historical_odds_sqlite`
- `src.data.historical_odds`
- `src.data.line_movement`
- `src.services.streamlit_dashboard_data`
- `src.services.streamlit_dashboard_facade`
- `src.analytics.model_governance.data_lineage`
- `src.data.validation`
- `src.data.metadata`
- `src.providers.contracts`
- `src.providers.registry`
- `src.market_intelligence.feature_packs`
- `src.data.source_quality_scoring`
- `src.data.data_paths`
- `src.backtesting.dataset_builder`
- `src.backtesting.historical_bridge`
- `src.backtesting.engine`

## Newly owned canonical surfaces

- `src.storage.local_store`
- `src.data.local_platform`

## Ownership decisions

| responsibility | existing module found | current owner | reuse decision | canonical target | action | reason |
|---|---|---|---|---|---|---|
| historical odds store | `src.data.historical_odds_sqlite`, `src.data.historical_odds` | `src.data` | KEEP_AS_CANONICAL | `src.data.historical_odds_sqlite` | WRAP_EXISTING | Existing odds persistence already owns historical odds ingestion and query behavior. |
| line movement store | `src.data.line_movement`, `src.data.historical_line_movement` | `src.data` | KEEP_AS_CANONICAL | `src.data.line_movement` | WRAP_EXISTING | Existing line-movement store already owns canonical snapshots and readiness helpers. |
| dashboard data adapters | `src.services.streamlit_dashboard_data` | `src.services` | KEEP_AS_CANONICAL | `src.services.streamlit_dashboard_data` | WRAP_EXISTING | Dashboard helpers already compose odds, line movement, backtest, and readiness views. |
| lineage helpers | `src.analytics.model_governance.data_lineage` | `src.analytics.model_governance` | KEEP_AS_CANONICAL | `src.analytics.model_governance.data_lineage` | WRAP_EXISTING | Existing lineage helper is safe, reusable, and importable. |
| validation helpers | `src.data.validation` | `src.data` | KEEP_AS_CANONICAL | `src.data.validation` | WRAP_EXISTING | Existing validation helpers already cover local-only dataset validation. |
| metadata helpers | `src.data.metadata` | `src.data` | KEEP_AS_CANONICAL | `src.data.metadata` | WRAP_EXISTING | Existing metadata helper is the canonical source for local dataset descriptors. |
| provider metadata helpers | `src.providers.contracts`, `src.providers.registry` | `src.providers` | KEEP_AS_CANONICAL | `src.providers.contracts` | WRAP_EXISTING | Provider contracts and registry remain the canonical owner of provider metadata. |
| feature-pack helpers | `src.market_intelligence.feature_packs` | `src.market_intelligence` | KEEP_AS_CANONICAL | `src.market_intelligence.feature_packs` | WRAP_EXISTING | Feature-pack ownership already exists and should not be duplicated. |
| source quality helpers | `src.data.source_quality_scoring` | `src.data` | KEEP_AS_CANONICAL | `src.data.source_quality_scoring` | WRAP_EXISTING | Source quality scoring already owns local source quality tiers. |
| local data path helpers | `src.data.data_paths` | `src.data` | KEEP_AS_CANONICAL | `src.data.data_paths` | WRAP_EXISTING | Path ownership already exists and is reused by the local platform. |
| backtest storage helpers | `src.backtesting.dataset_builder`, `src.backtesting.historical_bridge`, `src.backtesting.engine` | `src.backtesting` | KEEP_AS_CANONICAL | `src.backtesting.dataset_builder` | WRAP_EXISTING | Backtest persistence and extraction behavior already exists canonically. |
| storage backend abstraction | none | none | MISSING | `src.storage.local_store` | CREATE_NEW_ONLY_IF_MISSING | Generic local storage tables were not owned by an existing reusable module. |
| local platform registry / versioning / lineage persistence / feature snapshots | none | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | The repo had helpers for rows and lineage records, but not a persistent local platform. |
| synthetic fixture proof | none | none | MISSING | `src.data.local_platform` | CREATE_NEW_ONLY_IF_MISSING | A deterministic synthetic dataset was needed to prove ingest/validate/store/read-back. |
| dashboard local-platform snapshot | `src.services.streamlit_dashboard_data` | `src.services` | WRAP_EXISTING | `src.services.streamlit_dashboard_data` | WRAP_EXISTING | The dashboard proof should be a thin adapter over the canonical local platform. |

## Discovery summary

- Reuse-first composition was possible for odds, line movement, provider metadata, validation, lineage, and dashboard surfaces.
- The only new canonical code introduced was the generic local storage engine and the local platform coordinator.
- DuckDB is not installed in the current environment, so DuckDB support is import-safe and reported as unavailable.
