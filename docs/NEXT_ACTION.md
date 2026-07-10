# Next Action

## Next Phase

`Phase 4.9G - NFL Injuries Research Asset Population`

## Previous Phase

`Phase 4.9F - NFL Weather Research Asset Population` completed the certified forecast-only weather asset and its schedule/results/odds join gate.

## Objective

Populate the minimum-slice NFL injuries research asset and join each injury status snapshot to the certified schedule, results, odds, and weather backbone where applicable. Reuse the canonical connector mapping, raw-cache, validation, certification, lifecycle, coverage, and readiness owners without creating parallel infrastructure. Preserve report-time correctness, team/player identity, raw payload evidence, field-level provenance, and local certification. Do not treat post-decision availability updates or retrospective corrections as predecision evidence.
Preserve the canonical open-provider acquisition path where available, plus the documented manual injury evidence path, so the injury phase remains reusable for future markets.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same shared acquisition, raw-cache, certification, lifecycle, coverage, and readiness path without building a parallel NFL-specific pipeline.
- Define report-time-safe injury snapshots only where the minimum slice can be certified deterministically.
- Preserve player, team, injury status, report time, source lineage, and local evidence packaging.
- Keep the reusable path compatible with sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not implement connectors.
- Do not make uncontrolled network calls or require secrets in tests.
- Do not implement mathematical engines yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- NFL injuries research asset population implementation.
- Report-time-safe identity, lineage, validation, certification, and readiness mappings for injury snapshots.
- Schedule/results/odds/weather join validation and a negative proof that post-decision or orphaned injuries cannot certify.
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
