# NFL Feature Store Contract

This contract defines the feature-store shape for NFL feature families.
Phase 5.1A establishes the canonical reusable feature-definition contract and
feature-snapshot grain that Phase 5.1B will populate from the certified
historical dataset layer.
It does not claim a full feature-snapshot population or certification
implementation yet.

## Contract Rules

- store features by canonical name
- separate atomic and composite feature namespaces
- preserve lineage and cutoff timestamps
- keep point-in-time evidence only
- never compute feature values inside the store layer
- never hide provenance
- treat `dataset.sports.nfl.historical_dataset` as the sole canonical input to the first reusable feature layer
- do not reread or reselect predictor evidence from raw provider payloads or normalized source asset tables
- preserve `dataset_row_id` and `decision_context_id`
- preserve the certified Phase 5.0 cutoff rule: `decision_cutoff_time = scheduled_kickoff_time - 5 minutes`
- keep `label_*` and realized outcome fields out of predictor feature definitions

## Required Feature Fields

- `feature_id`
- `feature_name`
- `feature_family`
- `feature_version`
- `feature_type` (`ATOMIC` or `COMPOSITE`)
- `owner`
- `sport`
- `market`
- `entity_scope`
- `dataset_grain_compatibility`
- `position_group`
- `data_tier`
- `feature_pack_version`
- `cutoff_ts`
- `cutoff_policy_version`
- `source_snapshot_id`
- `source_dataset_id`
- `source_dataset_field_refs`
- `lineage_id`
- `lineage_requirements`
- `source_certification_ids`
- `storage_location`
- `value_type`
- `unit`
- `missingness_policy`
- `transformation_definition`
- `transformation_version`
- `point_in_time_constraints`
- `expected_range_or_allowed_values`
- `lifecycle_state`
- `certification_state`
- `portability_classification`
- `values`

## Phase 5.1A Canonical Input

The first reusable feature layer inherits the already selected and certified
predictor evidence from:

- `dataset.sports.nfl.historical_dataset`

The Phase 5.0 dataset row already encodes the event and market decision
context. Phase 5.1A must preserve that context rather than collapsing it.

### Certified Dataset Row Grain

The exact current dataset-row key is:

- `dataset_id`
- `game_id`
- `market_type`
- `selection`
- `book`
- `decision_cutoff_time`

This is why one fixture game currently produces three rows:

- `moneyline / home / consensus`
- `spread / home / consensus`
- `total / over / consensus`

The `total / over / consensus` row is intentionally event-scoped and may have a
blank `team_side`.

### Canonical Feature Snapshot Grain

The first reusable feature layer must treat one feature value as belonging to:

- one certified `dataset_row_id`
- one `decision_context_id`
- one `feature_id`
- one `feature_version`
- one `entity_scope`
- one `decision_cutoff_time`
- one `transformation_version`

This preserves distinct market contexts and prevents one-to-many evidence from
multiplying the canonical game row.

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

## Active Phase 5.1A Minimum Feature Families

The first active feature contract set supported by the certified historical
dataset layer is limited to dataset-backed fields and deterministic
transformations of those fields:

- event context
- market context
- weather context
- injury context
- team-statistics freshness context
- data-quality context

The active Phase 5.1A registry intentionally excludes unsupported dataset
payloads and deferred mathematical outputs.

## Deferred In Phase 5.1A

These remain out of the active registry until the certified dataset layer
exposes them directly without raw-source rereads:

- weather temperature
- wind speed
- precipitation probability
- injury practice-state counts
- team-stat metric values
- team-stat home-away differences
- team-stat measurement-window metadata
- model probability
- expected value
- edge
- Kelly sizing
- signals
- decision classifications

## Store Invariants

- no duplicate owner per feature family
- no hidden recomputation without version bump
- no leakage across cutoff boundaries
- no unsupported market or sport should silently pass validation
- scalar features must produce at most one value per `feature_id`, `feature_version`, `entity_scope`, and certified dataset context
- missing evidence must remain explicit and must not silently become zero

## Current Maturity

The repo has enough structure to define the feature store contract now.
It now has a canonical Phase 5.1A reusable feature-definition contract backed
by the certified historical dataset layer.
It does not yet have the final NFL end-to-end feature snapshot population,
feature certification, or backtest-ready feature materialization slice.
