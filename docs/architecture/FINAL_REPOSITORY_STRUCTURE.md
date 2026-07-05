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
- The repository root still contains a small number of non-runtime support artifacts from earlier phases; they are treated as repository material, not as runtime ownership
- GitHub Actions, when present, is an automation wrapper and not a runtime location

## Canonical Runtime Ownership

- `src.core`: math, pricing, portfolio, execution primitives
- `src.data`: canonical data contracts, historical data, lineage, storage, and local data helpers
- `src.providers`: provider contracts, provider policy, and provider-facing adapters
- `src.connectors`: external-source connectors and compatibility adapters that normalize external inputs
- `src.market_intelligence`: sports, prediction markets, manifold, options, and market signal intelligence
- `src.backtesting`: replay, simulation, strategy profiles, and backtest orchestration
- `src.analytics`: reporting, governance, readiness, summaries, and audits
- `src.research`: experiments, feature control, calibration, and research metadata
- `src.services`: orchestration, runtime facades, dashboard adapters, and shared service wiring
- `src.security`: policy, gates, approval, and secret-safety helpers
- `src.ai`: disabled AI/prompt metadata only
- `src.brokerage`: production-shaped execution and brokerage boundaries, without live activation
- `src.storage`: persistence primitives and backend abstractions used by canonical data ownership

## Archived Historical Material

- Historical failure and repository-tree artifacts are archived under `docs/archive/historical_reports/`
- Consolidated milestone summaries are archived under `docs/archive/milestones/`
- Inventory snapshots are archived under `docs/reports/inventories/`
- Phase-proof and checkpoint artifacts live under `docs/reports/proofs/`, `docs/reports/checkpoints/`, and related report subfolders

## Governance Surface

- Root Markdown is restricted to `README.md`
- Documentation lives under `docs/`
- Contract and architecture summaries are indexed from `docs/architecture/`
- Automated validation is performed locally through `scripts/check_root_markdown.py`, `scripts/check_openapi_contract.py`, `scripts/check_architecture.py`, and `scripts/ops_check.py`
- Optional CI wrappers call the same local scripts instead of duplicating validation logic

## Final Notes

- No runtime package remains outside `src/`
- No active legacy scheduler executable surface remains
- Root Markdown remains restricted to `README.md`
- Remaining root files are approved project files or thin entrypoints only
- The repository is ready for production maintenance and future data/backtesting work
