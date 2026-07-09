# Next Action

## Next Phase

`Phase 4.9B - NFL Results Research Asset Population`

## Objective

Populate the next minimum-schema NFL research asset: game results.
Keep the minimum certified schema first and preserve the same shared runtime path used by the schedule asset.
Reuse the same local-first acquisition, raw cache, integrity validation, normalization, research asset certification, dataset certification, lifecycle, and dashboard readiness owners that the schedule phase used.
This work follows Time & Entity Alignment Certification and time/entity alignment certification, and extends the same certified lifecycle path rather than creating a new one.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same schedule-population path into the NFL results asset instead of building a parallel NFL-specific pipeline.
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

- NFL results research asset population plan built on top of the shared research asset runtime framework.
- Identity, lifecycle, alignment, lineage, validation, certification, and readiness mappings for the minimum certified schema results asset.
- Lifecycle path updates for the research-asset layer.
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
