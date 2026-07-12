# Math Engine Population Layer

## Purpose

This document owns the reusable mathematical-engine population layer that sits above the certified NFL feature snapshots.
The canonical runtime owner is `src.data.math_engine_population`.
It materializes deterministic math-engine rows from `dataset.sports.nfl.historical_dataset` only through the certified feature layer and never rereads raw provider tables or normalized source tables directly.

## Canonical Owners Reused

- `src.data.math_engine_population`
- `src.data.feature_registry`
- `src.data.historical_research_database`
- `src.data.historical_research_asset_certification_runtime`
- `src.data.research_asset_lifecycle_runtime`
- `src.data.nfl_p0_foundation`
- `src.storage.local_store`
- `src.market_intelligence.research_asset_coverage_planner`
- `src.services.streamlit_dashboard_data`

## Canonical Input

The first reusable NFL math layer inherits the already certified feature layer.

- source dataset id: `dataset.sports.nfl.historical_dataset`
- source feature layer: certified feature snapshots derived from `dataset.sports.nfl.historical_dataset`
- source decision cutoff: `scheduled_kickoff_time - 5 minutes`
- source evidence: certified dataset rows, certified feature snapshots, and their lineage / certification references

The current minimum slice materializes 9 reusable engine definitions across 3 dataset contexts for 27 persisted math-engine rows.

## Math Engine Snapshot Grain

The canonical math snapshot grain is one mathematical-engine value for one certified feature context and one dataset row, at one decision cutoff, for one engine id, version, entity scope, and transformation version.

The reusable layer therefore keys each math snapshot by:

- `dataset_row_id`
- `decision_context_id`
- `feature_context_id`
- `engine_id`
- `engine_version`
- `entity_scope`
- `decision_cutoff_time`
- `transformation_version`

That grain keeps the three feature contexts distinct and prevents market-context collapse.

## Materialization Rules

The population runtime:

1. Reads only the certified feature snapshot batch.
2. Reuses the selected evidence already certified by Phase 5.1B.
3. Builds deterministic engine values from registered reusable engine definitions.
4. Preserves explicit missingness rather than silently imputing or zero-filling.
5. Persists stable math row ids, batch ids, lineage ids, evidence ids, and summary rows.
6. Writes lineage edges so the evidence chain stays queryable later.
7. Rejects any rerun that would mutate the certified lifecycle chain instead of reusing persisted state.

## Point-In-Time Safety

The math layer inherits the Phase 5.0 cutoff policy:

- `decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

The math layer must not reread or reselect predictor evidence from raw provider payloads, normalized source tables, or final results.
It preserves:

- scheduled kickoff
- decision cutoff
- selected source row ids
- source certification ids
- source lineage ids
- engine lineage ids
- missing required asset ids

Results remain label-only and never enter predictor engine definitions.

## Persistence And Queryability

The population runtime persists row-level math snapshots and a summary snapshot through the shared local storage owner.
Persisted artifacts include:

- row-level engine values
- batch summary rows
- math lineage edges
- math evidence ids
- source certification references
- source alignment references
- selected source row references
- missingness metadata
- dataset certification references
- lifecycle state

That keeps the layer deterministic, idempotent, and reconstructable from local state.

## Dashboard And Readiness Integration

The math layer is exposed through the shared dashboard adapter and the NFL P0 readiness rollup.
The dashboard surface reports:

- canonical dataset id
- math batch id
- engine row count
- lineage completeness
- provenance completeness
- explicit missingness
- unresolved blockers
- readiness state

The NFL P0 foundation now also reports math-layer readiness alongside the dataset-layer and feature-layer readiness that were already present.

## Senior Systems Engineer Review

### Strengths

- Reuses the certified feature layer instead of reopening raw provider reads.
- Keeps row ids, batch ids, lineage ids, and evidence ids deterministic.
- Preserves 3 distinct contexts for the one-game fixture without collapsing them.
- Keeps missingness explicit and queryable.

### Weaknesses

- The current minimum slice is intentionally narrow and fixture-backed.
- The math layer remains a reusable evidence substrate, not a signal or decision layer.

### Recommendation

Keep Phase 5.2 frozen as the canonical reusable math input to later signal and decision phases.

## Worldview / Research Query Engine Review

### Query Readiness

The layer is queryable by dataset, batch, row, engine id, feature context, cutoff, lineage, and evidence package.

### Evidence Readiness

Each persisted math row can be traced back to the certified feature context and its selected evidence.

### Experiment Readiness

The layer is ready for later signal and decision layers, but it does not itself create those outputs.

### Recommendation

Use the certified feature layer as the sole upstream input for later reusable math and signal layers.
