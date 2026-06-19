# Unified Quantitative Market Research & Backtesting Engine

## Product Scope
This repository is a research/backtest mode only codebase for markets, sports, and prediction workflows.
The canonical workflow is:

Data
-> Validation
-> Strategy Research
-> Backtest
-> Results / Metrics
-> Later: Live Model Testing

## Canonical Workflow
The public product surface should follow the canonical research/backtest workflow.
There is no separate fake, paper, or testing-room product architecture.

## Architecture Boundaries
- `src/core/` is pure math only: no API calls, no Streamlit imports, no database writes.
- `providers/` and provider adapters normalize external vendor data and do not own EV/Kelly/risk policy.
- `src/signals/` should own ORB, footprint, RLM, whale flow, and other market signals without UI rendering or broker execution.
- `src/backtester/` is the future historical simulation engine for fills, slippage, costs, experiment matrices, and results.
- `streamlit_app.py` is the dashboard entrypoint.
- `main.py` is the backend/API entrypoint if present.
- Do not merge FastAPI and Streamlit into one file.
- `quant_engine.py` remains the current canonical owner for EV/edge/fair odds/implied probability where applicable until migrated.
- `risk_engine.py` remains the current canonical owner for staking/risk/bankroll policy until migrated.
- `automation_scheduler/` is the current legacy orchestration, catalog, and dashboard-data area and is a migration target for future cleanup.

## Two-Terminal Local Development
Use two terminals during local development.

### Terminal 1: Backend / FastAPI Engine
Run the FastAPI service and API routes here.

### Terminal 2: Streamlit Operator Dashboard
Run the dashboard and operator readouts here.

## Data Handling Warning
Local /data is not product source code.
Do not commit local data dumps.
Do not commit raw JSON dumps.
Do not commit .env files.
Do not commit __pycache__.
Only tiny deterministic fixtures belong in tests/fixtures/.

## Local /data Policy
The `data/` tree is for local runtime state, generated outputs, and ignored artifacts.
It is not a source-of-truth package layer.

## What Must Never Be Committed
- Local data dumps
- Raw JSON dumps
- `.env` files
- Python caches such as `__pycache__`
- Large generated artifacts

## Current Safety Guardrails
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language

## Repository Cleanup Status
The repo has been inventoried for asset-grade cleanup.
`data/` and `reports/` are local-only ignored trees and must be reviewed before any controlled backtest/data-loader work starts.

## Pre-Backtest Cleanup Requirement
Pre-backtest cleanup must finish before controlled data loader or backtest runner.

## Final Target Architecture
The final architecture keeps:
- `src/core/` for pure math
- provider adapters for external data normalization
- `src/signals/` for market research features
- `src/backtester/` for historical simulation
- `streamlit_app.py` for operator display
- `main.py` for backend/API service entrypoints if present

## Notes
- research/backtest mode only
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing
- Terminal 1
- Backend / FastAPI Engine
- Terminal 2
- Streamlit Operator Dashboard
- Do not merge FastAPI and Streamlit into one file.
- streamlit_app.py is the dashboard entrypoint.
- main.py is the backend/API entrypoint if present.
- Local /data is not product source code.
- Do not commit local data dumps.
- Do not commit raw JSON dumps.
- Do not commit .env files.
- Do not commit __pycache__.
- Only tiny deterministic fixtures belong in tests/fixtures/.
- no broker execution
- no real trade execution
- no live connectors
- no API calls without explicit provider phase
- no database writes without explicit storage phase
- no guaranteed profit language
- no assured profit language
- pre-backtest cleanup must finish before controlled data loader or backtest runner
