# Project Status

Canonical live status for the repository and the required starting document for every human, Codex, ChatGPT, or future AI session.

- repository homepage: `docs/PROJECT_STATUS.md`
- required starting document: `docs/PROJECT_STATUS.md`
- current branch: `feature/nfl-backtesting`
- current HEAD: live branch tip (exact hash is reported in the task final report)
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 4.4 — NFL Open Data Integration`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation`
- completed phases:
  - `Phase 4.3.6 — Profile-Aware NFL P0 Validation`
  - `Phase 4.3.7 — Minimum Backtest Row Contract`
- current phase objective: Integrate the first free / open NFL data source against the minimum backtest row contract.
- next phase: `Phase 4.4 — NFL Open Data Integration`
- current blockers: None
- latest validation status:
  - `python -m compileall src tests scripts` passed
  - `pytest tests/test_minimum_backtest_row_contract_docs.py -q` passed
  - `pytest tests/test_project_status_governance.py -q` passed
  - `pytest -m smoke -q` passed
  - `python scripts/check_architecture.py --output text` passed
  - `python scripts/check_document_lifecycle.py --output text` passed
  - `python scripts/ops_check.py --mode local --output text --skip-network` passed
- latest full gate result: `3753 passed, 670 skipped, 519 subtests passed`
- latest pushed commit: live branch tip (exact hash is reported in the task final report)

## Active Canonical Rules

- Runtime/application code belongs under `src/`.
- Documentation belongs under `docs/`.
- Tests belong under `tests/`.
- Scripts belong under `scripts/`.
- The repository root should remain minimal; only approved entry files belong there.
- Reuse canonical owners before introducing new modules.
- Do not move to provider ingestion until the minimum decision-row readiness contract exists.

## Required Supporting Docs

Read these only when you need more detail than the project status page provides:

- `docs/MASTER_ROADMAP.md`
- `docs/NEXT_ACTION.md`
- `docs/MASTER_DOCUMENT_INDEX.md`
- `docs/STATUS_UPDATE_POLICY.md`
- `docs/DOCUMENT_RETENTION_INDEX.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/reports/NFL_BACKTEST_ROW_READINESS_CHECKLIST.md`
- `docs/reports/NFL_DECISION_TIME_ALIGNMENT_RULES.md`
- `docs/reports/NFL_BACKTEST_ROW_EXCLUSION_RULES.md`
- `docs/reports/NFL_STREAMLIT_BACKTEST_READINESS_SPEC.md`
- `docs/reports/NFL_WORLDVIEW_BACKTEST_READINESS_SPEC.md`
- `docs/reports/NFL_BACKTEST_PASS_FAIL_CRITERIA.md`
- `docs/architecture/PRODUCTION_READINESS.md`
- `docs/architecture/REPOSITORY_INDEPENDENCE_SCORECARD.md`
- `docs/architecture/MARKET_PROFILE_FRAMEWORK.md`
- `docs/architecture/NFL_P0_DATA_FOUNDATION.md`

## Next Recommended Codex Task

`Phase 4.4 — NFL Open Data Integration`
