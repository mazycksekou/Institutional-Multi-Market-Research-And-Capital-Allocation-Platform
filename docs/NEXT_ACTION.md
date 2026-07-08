# Next Action

## Next Phase

`Phase 4.5C - Universal Math Engine Contracts`

## Objective

Define the canonical math engine contracts on top of the universal feature registry so every future calculation path has one owner, lifecycle state, and reuse path.

## Allowed Actions

- Reuse the canonical market profile framework, market-input specification, storage, validation, and lineage owners.
- Extend the universal math engine contracts instead of creating market-specific math engines.
- Keep the math-contract architecture reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not build decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- Universal math engine contract plan built from the universal feature registry.
- Feature lifecycle mappings for inputs, features, signals, targets, confidence metrics, and validation metrics.
- Readiness, lineage, validation, and engine-owner updates for the math-contract layer.
- Updated project status and index entries.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`

## Commit Policy

- Commit only when the phase deliverables are documented and validation passes.
- Keep runtime changes out of scope unless a shared canonical contract must be clarified.
- Push to `origin/feature/nfl-backtesting` after the commit is clean and validated.
