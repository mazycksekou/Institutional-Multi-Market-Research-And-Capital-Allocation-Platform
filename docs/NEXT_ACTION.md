# Next Action

## Next Phase

`Phase 4.9H - NFL Team Statistics Research Asset Population`

## Previous Phase

`Phase 4.9G - NFL Injuries Research Asset Population` completed the certified report-time-safe injuries asset and its schedule/results/odds/weather join gate.

## Objective

Populate the minimum-slice NFL team statistics research asset and join each team snapshot to the certified schedule, results, odds, weather, and injuries backbone where applicable. Reuse the canonical connector mapping, raw-cache, validation, certification, lifecycle, coverage, and readiness owners without creating parallel infrastructure. Preserve point-in-time correctness, team identity, raw payload evidence, field-level provenance, and local certification. Do not treat same-event or postgame team statistics as predecision evidence for the event being evaluated.
Preserve the canonical open-provider acquisition path where available so the team-statistics phase remains reusable for future markets.
Apply the minimum certified schema first rule: only fields required by the minimum certified schema may block this phase, while broader future team metrics remain deferred.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same shared acquisition, raw-cache, certification, lifecycle, coverage, and readiness path without building a parallel NFL-specific pipeline.
- Define point-in-time-safe team statistics snapshots only where the minimum slice can be certified deterministically.
- Preserve team identity, prior-game or frozen snapshot timing, efficiency context, source lineage, and local evidence packaging.
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

- NFL team statistics research asset population implementation.
- Point-in-time-safe identity, lineage, validation, certification, and readiness mappings for team-statistics snapshots.
- Schedule/results/odds/weather/injuries join validation and a negative proof that same-event or postgame team statistics cannot certify.
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
