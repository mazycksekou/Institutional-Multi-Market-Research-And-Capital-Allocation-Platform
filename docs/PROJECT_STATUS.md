# Project Status

Canonical live status for the repository and the required starting document for every human, Codex, ChatGPT, or future AI session.

- repository homepage: `docs/PROJECT_STATUS.md`
- required starting document: `docs/PROJECT_STATUS.md`
- current branch: `feature/nfl-backtesting`
- current HEAD: live branch tip (exact hash is reported in the task final report)
- remote tracking branch: `origin/feature/nfl-backtesting`
- active phase: `Phase 5.2 - Reusable Mathematical Engines (complete)`
- active market profile: `sports:nfl`
- active implementation lane: `NFL P0 profile-aware foundation + event-centric historical research database + master research engine specification + universal feature registry + universal math engine contracts + research asset runtime framework + historical dataset acquisition framework + historical dataset acquisition runtime + research asset source discovery and connector mapping framework + historical research asset certification runtime + research asset lifecycle runtime + NFL schedule research asset population + research asset coverage planner and provider selection framework + first production NFL schedule connector + certified NFL results research asset + certified NFL odds research asset + certified NFL weather research asset + certified NFL injuries research asset + certified NFL team statistics research asset + deterministic historical dataset population layer + deterministic feature snapshot population layer + deterministic mathematical engine population layer`
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
  - `Phase 4.9A - NFL Schedule Research Asset Population`
  - `Phase 4.9B - Research Asset Coverage Planner & Provider Selection Framework`
  - `Phase 4.9C - First Production Connector (NFL Schedule)`
  - `Phase 4.9D - NFL Results Research Asset Population`
  - `Phase 4.9E - NFL Odds Research Asset Population`
  - `Phase 4.9F - NFL Weather Research Asset Population`
  - `Phase 4.9G - NFL Injuries Research Asset Population`
  - `Phase 4.9H - NFL Team Statistics Research Asset Population`
  - `Phase 5.0 - Historical Dataset Population Layer`
  - `Phase 5.1B - Feature Snapshot Population`
  - `Phase 5.2 - Reusable Mathematical Engines`
- current phase objective: Phase 5.2 is complete; the next objective is to implement reusable signals from the certified math-engine layer without starting decision rows or backtesting.
- next phase: `Phase 5.3 - Reusable Signals`
- current blockers: None
- latest validation status:
  - Phase 4.7C runtime validation passed: compileall, certification runtime tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.8 lifecycle runtime code changes are complete and validated: compileall, focused lifecycle tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.9A schedule research asset population code changes are complete and validated: compileall, focused schedule runtime tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.9B coverage planner code changes are complete and validated: compileall, focused planner tests, smoke, architecture, document lifecycle, and ops checks are green.
  - Phase 4.9C connector code changes are complete and validated through compileall, focused NFL schedule connector tests, smoke, architecture, document lifecycle, ops checks, and the final end-task preflight; the branch is clean and pushed.
  - Phase 4.9D results population focused runtime tests pass for the certified schedule/results path, schedule-join rejection path, coverage planner, dashboard readiness, compileall, smoke, architecture, document lifecycle, ops checks, and the full repository test suite.
  - Phase 4.9E odds population code changes are complete and validated: compileall, focused odds runtime tests, smoke, architecture, document lifecycle, ops checks, and the full repository test suite are green.
  - Phase 4.9F weather population code changes are complete and validated: compileall, focused weather runtime tests, smoke, architecture, document lifecycle is advisory with no clear violations, and ops checks are green.
  - Phase 4.9G injuries population code changes are complete and validated: compileall, focused injuries runtime tests, focused injuries documentation tests, smoke, root markdown, OpenAPI contract, architecture, audit lifecycle, document lifecycle advisory with no clear violations, and the full repository test suite are green.
  - Phase 4.9H team statistics population code changes are complete and validated: compileall, focused team-statistics runtime tests, focused team-statistics documentation tests, smoke, root markdown, OpenAPI contract, architecture, audit lifecycle, document lifecycle advisory with no clear violations, repository preflight checks, and the full repository test suite are green.
  - Phase 5.0 historical dataset population code changes are complete and validated: focused dataset-population runtime tests, focused dataset-population documentation tests, adjacent shared-runtime regressions, compileall, smoke, root markdown, OpenAPI contract, architecture, audit lifecycle, ops checks, repository preflight checks, and the full repository test suite are green; document lifecycle remains advisory with one warning and no clear violations.
  - Phase 5.1B feature snapshot population code changes are complete and validated: focused feature registry tests, focused feature snapshot population tests, adjacent dataset and local-platform regressions, compileall, and git diff checks are green; broader repository gates remain queued for the final phase handoff.
