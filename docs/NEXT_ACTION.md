# Next Action

## Next Phase

`Phase 4.5B - Universal Feature Registry`

## Objective

Turn the master market input specification into the universal feature registry so every future feature family has one canonical owner, lifecycle state, and reuse path.

## Allowed Actions

- Reuse the canonical market profile framework, market-input specification, storage, validation, and lineage owners.
- Extend the universal feature registry instead of creating market-specific registries.
- Keep the registry architecture reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not build decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- Universal feature registry plan built from the master market input specification.
- Feature lifecycle mappings for market inputs, signals, targets, confidence metrics, and validation metrics.
- Readiness, lineage, and validation updates for the feature registry layer.
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
