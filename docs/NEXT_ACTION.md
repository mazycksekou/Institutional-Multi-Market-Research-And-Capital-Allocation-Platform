# Next Action

## Next Phase

`Phase 4.9D - NFL Results Research Asset Population`

## Objective

Populate the NFL results research asset using the same canonical runtime path introduced by the first production connector in Phase 4.9C. Keep the minimum certified schema first, preserve the same shared runtime path used by the schedule asset, and extend the event-centric research-asset pipeline without introducing provider-driven ownership. Preserve the canonical open-provider acquisition path shape for later live use.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same shared runtime path that powered the first production connector without building a parallel NFL-specific pipeline.
- Keep the minimum-certified-schema path reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not implement mathematical engines yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- NFL results research asset population implementation.
- Identity, lifecycle, alignment, lineage, validation, certification, and readiness mappings for the minimum certified schema results asset path.
- Lifecycle path updates for the research-asset layer and planner-driven acquisition selection, preserving the first production connector architecture introduced in Phase 4.9C.
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
