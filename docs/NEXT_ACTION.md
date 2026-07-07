# Next Action

## Next Phase

`Phase 4.3.7 — Minimum Backtest Row Contract`

## Objective

Define exactly when an event row becomes backtest-ready.

## Allowed Actions

- Update or create documentation for the minimum decision-row readiness contract.
- Reuse existing canonical contracts, storage, validation, and lineage owners.
- Add lightweight tests that prove the contract is understood by the repository.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest data.
- Do not implement providers.
- Do not build features.
- Do not backtest.
- Do not build models.
- Do not change runtime behavior unless required to clarify the contract.

## Expected Deliverables

- Minimum backtest row contract documentation.
- Decision-row readiness rules.
- Point-in-time safety criteria for a backtest-ready event row.
- Validation guidance for row acceptance.
- Updated project status and index entries.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python scripts/check_architecture.py --output text`

## Commit Policy

- Commit only when the phase deliverables are documented and validation passes.
- Keep runtime changes out of scope unless a shared canonical contract must be clarified.
- Push to `origin/feature/nfl-backtesting` after the commit is clean and validated.

