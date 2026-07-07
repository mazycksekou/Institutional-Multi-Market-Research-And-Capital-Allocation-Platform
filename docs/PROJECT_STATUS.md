# Project Status

Canonical live status for the repository.

- current branch: `feature/nfl-backtesting`
- current HEAD: `530ab2e149a3c171da7dee4ad06a1a72f8528b4a`
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 4.3.7 — Minimum Backtest Row Contract`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation`
- completed phases:
  - `Phase 4.3.6 — Profile-Aware NFL P0 Validation`
- current phase objective: Define exactly when an event row becomes backtest-ready.
- next phase: `Phase 4.3.7 — Minimum Backtest Row Contract`
- current blockers: None
- latest validation status:
  - `python -m compileall src tests scripts` passed
  - `pytest -m smoke -q` passed
  - `python scripts/ops_check.py --mode local --output text --skip-network` passed
  - `python scripts/check_architecture.py --output text` passed
- latest full gate result: `3753 passed, 670 skipped, 519 subtests passed`
- latest pushed commit: `530ab2e149a3c171da7dee4ad06a1a72f8528b4a`

## Active Canonical Rules

- Runtime/application code belongs under `src/`.
- Documentation belongs under `docs/`.
- Tests belong under `tests/`.
- Scripts belong under `scripts/`.
- The repository root should remain minimal; only approved entry files belong there.
- Reuse canonical owners before introducing new modules.
- Do not move to provider ingestion until the minimum decision-row readiness contract exists.

## Current Docs To Read First

- `docs/MASTER_ROADMAP.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/PRODUCTION_READINESS.md`
- `docs/architecture/REPOSITORY_INDEPENDENCE_SCORECARD.md`
- `docs/architecture/MARKET_PROFILE_FRAMEWORK.md`
- `docs/architecture/NFL_P0_DATA_FOUNDATION.md`
- `docs/NEXT_ACTION.md`
- `docs/STATUS_UPDATE_POLICY.md`

## Next Recommended Codex Task

`Phase 4.3.7 — Minimum Backtest Row Contract`
