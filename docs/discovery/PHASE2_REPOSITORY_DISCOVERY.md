# Phase 2 Repository Discovery

## Baseline

- Branch: `phase-6-api-slimming`
- HEAD at start of this phase: `1f5ce1ba22b2f798b989e6ab740e2c0b00ea3b29`
- Smoke: green (`19 passed`)
- Ops check: `verification_ok`
- No live ingestion was performed.

## Repository inventory

| Bucket | Count |
|---|---:|
| Tracked Python files | 1164 |
| `src/` Python files | 610 |
| `tests/` Python files | 546 |
| `scripts/` Python files | 6 |
| Runtime entrypoints | 2 |

## Runtime entry surfaces

| Surface | Canonical target |
|---|---|
| `main.py` | `src.api.app` |
| `api_server.py` | `src.api.server` |
| `streamlit_app.py` | `src.services.streamlit_dashboard_facade` |

## High-fan-in runtime hubs

| Module | Why it matters |
|---|---|
| `src/services/streamlit_dashboard_facade.py` | Most imported dashboard facade |
| `src/services/scheduler_config.py` | Config and filename sanitization hub |
| `src/security/policy.py` | Security policy hub |
| `src/data/data_paths.py` | Storage boundary hub |
| `src/brokerage/contracts.py` | Brokerage contract hub |
| `src/market_intelligence/multi_sport_model_registry.py` | Sports/model registry hub |
| `src/providers/contracts.py` | Provider contract hub |

## Discovered market domains

- Sports: NBA, WNBA, NCAA Basketball, NFL, NCAA Football, MLB, NHL, Soccer, Tennis, MMA/UFC, Boxing, Golf, Esports, Formula 1, Formula E, NASCAR, IndyCar, MotoGP, Badminton, Darts, Handball, Lacrosse, Pickleball, Rugby, Snooker, Table Tennis, Volleyball, Water Polo, Cricket, AFL
- Prediction markets: `prediction_markets`, `kalshi`, `polymarket`
- Financial markets: stocks, ETFs, bonds, rates, macro, major assets, FX/currencies
- Context / signal lanes: weather, news/sentiment, government/open data, transportation/logistics, health/public context, security/ops, officials, injuries, lineups, schedules, news context

## Current support snapshot

- Providers: candidate-source coverage exists for 34 lanes; 0 lanes have verified sources.
- Historical data: backfill contracts exist, but no verified source-backed historical lanes yet.
- Live data: execution remains disabled across the stack.
- Feature engineering: canonical feature groups and model input catalogs exist.
- Backtesting: canonical contracts exist for leakage-safe replay and simulation.
- Streamlit: dashboard pages and metric labels are present for the main workflows.
- APIs: `main.py` and `api_server.py` remain the entry points.
- Research: experiment/history/calibration scaffolding exists.
- Intelligence: market intelligence packages are canonicalized under `src.market_intelligence`.
- Models: model input/output contracts exist, with a concrete basketball NBA artifact under `src/sports/models/compressed`.
- Reporting: analytics, readiness, and dashboard report surfaces are present.

## What this phase established

The repository already has enough canonical structure to express one data platform contract across:

1. `src.data` for sources, contracts, storage boundaries, and normalization.
2. `src.market_intelligence` for market/sport feature construction and signals.
3. `src.backtesting` for leakage-safe snapshots, replay, and simulation.
4. `src.analytics` for reports, governance, and summaries.
5. `src.services` for dashboard/runtime facades.
6. `src.providers` for provider contracts, categories, and routing.
