# Next Action

## Next Phase

`Phase 4.9C - First Production Connector (NFL Schedule)`

## Objective

Implement the first production connector path for the certified NFL schedule research asset.
Keep the minimum certified schema first, preserve the same shared runtime path used by the schedule asset, and replace the deterministic fixture-backed readiness path with the canonical open-provider acquisition path without introducing provider-driven ownership.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same schedule-population path into the first production connector without building a parallel NFL-specific pipeline.
- Keep the minimum-certified-schema path reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement connectors beyond the shared runtime contracts.
- Do not implement mathematical engines yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- First production connector implementation for the NFL schedule research asset.
- Identity, lifecycle, alignment, lineage, validation, certification, and readiness mappings for the minimum certified schema schedule connector path.
- Lifecycle path updates for the research-asset layer and planner-driven acquisition selection.
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
