# Project Status

Canonical live status for the repository and the required starting document for every human, Codex, ChatGPT, or future AI session.

- repository homepage: `docs/PROJECT_STATUS.md`
- required starting document: `docs/PROJECT_STATUS.md`
- current branch: `feature/nfl-backtesting`
- current HEAD: live branch tip (exact hash is reported in the task final report)
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 4.9A - NFL Schedule Research Asset Population`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation + event-centric historical research database + master research engine specification + universal feature registry + universal math engine contracts + research asset runtime framework + historical dataset acquisition framework + historical dataset acquisition runtime + research asset source discovery and connector mapping framework + historical research asset certification runtime + NFL schedule research asset population`
- completed phases:
  - `Phase 4.3.6 - Profile-Aware NFL P0 Validation`
  - `Phase 4.3.7 - Minimum Backtest Row Contract`
  - `Phase 4.4 - Event-Centric Historical Data Acquisition`
  - `Phase 4.5A - Master Research Engine Specification`
  - `Phase 4.5B - Universal Feature Registry`
  - `Phase 4.5C - Universal Math Engine Contracts`
  - `Phase 4.5D - Research Asset Runtime Framework`
  - `Phase 4.5E - Canonical Engineering Specification Rename & Research Asset Runtime Framework`
  - `Phase 4.7B - Historical Dataset Acquisition Runtime`
  - `Phase 4.7C - Historical Research Asset Certification Runtime`
  - `Phase 4.8 - Research Asset Lifecycle Runtime & Time & Entity Alignment Certification`
- current phase objective: Populate the first minimum-schema NFL research asset (schedule) through the shared acquisition cache, integrity validation, normalization, research asset certification, dataset certification, and lifecycle runtime while preserving queryability for future event-centric joins and Worldview evidence packages.
- next phase: `Phase 4.9B - NFL Results Research Asset Population`
- current blockers: None
- latest validation status:
  - Phase 4.7C runtime validation passed: compileall, certification runtime tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.8 lifecycle runtime code changes are complete and validated: compileall, focused lifecycle tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.9A schedule research asset population code changes are complete and validated: compileall, focused schedule runtime tests, smoke, architecture, document lifecycle, and ops checks are green.
- latest full gate result: `not run; broader regression gate deferred for this runtime-and-contract phase`
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
- Research assets are certified individually before dataset certification completes.
- Dataset certification is gated on the required research assets passing first.
- Research assets advance through one canonical lifecycle and must satisfy time/entity alignment before lifecycle promotion.
- Events own shared context.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later and are not the storage primitive.
- Backtests never read directly from providers.
- The master research engine specification is the next governing layer above the market-profile framework.

## Required Supporting Docs

Read these only when you need more detail than the project status page provides:

- `docs/MASTER_ROADMAP.md`
- `docs/NEXT_ACTION.md`
- `docs/MASTER_DOCUMENT_INDEX.md`
- `docs/STATUS_UPDATE_POLICY.md`
- `docs/DOCUMENT_RETENTION_INDEX.md`
- `docs/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
- `docs/architecture/UNIVERSAL_FEATURE_REGISTRY.md`
- `docs/architecture/UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`
- `docs/architecture/RESEARCH_ASSET_RUNTIME_FRAMEWORK.md`
- `docs/architecture/HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md`
- `docs/architecture/NFL_SCHEDULE_RESEARCH_ASSET.md`
- `docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md`
- `docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md`
- `docs/contracts/RESEARCH_ASSET_CONTRACT.md`
- `docs/contracts/DATASET_REGISTRY.md`
- `docs/contracts/DATA_LINEAGE_CONTRACT.md`
- `docs/architecture/RESEARCH_ASSET_LIFECYCLE_RUNTIME.md`
- `docs/reports/PHASE4_5B_UNIVERSAL_FEATURE_REGISTRY.md`
- `docs/reports/PHASE4_5C_UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`
- `docs/reports/PHASE4_5D_RESEARCH_ASSET_RUNTIME_FRAMEWORK.md`
- `docs/reports/PHASE4_6_MINIMUM_CERTIFIED_HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md`
- `docs/reports/PHASE4_7B_HISTORICAL_DATASET_ACQUISITION_RUNTIME.md`
- `docs/reports/PHASE4_7C_HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md`
- `docs/reports/PHASE4_7A_RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md`
- `docs/reports/PHASE4_8_RESEARCH_ASSET_LIFECYCLE_RUNTIME_AND_TIME_ENTITY_ALIGNMENT_CERTIFICATION.md`
- `docs/reports/PHASE4_9A_NFL_SCHEDULE_RESEARCH_ASSET_POPULATION.md`
- `docs/contracts/MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_MINIMUM_BACKTEST_ROW_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/reports/PHASE4_5A_MASTER_RESEARCH_ENGINE_SPECIFICATION.md`
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

`Phase 4.9B - NFL Results Research Asset Population`
