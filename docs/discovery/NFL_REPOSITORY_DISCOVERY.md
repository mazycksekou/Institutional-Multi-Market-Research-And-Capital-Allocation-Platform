# NFL Repository Discovery

## Scope

This document records the Phase 4.1 discovery pass for NFL capability in the repository.
It is discovery-only: no provider activation, no ingestion, no feature engineering, no model training, and no runtime behavior changes were introduced.

## Baseline

- Branch: `main`
- HEAD: `64f4ad1be635c8a9224f9363d1cb49b5f41183d1`
- Working tree: clean
- Upstream: `origin/main`

## Discovery Method

The audit used:

- repository-wide filename and content scans
- AST-oriented symbol review of NFL-related modules
- import and dependency tracing
- existing report and matrix documents under `docs/`
- test coverage inspection for NFL-facing surfaces

The review looked across:

- `src/`
- `tests/`
- `scripts/`
- `docs/`

## What Exists Today

### Runtime and domain modules

Discovered NFL-related runtime modules include:

- `src/data/nfl_open_data_sources.py`
- `src/data/nfl_open_data_field_catalog.py`
- `src/data/nfl_open_data_source_exhaustion.py`
- `src/data/nfl_historical_pattern_lab.py`
- `src/providers/nfl_open_data_adapters.py`
- `src/providers/nfl_open_data_backfill.py`
- `src/providers/nfl_open_data_feature_builders.py`
- `src/providers/nfl_open_data_feature_readiness.py`
- `src/providers/nfl_coaching_adapters.py`
- `src/providers/ncaaf_collegefootballdata_adapter.py`
- `src/market_intelligence/football_impact_schema.py`
- `src/market_intelligence/football_impact_common.py`
- `src/market_intelligence/football_data_availability.py`
- `src/market_intelligence/football_availability_context.py`
- `src/market_intelligence/football_incentive_context.py`
- `src/market_intelligence/football_market_relevance.py`
- `src/market_intelligence/football_matchup_context.py`
- `src/market_intelligence/football_personnel_context.py`
- `src/market_intelligence/football_play_drive_impact.py`
- `src/market_intelligence/football_role_impact.py`
- `src/market_intelligence/nfl_cutoff_week_features.py`
- `src/market_intelligence/nfl_coaching_sources.py`
- `src/market_intelligence/nfl_coaching_feature_builders.py`
- `src/analytics/football_impact_report.py`
- `src/analytics/football_impact_calibration.py`
- `src/analytics/football_impact_red_team.py`

### API and service surfaces

NFL-related functionality is exposed through shared platform services rather than a dedicated NFL-only API package:

- `src/services/streamlit_dashboard_facade.py`
- `src/services/runtime_facade.py`
- `main.py`
- `streamlit_app.py`

The shared API layer and dashboard facade expose football diagnostics, readiness, and report helpers used by the tests and UI.

### Tests

NFL-focused tests discovered in the repo include:

- `tests/test_football_impact_intelligence.py`
- `tests/test_nfl_open_data_sources.py`
- `tests/test_nfl_open_data_field_catalog.py`
- `tests/test_nfl_open_data_feature_builders.py`
- `tests/test_nfl_open_data_backfill.py`
- `tests/test_nfl_open_data_adapters.py`
- `tests/test_nfl_coaching_sources.py`
- `tests/test_nfl_coaching_feature_builders.py`
- `tests/test_nfl_coaching_adapters.py`
- `tests/test_nfl_cutoff_week_features.py`
- `tests/test_nfl_historical_pattern_lab.py`
- `tests/test_nfl_historical_pattern_validation.py`
- `tests/test_nfl_source_exhaustion.py`
- `tests/test_nfl_model_activation.py`
- `tests/test_ncaaf_collegefootballdata_adapter.py`
- `tests/test_college_football_model_activation.py`

### Report and matrix artifacts already in the repo

The NFL discovery pass builds on existing higher-level documentation:

- `docs/reports/matrices/SPORT_CAPABILITY_MATRIX.md`
- `docs/reports/matrices/SPORT_BACKTEST_COMPATIBILITY_MATRIX.md`
- `docs/reports/matrices/MARKET_CAPABILITY_MATRIX.md`
- `docs/reports/matrices/PROVIDER_FIELD_MATRIX.md`
- `docs/reports/matrices/IMPLEMENTATION_MATURITY_MATRIX.md`
- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/CANONICAL_OWNERSHIP_MAP.md`
- `docs/architecture/DEPENDENCY_FLOW_MAP.md`
- `docs/architecture/TERMINOLOGY_STANDARD.md`

## Discovery Summary

### NFL data foundation

The repository already has a recognizable NFL open-data foundation:

- open-data source registry
- field catalog
- source exhaustion audit
- feature-builder readiness
- backfill / coverage reporting
- point-in-time cutoff-week helpers
- historical pattern laboratory

### Football intelligence foundation

The repository also has a non-trivial football intelligence layer:

- play-drive and possession impact scoring
- role-based player impact scoring
- personnel and matchup context scoring
- availability and incentive modifiers
- market relevance scoring
- red-team and calibration reporting

### Coaching and staff lane

There is a separate coaching/staff discovery lane:

- source registry
- source classification
- adapter layer
- feature builders
- acquisition and readiness reports

Most coaching sources are blocked pending terms, robots, or provenance review.

### NCAAF / college football lane

The repository includes a separate NCAAF adapter path via CollegeFootballData and related open-data registry entries.
This is a discovery/adapter surface only; it is not a live ingestion commitment.

## High-Level Discovery Result

The NFL slice is best described as:

- structurally real
- discovery rich
- contractually explicit
- validation aware
- not yet backed by fully validated end-to-end ingested NFL data

That means the architecture is foundation-ready, but the platform is still missing the final reusable data slice that would support full backtesting and model work.

## Implementation Boundary

This phase intentionally did not:

- activate providers
- ingest live or historical NFL data
- build a new duplicate NFL subsystem
- change runtime behavior
- create a new branch for implementation

## Next Doc Set

The detailed findings are captured in:

- `docs/discovery/NFL_CAPABILITY_MATRIX.md`
- `docs/discovery/NFL_PROVIDER_INVENTORY.md`
- `docs/discovery/NFL_FEATURE_INVENTORY.md`
- `docs/discovery/NFL_METRIC_INVENTORY.md`
- `docs/contracts/NFL_CANONICAL_DATA_CONTRACT.md`
- `docs/contracts/NFL_BACKTEST_CONTRACT.md`
- `docs/contracts/NFL_FEATURE_STORE_CONTRACT.md`
- `docs/contracts/NFL_STREAMLIT_CONTRACT.md`
- `docs/contracts/NFL_PROVIDER_CONTRACT.md`
- `docs/contracts/NFL_ATOMIC_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_COMPOSITE_FEATURE_CONTRACT.md`
- `docs/contracts/NFL_POSITION_GROUP_FEATURE_CONTRACT.md`
- `docs/discovery/NFL_POSITION_GROUP_FEATURE_INVENTORY.md`
- `docs/reports/NFL_GAP_ANALYSIS.md`
- `docs/reports/NFL_VERTICAL_SLICE_RECOMMENDATION.md`

