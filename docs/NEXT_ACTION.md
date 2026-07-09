# Next Action

## Next Phase

`Phase 4.8 - Research Asset Lifecycle Runtime & Time & Entity Alignment Certification`

## Objective

Implement canonical research asset lifecycle management, immutable research asset identity, and time/entity alignment certification without introducing parallel ownership. This remains a minimum certified schema first phase.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, source discovery, connector mapping, acquisition runtime, research asset runtime framework, research asset certification runtime, and lifecycle runtime owners.
- Extend the lifecycle layer on top of certified research assets instead of creating market-specific pipelines.
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

- Minimum research asset lifecycle and alignment certification plan built on top of the research asset runtime framework.
- Identity, lifecycle, alignment, lineage, validation, certification, and readiness mappings for the minimum certified schema.
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
