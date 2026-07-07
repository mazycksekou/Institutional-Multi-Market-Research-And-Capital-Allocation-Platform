# Next Action

## Next Phase

`Phase 4.5 — Historical Feature Population`

## Objective

Populate certified historical events, markets, selections, and event context with the first reusable feature snapshots.

## Allowed Actions

- Reuse the canonical event-centric historical database, storage, validation, and lineage owners.
- Populate feature snapshots only from certified historical events and their markets / selections.
- Extend the shared readiness and lineage reporting for historical feature population.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not build decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- Historical feature population plan for the certified event database.
- Feature snapshot mappings for event-owned context and market-owned selections.
- Readiness, lineage, and validation updates for historical feature population.
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
