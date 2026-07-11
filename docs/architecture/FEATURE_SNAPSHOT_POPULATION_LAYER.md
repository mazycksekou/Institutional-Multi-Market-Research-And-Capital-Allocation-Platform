# Feature Snapshot Population Layer

## Purpose

This document owns the reusable feature-snapshot population layer that sits above the certified historical dataset batch.
The canonical runtime owner is `src.data.feature_registry`.
It materializes deterministic feature snapshots from `dataset.sports.nfl.historical_dataset` without rereading raw provider tables or normalized source tables.

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

## Canonical Input

The first reusable NFL feature layer inherits the already certified and persisted historical dataset layer.

- dataset id: `dataset.sports.nfl.historical_dataset`
- dataset row grain: `dataset_id`, `game_id`, `market_type`, `selection`, `book`, `decision_cutoff_time`
- row-level identities inherited by the feature layer: `dataset_row_id`, `decision_context_id`

The current one-game fixture preserves three distinct dataset contexts:

- `moneyline / home / consensus`
- `spread / home / consensus`
- `total / over / consensus`

## Feature Snapshot Grain

The canonical feature snapshot grain is one feature value for one certified dataset row and one decision context, at one decision cutoff, for one feature id, version, entity scope, and transformation version.

The reusable layer therefore keys each feature snapshot by:

- `dataset_row_id`
- `decision_context_id`
- `feature_id`
- `feature_version`
- `entity_scope`
- `decision_cutoff_time`
- `transformation_version`

That grain keeps distinct market or team contexts from being collapsed or multiplied.

## Materialization Rules

The population runtime:

1. Reads only the certified historical dataset batch.
2. Reuses the selected evidence already certified by Phase 5.0.
3. Builds one feature row per registered feature definition and dataset context.
4. Preserves explicit missingness rather than silently imputing or zero-filling.
5. Persists stable feature row ids, batch ids, lineage ids, evidence ids, and summary rows.
6. Writes lineage edges so the evidence chain stays queryable later.

The current minimum slice materializes 38 registered features across 3 dataset contexts for 114 persisted feature rows.

## Point-In-Time Safety

The feature layer inherits the Phase 5.0 cutoff policy:

- `decision_cutoff_time = scheduled_kickoff_time - 5 minutes`

Feature snapshots must not reread or reselect predictor evidence from raw provider payloads or normalized source asset tables.
They must preserve:

- scheduled kickoff
- decision cutoff
- selected source row ids
- source certification ids
- source lineage ids
- missing required asset ids

Results remain label-only and never enter predictor feature definitions.

## Persistence And Queryability

The population runtime persists row-level feature snapshots and a summary snapshot through the shared local storage owner.
Persisted artifacts include:

- row-level feature values
- batch summary rows
- feature lineage edges
- feature evidence ids
- source certification references
- source alignment references
- selected source row references
- missingness metadata

That keeps the layer deterministic, idempotent, and reconstructable from local state.

## Dashboard And Readiness Integration

The feature layer is exposed through the shared dashboard adapter and the NFL P0 readiness rollup.
The dashboard surface reports:

- canonical dataset id
- feature batch id
- feature snapshot count
- lineage completeness
- provenance completeness
- explicit missingness
- unresolved blockers
- readiness state

The NFL P0 foundation now also reports feature-layer readiness alongside the dataset-layer readiness that was already present.

## Senior Systems Engineer Review

### Strengths

- Reuses the canonical dataset layer instead of reopening raw provider reads.
- Keeps feature row ids, batch ids, and lineage ids deterministic.
- Preserves 3 distinct contexts for the one-game fixture without collapsing them.
- Keeps missingness explicit and queryable.

### Weaknesses

- The current minimum slice is intentionally narrow and still fixture-backed.
- The feature layer remains a reusable evidence substrate, not a math or signal layer.

### Recommendation

Keep Phase 5.1B as the final reusable feature-materialization layer before the repository moves to mathematical engines.

## Worldview / Research Query Engine Review

### Query Readiness

The layer is queryable by dataset, batch, row, feature id, decision context, cutoff, lineage, and evidence package.

### Evidence Readiness

Each persisted feature row can be traced back to the certified historical dataset row and its selected evidence.

### Experiment Readiness

The layer is ready for later mathematical-engine and signal layers, but it does not itself create those outputs.

### Recommendation

Use the certified historical dataset layer as the only upstream input for later reusable research layers.
