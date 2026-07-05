# Final Repository Structure

## Current Shape

- Runtime/application code lives under `src/`
- Tests live under `tests/`
- Scripts live under `scripts/`
- Documentation lives under `docs/`
- Approved root entrypoints remain:
  - `api_server.py`
  - `main.py`
  - `streamlit_app.py`

## Canonical Runtime Ownership

- `src.core`: math, pricing, portfolio, execution primitives
- `src.data`: local data contracts, historical data, lineage, storage, and canonical data helpers
- `src.providers`: provider contracts, provider policy, and provider-facing adapters
- `src.market_intelligence`: sports, prediction markets, manifold, options, and market signal intelligence
- `src.backtesting`: replay, simulation, strategy profiles, and backtest orchestration
- `src.analytics`: reporting, governance, readiness, summaries, and audits
- `src.research`: experiments, feature control, calibration, and research metadata
- `src.services`: orchestration, runtime facades, dashboard adapters, and shared service wiring
- `src.security`: policy, gates, approval, and secret-safety helpers
- `src.ai`: disabled AI/prompt metadata only
- `src.brokerage`: production-shaped execution and brokerage boundaries, without live activation

## Archived Historical Material

- Historical failure and repository-tree artifacts are archived under `docs/archive/historical_reports/`
- Inventory snapshots are archived under `docs/reports/inventories/`
- Phase-proof and checkpoint artifacts live under `docs/reports/proofs/`, `docs/reports/checkpoints/`, and related report subfolders

## Final Notes

- No runtime package remains outside `src/`
- No active legacy scheduler executable surface remains
- Root Markdown remains restricted to `README.md`
- Remaining root files are approved project files or thin entrypoints only
- The repository is ready for production maintenance and future data/backtesting work
