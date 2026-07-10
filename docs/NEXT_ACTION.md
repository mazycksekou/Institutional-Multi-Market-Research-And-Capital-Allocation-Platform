# Next Action

## Next Phase

`Phase 4.9F - NFL Weather Research Asset Population`

## Previous Phase

`Phase 4.9E - NFL Odds Research Asset Population` completed the certified odds asset and schedule/results join gate.

## Objective

Populate the minimum-schema NFL weather research asset and join every weather snapshot to the certified schedule, results, and odds backbone. Keep the minimum certified schema first. Reuse the canonical connector, raw-cache, validation, certification, lifecycle, coverage, and readiness owners without creating parallel infrastructure. Preserve forecast-time correctness, snapshot timestamps, raw payload evidence, field-level provenance, and local certification. Do not confuse actual weather observations with pregame forecast evidence.
Preserve the canonical open-provider acquisition path and the minimum-certified-schema path so the weather phase remains reusable for future markets.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same shared connector, raw-cache, certification, lifecycle, coverage, and readiness path without building a parallel NFL-specific pipeline.
- Define forecast snapshots only where the minimum schema can be certified deterministically.
- Preserve location, forecast time, temperature, wind, precipitation, snapshot time, provider role, and source lineage.
- Keep the minimum-certified-schema path reusable for sports, prediction markets, and options / 0DTE.
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

- NFL weather research asset population implementation.
- Forecast-time-safe identity, lineage, validation, certification, and readiness mappings for weather snapshots.
- Schedule/results/odds join validation and a negative proof that post-decision or orphaned weather cannot certify.
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
