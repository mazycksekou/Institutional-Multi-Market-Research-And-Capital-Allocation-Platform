# PHASE10K8ZF4 Asset-Grade Repo Clean Inventory

## Executive Summary
This 10K8ZF4 inventory establishes the current repository shape at senior-systems-engineer quality before any controlled data loader, backtest runner, footprint implementation, ORB integration, or results UI work.

The repo is currently in research/backtest mode only and still carries a large local `data/` tree and a generated `reports/` tree. Both are ignored by `.gitignore` and are not tracked in git.

## Senior Systems Engineering Standard
Asset-grade means:
- every runtime entrypoint is explicit
- every local data tree is classified
- every generated artifact is ignored or quarantined
- every future backtest boundary is documented before execution work starts
- no ambiguous fake/paper/testing-room product language remains in the visible workflow

## Current HEAD
Current HEAD: `c32a7d1`

## Current Repo Shape
Top-level structure observed in the repository:
- `src/`
- `automation_scheduler/`
- `research/`
- `providers/`
- `betting_providers/`
- `docs/`
- `tests/`
- `data/`
- `reports/`
- `scripts/`
- `models/`
- `math_models/`
- `model_governance/`
- `live_market_intelligence/`
- `temporal_ops/`
- `unused/`
- root-level application and service entrypoints such as `main.py`, `api_server.py`, and `streamlit_app.py`

## README Status
`README.md` did not exist before this phase and is created in this inventory phase.

## .gitignore Status
`.gitignore` existed before this phase and now explicitly covers local data and generated artifact classes:
- `data/`
- `reports/`
- `.env`
- `.pytest_cache/`
- `.venv/`
- `*.sqlite`
- `*.db`

## Local Data Inventory
`data/` exists.

Observed size:
- 6,856 files
- 1,595,262,938 bytes total

Observed file types:
- `.json` 6,807
- `.md` 32
- `.csv` 14
- `.db` 2
- `.jsonl` 1

Observed references in source/tests include:
- `src/core/settings.py`
- `src/services/model_backtest_service.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/paper_trade_ledger.py`
- many tests that assume local fixtures, local runtime state, or local historical odds storage

## Local Reports Inventory
`reports/` exists.

Observed size:
- 7 files
- 10,719,507 bytes total

Observed file types:
- `.json` 3
- `.md` 2
- `.txt` 2

The visible subtree is generated audit/report output, not product source code.

## Tracked Data Files
No tracked files were returned by `git ls-files data reports`.

## Untracked Data Files
No untracked `data/` or `reports/` paths were surfaced by `git status --short` because the trees are ignored by `.gitignore`.

## Data Deletion Recommendation
Do not delete `data/` or `reports/` in this phase.
They are local-only ignored trees and may still contain test-referenced runtime state.

Later review candidates:
- ignored generated JSON/MD/TXT outputs in `reports/`
- ignored runtime caches in `data/`
- local SQLite artifacts used only for test/runtime state

## Runtime Entrypoints
Observed runtime entrypoints:
- `main.py`
- `api_server.py`
- `streamlit_app.py`
- `screenshot_intake.py`
- `sharp_client.py`

## Dashboard/UI Surface
Observed UI surface:
- `streamlit_app.py`
- dashboard helpers in `automation_scheduler/`
- Streamlit-only display and review utilities

## Core Math Surface
Observed core math surface:
- `quant_engine.py`
- `risk_engine.py`
- `src/core/math_utils.py`
- `src/core/clv.py`
- `src/core/calibrator.py`
- `src/core/opportunity_scanner.py`
- `src/core/backtester.py`

## Risk Surface
Observed risk surface:
- `risk_engine.py`
- `src/core/calibrator.py`
- `automation_scheduler/drawdown_controls.py`
- `automation_scheduler/exposure_limits.py`
- `automation_scheduler/hard_gate_policy.py`
- `automation_scheduler/budget_gates.py`
- bankroll and risk policy helpers in `automation_scheduler/`

## Provider/API Surface
Observed provider/API surface:
- `betting_providers/`
- `providers/`
- `src/api/*`
- `kalshi_client.py`
- `sharp_client.py`
- `automation_scheduler/data_source_registry.py`
- service adapters in `src/services/`

