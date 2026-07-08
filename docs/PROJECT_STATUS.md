# Project Status

Canonical live status for the repository and the required starting document for every human, Codex, ChatGPT, or future AI session.

- repository homepage: `docs/PROJECT_STATUS.md`
- required starting document: `docs/PROJECT_STATUS.md`
- current branch: `feature/nfl-backtesting`
- current HEAD: live branch tip (exact hash is reported in the task final report)
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 4.5A - Master Market Input Specification`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation + event-centric historical research database + master market input specification`
- completed phases:
  - `Phase 4.3.6 - Profile-Aware NFL P0 Validation`
  - `Phase 4.3.7 - Minimum Backtest Row Contract`
  - `Phase 4.4 - Event-Centric Historical Data Acquisition`
- current phase objective: Build the repository's master market input specification so every future input, feature, signal, target, confidence metric, validation metric, connector, and engine traces back to one canonical owner before new implementation phases begin.
- next phase: `Phase 4.5B - Universal Feature Registry`
- current blockers: None
- latest validation status:
  - `python -m compileall src tests scripts` passed on the current commit
  - `pytest tests/test_master_market_input_specification_docs.py -q` passed on the current commit
  - `pytest tests/test_project_status_governance.py -q` passed on the current commit
  - `pytest tests/test_minimum_backtest_row_contract_docs.py -q` passed on the current commit
  - `pytest -m smoke -q` passed on the current commit
  - `python scripts/check_architecture.py --output text` passed on the current commit
  - `python scripts/check_document_lifecycle.py --output text` passed on the current commit
  - `python scripts/ops_check.py --mode local --output text --skip-network` passed with repo-preflight blocked only by the uncommitted docs/test changes
- latest full gate result: `not run for this docs-only phase`
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
- The master market input specification is the next governing layer above the market-profile framework.

## Required Supporting Docs

Read these only when you need more detail than the project status page provides:

- `docs/MASTER_ROADMAP.md`
- `docs/NEXT_ACTION.md`
- `docs/MASTER_DOCUMENT_INDEX.md`
- `docs/STATUS_UPDATE_POLICY.md`
- `docs/DOCUMENT_RETENTION_INDEX.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/MASTER_MARKET_INPUT_SPECIFICATION.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/reports/PHASE4_5A_MASTER_MARKET_INPUT_SPECIFICATION.md`
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

`Phase 4.5B - Universal Feature Registry`
