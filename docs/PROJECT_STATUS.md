# Project Status

Canonical live status for the repository and the required starting document for every human, Codex, ChatGPT, or future AI session.

- repository homepage: `docs/PROJECT_STATUS.md`
- required starting document: `docs/PROJECT_STATUS.md`
- current branch: `feature/nfl-backtesting`
- current HEAD: live branch tip (exact hash is reported in the task final report)
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 4.4 — Event-Centric Historical Data Acquisition`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation + event-centric historical research database`
- completed phases:
  - `Phase 4.3.6 — Profile-Aware NFL P0 Validation`
  - `Phase 4.3.7 — Minimum Backtest Row Contract`
- current phase objective: Build the permanent event-centric historical research database that stores certified NFL events, markets, selections, and acquisition bundles before decision rows are generated.
- next phase: `Phase 4.5 — Historical Feature Population`
- current blockers: None
- latest validation status:
  - `python -m compileall src tests scripts` passed on the current commit
  - `pytest -m smoke -q` passed on the current commit
  - `python scripts/check_repo_preflight.py --end-task --include-ops` passed on the current commit
  - `python scripts/ops_check.py --mode local --output text --skip-network` passed on the current commit
  - Phase 4.4 event-centric historical acquisition changes are validated on the current commit
- latest full gate result: `3753 passed, 670 skipped, 519 subtests passed`
- latest pushed commit: live branch tip (exact hash is reported in the task final report)

## Active Canonical Rules

- Runtime/application code belongs under `src/`.
- Documentation belongs under `docs/`.
- Tests belong under `tests/`.
- Scripts belong under `scripts/`.
- The repository root should remain minimal; only approved entry files belong there.
- Reuse canonical owners before introducing new modules.
- Historical datasets are permanent repository assets.
- Providers are acquisition mechanisms only.
- The repository owns certified datasets after acquisition and certification.
- Events own shared context.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later and are not the storage primitive.
- Backtests never read directly from providers.

## Required Supporting Docs

Read these only when you need more detail than the project status page provides:

- `docs/MASTER_ROADMAP.md`
- `docs/NEXT_ACTION.md`
- `docs/MASTER_DOCUMENT_INDEX.md`
- `docs/STATUS_UPDATE_POLICY.md`
- `docs/DOCUMENT_RETENTION_INDEX.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/reports/PHASE4_4_EVENT_CENTRIC_HISTORICAL_ACQUISITION.md`
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

`Phase 4.5 — Historical Feature Population`
