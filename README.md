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

## Universal Ownership Rule
There must be one canonical owner per concept.
Do not create parallel implementations of math, metrics, signals, providers, backtesting, storage, or dashboard-data logic.
automation_scheduler/ and live_market_intelligence/ are migration sources until mapped into canonical owners.
Do not delete legacy code until duplicate status is proven and tests protect the canonical replacement.

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

## R2 Object Storage Archive Policy
R2 object storage is the archive layer for large local market data bundles.
R2 is not the live application database.
Do not upload thousands of tiny JSON files.
Aggregate raw JSON into daily archive bundles before upload.
Use one object per date/source/market bundle.
Keep a manifest for every archive bundle.
Verify upload before local deletion.
Local deletion is off by default.
Credentials must come from environment variables or ignored local config only.
Do not commit R2 access keys, secret keys, tokens, endpoints, bucket names if sensitive, or local credential files.
Do not paste real R2 credentials into source code, README examples, tests, or committed config.
Core math, risk, signals, metrics, backtester, and dashboard code must not import R2 clients directly.
Future R2 adapter code belongs behind src/storage/ or a storage-provider boundary.
End-of-day archive scripts belong in scripts/.
Only tiny deterministic fixtures belong in tests/fixtures/.

Example environment variables with placeholder values only:
- `R2_ACCOUNT_ID=example-account-id`
- `R2_ACCESS_KEY_ID=example-access-key-id`
- `R2_SECRET_ACCESS_KEY=example-secret-access-key`
- `R2_BUCKET_NAME=example-bucket-name`
- `R2_ENDPOINT_URL=https://example.invalid/r2`

The real values belong only in local environment variables or ignored local config.
The real R2 key is first used in 10K8ZF8/10K8ZF9, not 10K8ZF6.
10K8ZF6 performs no upload.

### R2 Archive Pipeline
10K8ZF7 R2 Archive Pipeline
scripts/r2_archive_pipeline.py
dry-run mode writes nothing
bundle mode writes local jsonl.gz archive and manifest
upload mode requires R2 environment variables
verify mode checks the remote object before cleanup eligibility
cleanup-plan mode marks eligibility only
cleanup mode is explicit and gated
no cleanup runs by default
verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed
the intended end state is R2 transfer verified and eligible local raw/generated data removed from local storage
credentials must remain in local environment variables or ignored local config

Example dry-run command:
```powershell
python scripts/r2_archive_pipeline.py --input-dir data --output-dir . --environment local --source example-source --market example-market --trading-date 2026-01-31 --dry-run
```

Example bundle command:
```powershell
python scripts/r2_archive_pipeline.py --input-dir data --output-dir . --environment local --source example-source --market example-market --trading-date 2026-01-31 --bundle
```

Example upload and verify command with placeholders only:
```powershell
python scripts/r2_archive_pipeline.py --input-dir data --output-dir . --environment local --source example-source --market example-market --trading-date 2026-01-31 --bundle --upload --verify
```

Example verified cleanup command with placeholders only:
```powershell
python scripts/r2_archive_pipeline.py --input-dir data --output-dir . --manifest-path reports/archive_manifests/example-manifest.json --cleanup --allow-delete-local-raw
```

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

## Documentation Governance
`README.md` is the only Markdown file permitted at repository root.
All other documentation must live under `docs/`; see `docs/architecture/DOCUMENTATION_GOVERNANCE.md`.

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
