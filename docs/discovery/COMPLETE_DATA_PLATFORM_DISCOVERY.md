# Complete Data Platform Discovery

## Executive view

The repository now has a canonical data platform shape:

`providers / imports / local files -> src.data -> src.market_intelligence -> src.backtesting -> src.analytics / src.services`

No live ingestion occurred during discovery. This phase only documents what the repository already expresses.

## Canonical ownership map

| Domain | Canonical owner |
|---|---|
| Raw sources, normalization, storage boundaries | `src.data` |
| Feature packs, signals, market intelligence, sports / prediction markets / options intelligence | `src.market_intelligence` |
| Leakage-safe dataset / replay / simulation / backtest contracts | `src.backtesting` |
| Reports, governance, summaries, readiness | `src.analytics` |
| Dashboard/runtime orchestration and facades | `src.services` |
| Provider contracts, categories, routing, health | `src.providers` |
| Disabled AI boundary | `src.ai` |
| Security primitives | `src.security` |
| Brokerage / execution boundary | `src.brokerage` |

## Data platform pillars discovered

- `src.data.data_paths` defines the persistent local data directories.
- `src.data.data_source_registry` defines 38 lanes and 287 candidate sources.
- `src.data.model_data_field_catalog` defines model input/output field contracts.
- `src.market_intelligence.feature_packs` defines sport and market feature packs.
- `src.backtesting.backtest_schema` defines the leakage-safe historical snapshot contract.
- `src.services.streamlit_dashboard_data` defines the dashboard display contract.
- `src.providers.categories` defines the provider family taxonomy.
- `src.storage.archive_manifest` defines archive and cleanup gates.

## What is not happening yet

- No live provider activation.
- No brokerage execution.
- No connector activation.
- No AI/LLM activation.
- No production deployment.
- No ingestion rewrite.

## Next architectural step

Complete provider-backed storage contracts for the most mature lanes first, then wire those lanes into reproducible historical snapshots and backtests.
