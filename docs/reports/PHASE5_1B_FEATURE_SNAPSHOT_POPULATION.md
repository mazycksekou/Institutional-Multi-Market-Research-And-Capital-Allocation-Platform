# Phase 5.1B - Feature Snapshot Population

## Summary

Phase 5.1B materializes the first reusable NFL feature layer from the certified Phase 5.0 historical dataset batch.
The implementation reuses the canonical dataset, certification, lifecycle, storage, coverage, dashboard, and NFL P0 owners rather than creating a parallel feature framework.

## What Changed

- populated deterministic feature snapshots from `dataset.sports.nfl.historical_dataset`
- preserved the certified Phase 5.0 cutoff policy and selected evidence chain
- registered 38 reusable feature definitions and materialized 114 persisted feature rows for the current minimum slice
- preserved explicit missingness rather than silently imputing or zero-filling
- persisted feature batch, row, lineage, and evidence identifiers through the shared local storage owner
- added dashboard wrappers for feature-layer readiness and NFL P0 feature-layer rollup
- added focused regression coverage for grain preservation, idempotent reruns, cutoff inheritance, lineage sensitivity, and package exports

## Dataset Grain And Fixture Context

The certified historical dataset grain remains the source of truth for this phase:

- `dataset_id`
- `game_id`
- `market_type`
- `selection`
- `book`
- `decision_cutoff_time`

For the current one-game fixture, that yields three distinct contexts that remain distinct feature contexts:

- `moneyline / home / consensus`
- `spread / home / consensus`
- `total / over / consensus`

The feature layer preserves those three contexts instead of collapsing them into a single representative row.

## Population Behavior

The feature population runtime:

- reads only the certified historical dataset batch
- inherits the Phase 5.0 decision cutoff of scheduled kickoff minus five minutes
- materializes one row per feature definition and dataset context
- keeps results out of predictor feature definitions
- persists row-level lineage and batch-level evidence references
- stays deterministic across reruns

The minimum slice currently produces:

- 38 registered active feature definitions
- 3 dataset contexts
- 114 feature rows
- 115 lineage edges including the batch summary lineage row

## Canonical Owners Reused

- `src.data.feature_registry`
- `src.data.historical_research_database`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.data.local_platform`
- `src.storage.local_store`
- `src.data.nfl_p0_foundation`
- `src.market_intelligence.research_asset_coverage_planner`
- `src.services.streamlit_dashboard_data`

## Validation

- focused feature registry tests: passed
- focused feature snapshot population tests: passed
- adjacent historical dataset regression: passed
- local-platform regression: passed
- compileall: passed
- git diff --check: passed

## Senior Systems Engineer Review

### Strengths

- Reuses the certified dataset layer instead of reopening raw source reads.
- Keeps row ids, batch ids, lineage ids, and evidence ids deterministic.
- Preserves explicit missingness and point-in-time safety.
- Exposes feature-layer readiness through the shared dashboard adapter.

### Weaknesses

- The current layer is intentionally minimum-slice only.
- Feature snapshots remain an evidence substrate, not a math or signal layer.

### Implemented Improvements

- deterministic feature-materialization path
- feature-layer dashboard readiness
- feature-layer package exports
- persisted feature lineage edges for later evidence packaging

### Deferred Improvements

- mathematical engines
- signals
- decision rows
- backtesting
- optional enrichment assets

### Recommendation

Advance to Phase 5.2 and keep the feature layer frozen as the canonical reusable input to later mathematical engines.

## Worldview / Research Query Engine Review

### Query Readiness

The layer is queryable by dataset id, batch id, row id, feature id, decision context, cutoff, lineage, and evidence package.

### Evidence-Package Readiness

The persisted feature batch includes source certification references, source lineage references, selected source row ids, missingness metadata, and lineage edges.

### Experiment Readiness

The layer is ready for downstream mathematical engines and later research experiments, but it does not create any predictive outputs itself.

### Unresolved Blockers

No minimum-schema blockers remain.
Optional enrichment assets stay deferred and non-blocking.

### Recommendation

Use the certified historical dataset layer as the sole upstream input for Phase 5.2 reusable mathematical engines.
