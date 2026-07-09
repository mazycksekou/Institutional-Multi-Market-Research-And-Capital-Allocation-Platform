# Next Action

## Next Phase

`Phase 4.9E - NFL Odds Research Asset Population`

## Previous Phase

`Phase 4.9D - NFL Results Research Asset Population` completed the certified results asset and schedule join gate.

## Objective

Populate the minimum-schema NFL odds research asset and join every odds snapshot to the certified schedule and results backbone. Keep the minimum certified schema first. Reuse the first production connector architecture and preserve the canonical open-provider acquisition path for later live use. Preserve decision-time correctness, line/price timestamps, raw payload evidence, field-level provenance, and local certification. Do not treat closing odds as information available before the decision timestamp.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, acquisition runtime, certification runtime, and lifecycle runtime owners.
- Extend the same shared connector, raw-cache, certification, lifecycle, coverage, and readiness path without building a parallel NFL-specific pipeline.
- Define spread, moneyline, and total snapshots only where the minimum schema can be certified deterministically.
- Preserve bookmaker, market, selection, line, price, snapshot time, provider role, and source lineage.
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

- NFL odds research asset population implementation.
- Decision-time-safe identity, lineage, validation, certification, and readiness mappings for spread, moneyline, and total snapshots.
- Schedule/results join validation and a negative proof that post-decision or orphaned odds cannot certify.
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
