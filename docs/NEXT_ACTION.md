# Next Action

## Next Phase

`Phase 4.6 - Historical Dataset Acquisition (minimum certified schema first)`

## Objective

Acquire the minimum certified historical schema as a repository-owned asset first, then certify it so future datasets can mature without introducing parallel ownership.

## Allowed Actions

- Reuse the canonical market profile framework, research engine specification, storage, validation, lineage, and research asset runtime framework owners.
- Extend the historical dataset acquisition layer on top of the research asset runtime framework instead of creating market-specific pipelines.
- Keep the minimum-certified-schema path reusable for sports, prediction markets, and options / 0DTE.
- Update the project status and document indexes when this phase completes.

## Forbidden Actions

- Do not ingest paid or live data.
- Do not populate features yet.
- Do not implement mathematical engines yet.
- Do not generate decision rows yet.
- Do not backtest.
- Do not build models.
- Do not add provider-specific runtime ownership.

## Expected Deliverables

- Minimum certified schema acquisition plan built on top of the research asset runtime framework.
- Dataset, lineage, validation, and readiness mappings for the minimum certified schema.
- Historical acquisition and certification path updates for the research-asset layer.
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