## Market Schema/Catalog Surface
Observed market schema/catalog surface:
- `automation_scheduler/model_data_field_catalog.py`
- `automation_scheduler/technical_signal_fields.py`
- `src/api/schemas/*`
- `multi_sport_model_registry.py`
- `automation_scheduler/backtest_schema.py`

## Signals/Research Surface
Observed signals/research surface:
- `research/`
- `research_engine/`
- `automation_scheduler/feature_ablation_lab.py`
- `automation_scheduler/line_movement_readiness.py`
- `automation_scheduler/line_movement_import_contract.py`
- `automation_scheduler/line_movement_data_quality_dashboard.py`
- `automation_scheduler/arbitrage/`
- sports and market context modules in `automation_scheduler/`

## Backtest/Data Surface
Observed backtest/data surface:
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_strategy_profiles.py`
- `automation_scheduler/backtest_strategy_bankroll.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/historical_odds_importers.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `src/services/model_backtest_service.py`
- `src/core/backtester.py`

## Storage/History Surface
Observed storage/history surface:
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/clv_tracker.py`
- `automation_scheduler/audit_log.py`
- `automation_scheduler/audit_ledger.py`
- `automation_scheduler/paper_trade_ledger.py`
- `data/`
- `reports/`

## Tests Surface
Observed tests surface:
- `tests/` is the dominant validation tree
- phase tests dominate the repo and document each migration step
- architecture and API tests also cover data source and backtest boundaries

## Phase Artifact Surface
Observed phase artifact surface:
- root-level `PHASE*.md` and `PHASE*.json` files
- these files are audit/history artifacts and should be treated as documentation until a later archive plan exists

## Delete Candidates
Candidates for later deletion only after provenance review:
- `.pytest_cache/`
- `__pycache__/`
- `.venv/`
- `venv/`
- `.aider*`
- ignored runtime caches under `data/`
- generated audit outputs under `reports/`
- stale repo-tree dumps such as `FULL_REPO_TREE_AFTER_PHASE_6.txt`

## Move Candidates
Candidates for later move:
- phase docs to a dedicated `docs/phase-archive/` or equivalent archive tree
- deterministic local fixtures into `tests/fixtures/` when they are required by tests
- generated report snapshots into a formal artifact path instead of ad hoc local directories

## Must-Not-Touch-Yet
Do not touch these yet:
- `streamlit_app.py`
- `main.py`
- `api_server.py`
- `quant_engine.py`
- `risk_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/model_data_field_catalog.py`
- `automation_scheduler/technical_signal_fields.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/zero_dte_fixture_template.py`
- `src/api/*`
- `src/core/backtester.py`
- any `data/` files referenced by tests or runtime configuration

## Final Target Architecture
The final architecture should keep:
- `src/core/` as pure math
- provider adapters as normalization layers only
- `src/signals/` as the market-signal research layer
- `src/backtester/` as the historical simulation engine
- `streamlit_app.py` as the operator dashboard
- `main.py` as the backend/API entrypoint if present

## Pre-Backtest Cleanup Gates
The repo should not start controlled data-loader or backtest-runner work until:
- local data provenance is reviewed
- generated artifacts are classified
- runtime entrypoints are explicit
- README and `.gitignore` contract the repo boundaries
- stale phase/documentation artifacts are inventory-mapped

## Next Phase Recommendation
Proceed to 10K8ZF5 Runtime Entrypoint + Ownership Map.

## Required Audit Strings
- 10K8ZF4
- Asset-Grade Repo Clean Inventory
- senior-systems-engineer quality
- README.md
- .gitignore
- Local /data is not product source code
- Do not commit local data dumps
- Only tiny deterministic fixtures belong in tests/fixtures/
- Terminal 1 is Backend / FastAPI Engine
- Terminal 2 is Streamlit Operator Dashboard
- Do not merge FastAPI and Streamlit into one file
- streamlit_app.py is the dashboard entrypoint
- main.py is the backend/API entrypoint if present
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing
- pre-backtest cleanup must finish before controlled data loader or backtest runner
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF4
