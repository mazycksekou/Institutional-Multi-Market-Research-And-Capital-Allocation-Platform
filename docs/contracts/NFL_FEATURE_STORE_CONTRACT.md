# NFL Feature Store Contract

This contract defines the feature-store shape for NFL feature families.
It is discovery-first and does not claim a full storage implementation yet.

## Contract Rules

- store features by canonical name
- separate atomic and composite feature namespaces
- preserve lineage and cutoff timestamps
- keep point-in-time evidence only
- never compute feature values inside the store layer
- never hide provenance

## Required Feature Fields

- `feature_id`
- `feature_name`
- `feature_type` (`ATOMIC` or `COMPOSITE`)
- `owner`
- `sport`
- `market`
- `position_group`
- `data_tier`
- `feature_pack_version`
- `cutoff_ts`
- `source_snapshot_id`
- `lineage_id`
- `storage_location`
- `values`

## Atomic Feature Expectations

Atomic features should map directly to source fields or direct canonical records.

Examples:

- player identity
- game identity
- official identity
- weather identity
- market quote identity
- roster identity

## Composite Feature Expectations

Composite features should be deterministic calculations from atomic inputs or other approved composites.

Examples:

- red zone percentage
- offensive line score
- weather impact score
- market relevance score
- football impact score
- calibration confidence

## Feature Families Discovered

The repository already contains feature-family work for:

- schedule and results
- play-by-play efficiency
- pace / volume
- player availability
- depth chart stability
- roster continuity
- coaching / staff
- matchup context
- weather context
- market odds
- historical similarity
- diagnostics / red-team scoring

## Store Invariants

- no duplicate owner per feature family
- no hidden recomputation without version bump
- no leakage across cutoff boundaries
- no unsupported market or sport should silently pass validation

## Current Maturity

The repo has enough structure to define the feature store contract now.
It does not yet have the final NFL end-to-end feature store slice backed by validated historical data.

