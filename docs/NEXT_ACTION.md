# Next Action

## Next Phase

`Phase 4.4 — NFL Open Data Integration`

## Objective

Integrate the first free / open NFL data source against the minimum backtest row contract.

## Allowed Actions

- Reuse existing canonical contracts, storage, validation, and lineage owners.
- Integrate the first open-data provider against the canonical minimum backtest row contract.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not build features beyond the contract.
- Do not backtest.
- Do not build models.
- Do not change runtime behavior unless required to clarify the integration contract.

## Expected Deliverables

- Open-data provider mapping for NFL.
- Minimum backtest row contract implementation references.
- Storage, validation, and readiness updates for the first open-data lane.
- Updated project status and index entries.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest tests/test_minimum_backtest_row_contract_docs.py -q`
- `pytest tests/test_project_status_governance.py -q`
- `pytest -m smoke -q`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`

## Commit Policy

- Commit only when the phase deliverables are documented and validation passes.
- Keep runtime changes out of scope unless a shared canonical contract must be clarified.
- Push to `origin/feature/nfl-backtesting` after the commit is clean and validated.
