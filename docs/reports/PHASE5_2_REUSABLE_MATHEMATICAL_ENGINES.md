# Phase 5.2 - Reusable Mathematical Engines

## Summary

Phase 5.2 materializes the first reusable NFL mathematical-engine layer from the certified Phase 5.1B feature batch.
The implementation reuses the canonical feature, dataset, certification, lifecycle, storage, coverage, dashboard, and NFL P0 owners rather than creating a parallel math framework.

## What Changed

- populated deterministic math-engine rows from the certified feature snapshot layer derived from `dataset.sports.nfl.historical_dataset`
- preserved the certified Phase 5.0 cutoff policy and feature-layer evidence chain
- registered 9 reusable mathematical-engine definitions and materialized 27 persisted math rows for the current minimum slice
- preserved explicit missingness rather than silently imputing or zero-filling
- persisted math batch, row, lineage, evidence, certification, and lifecycle identifiers through the shared local storage owner
- added read-only dashboard wrappers for math-layer readiness and NFL P0 math-layer rollup
- added focused regression coverage for rerun idempotency, persisted dashboard reconstruction, package exports, and P0 readiness exposure

## Grain And Context

The certified feature batch remains the source of truth for this phase.
The math layer preserves the same three feature contexts that Phase 5.1B materialized from the certified historical dataset batch:

- `moneyline / home / consensus / home`
- `spread / home / consensus / home`
- `total / over / consensus / ""`

The math layer preserves those contexts instead of collapsing them into a single representative row.

## Population Behavior

The math population runtime:

- reads only the certified feature batch
- inherits the Phase 5.0 decision cutoff of scheduled kickoff minus five minutes
- materializes one row per registered engine definition and feature context
- keeps results out of predictor engine definitions
- persists row-level lineage and batch-level evidence references
- stays deterministic across reruns by reusing persisted state when the batch already exists

The minimum slice currently produces:

- 9 registered reusable mathematical-engine definitions
- 3 feature contexts
- 27 math rows

## Canonical Owners Reused

- `src.data.math_engine_population`
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

- focused mathematical-engine runtime tests: passed
- focused mathematical-engine docs tests: passed
- adjacent feature, dataset, and P0 regressions: passed
- compileall: passed
- git diff --check: passed

## Senior Systems Engineer Review

### Strengths

- Reuses the certified feature layer instead of reopening raw source reads.
- Keeps row ids, batch ids, lineage ids, and evidence ids deterministic.
- Preserves explicit missingness and point-in-time safety.
- Exposes math-layer readiness through the shared dashboard adapter.

### Weaknesses

- The current layer is intentionally minimum-slice only.
- Mathematical engines remain an evidence substrate, not a signal or decision layer.

### Implemented Improvements

- deterministic math-materialization path
- math-layer dashboard readiness
- math-layer package exports
- persisted math lineage edges for later evidence packaging
- read-only dashboard reconstruction from persisted state

### Deferred Improvements

- signals
- decision rows
- backtesting
- optional enrichment assets

### Recommendation

Advance to Phase 5.3 and keep the math layer frozen as the canonical reusable input to later signal generation.

## Worldview / Research Query Engine Review

### Query Readiness

The layer is queryable by dataset id, batch id, row id, engine id, feature context, cutoff, lineage, and evidence package.

### Evidence-Package Readiness

The persisted math batch includes source certification references, source lineage references, selected source row ids, missingness metadata, and lineage edges.

### Experiment Readiness

The layer is ready for downstream signal generation and later research experiments, but it does not create any predictive outputs itself.

### Unresolved Blockers

No minimum-schema blockers remain.
Optional enrichment assets stay deferred and non-blocking.

### Recommendation

Use the certified feature layer as the sole upstream input for Phase 5.3 reusable signals.
