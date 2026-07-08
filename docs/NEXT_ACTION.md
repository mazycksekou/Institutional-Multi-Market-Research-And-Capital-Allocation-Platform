# Next Action

## Next Phase

`Phase 4.5D - Research Asset Population Framework`

## Objective

Define the governed research-asset population framework that will mature certified datasets, features, mathematical engines, connectors, and evidence without introducing parallel ownership.

## Allowed Actions

- Reuse the canonical market profile framework, market-input specification, storage, validation, and lineage owners.
- Extend the research-asset population framework on top of the universal math engine contracts instead of creating market-specific pipelines.
- Keep the research-asset architecture reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not build decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- Research asset maturity plan built on top of the universal math engine contracts.
- Feature, dataset, engine, and evidence lifecycle mappings.
- Readiness, lineage, validation, and population-path updates for the research-asset layer.
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