- latest full gate result: `passed for the completed Phase 5.0 gate; Phase 5.1B broader repository gates are pending rerun before the final handoff`
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
- Historical dataset population derives one deterministic game-level cutoff from scheduled kickoff minus five minutes; predictor assets select their latest eligible evidence independently at or before that cutoff, while results remain label-only.
- Events own shared context.
- Markets belong to events.
- Selections belong to markets.
- Decision rows are generated later and are not the storage primitive.
- Backtests never read directly from providers.
- The master research engine specification is the next governing layer above the market-profile framework.
- The first production NFL schedule connector is the canonical connector-backed pattern for future research asset population phases.
- NFL results reuse the schedule event identity and cannot certify without a certified games/schedule backbone and a successful event join.
- NFL injuries reuse the certified schedule/results/odds/weather backbone and cannot certify without report-time-safe injury timestamps, successful join alignment, and continued separation between forecast weather and realized weather.
- NFL team statistics reuse the certified schedule/results/odds/weather/injuries backbone and cannot certify unless every metric excludes the target event, remains frozen before the decision cutoff, and preserves row-level alignment evidence alongside the asset-scoped lifecycle state.

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
- `docs/architecture/NFL_ODDS_RESEARCH_ASSET.md`
- `docs/architecture/NFL_WEATHER_RESEARCH_ASSET.md`
- `docs/architecture/NFL_INJURIES_RESEARCH_ASSET.md`
- `docs/architecture/NFL_TEAM_STATISTICS_RESEARCH_ASSET.md`
- `docs/architecture/RESEARCH_ASSET_SOURCE_DISCOVERY_AND_CONNECTOR_MAPPING.md`
- `docs/architecture/RESEARCH_ASSET_COVERAGE_AND_PROVIDER_SELECTION_FRAMEWORK.md`
- `docs/architecture/HISTORICAL_RESEARCH_DATABASE.md`
- `docs/architecture/HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md`
- `docs/architecture/HISTORICAL_DATASET_ACQUISITION_RUNTIME.md`
- `docs/architecture/HISTORICAL_DATASET_POPULATION_LAYER.md`
- `docs/architecture/NFL_SCHEDULE_CONNECTOR.md`
- `docs/architecture/NFL_RESULTS_RESEARCH_ASSET.md`
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
- `docs/reports/PHASE4_9B_RESEARCH_ASSET_COVERAGE_PLANNER_AND_PROVIDER_SELECTION_FRAMEWORK.md`
- `docs/reports/PHASE4_9C_FIRST_PRODUCTION_NFL_SCHEDULE_CONNECTOR.md`
- `docs/reports/PHASE4_9D_NFL_RESULTS_RESEARCH_ASSET_POPULATION.md`
- `docs/reports/PHASE4_9E_NFL_ODDS_RESEARCH_ASSET_POPULATION.md`
- `docs/reports/PHASE4_9F_NFL_WEATHER_RESEARCH_ASSET_POPULATION.md`
- `docs/reports/PHASE4_9G_NFL_INJURIES_RESEARCH_ASSET_POPULATION.md`
- `docs/reports/PHASE4_9H_NFL_TEAM_STATISTICS_RESEARCH_ASSET_POPULATION.md`
- `docs/reports/PHASE5_0_HISTORICAL_DATASET_POPULATION_LAYER.md`
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

`Phase 5.3 - Reusable Signals`
