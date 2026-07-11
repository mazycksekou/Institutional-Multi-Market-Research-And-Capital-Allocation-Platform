
# Feature Store Architecture

## Contract

Every feature record must include:

- `feature_id`
- `feature_version`
- `owner`
- `market`
- `sport`
- `asset_class`
- `entity_scope`
- `dataset_grain_compatibility`
- `raw_or_derived`
- `required_inputs`
- `calculation_stage`
- `cutoff_semantics`
- `transformation_version`
- `backtest_usage`
- `model_usage`
- `dashboard_usage`
- `version`

## Storage Model

| Layer | Purpose |
| --- | --- |
| Definition layer | Describes feature semantics and ownership. |
| Materialization layer | Stores computed feature values. |
| Snapshot layer | Preserves point-in-time feature states. |
| Usage layer | Tracks downstream consumers and compatibility. |

## Phase 5.1A Runtime Owner

The canonical runtime owner for reusable feature definitions is:

- `src.data.feature_registry`

The first active source dataset for this runtime contract is:

- `dataset.sports.nfl.historical_dataset`

Phase 5.1A defined the contract surface for reusable feature snapshots.
Phase 5.1B materializes those snapshots from the certified historical dataset layer.

## Phase 5.1B Runtime Owner

The canonical runtime owner for reusable feature-snapshot population is:

- `src.data.feature_registry`

The phase materializes feature rows, batch summaries, and lineage edges through the shared local storage owner.

## Phase 5.1A Grain Rule

The certified Phase 5.0 dataset row already owns the market decision context.
Feature snapshots must preserve that context by inheriting:

- `dataset_row_id`
- `decision_context_id`
- `market_type`
- `selection`
- `book`
- `decision_cutoff_time`

The canonical feature-snapshot grain is:

- one feature value
- for one certified dataset row
- for one `feature_id`
- for one `feature_version`
- for one `entity_scope`
- for one `transformation_version`

This keeps:

- `moneyline / home / consensus`
- `spread / home / consensus`
- `total / over / consensus`

as three distinct feature contexts for the current one-game fixture.
The current implementation persists 38 features across those three contexts as 114 deterministic feature rows.

## Notes

- The feature store must stay market-agnostic.
- Domain logic can compute features, but the store owns persistence and versioning.
- Backtest and dashboard consumers must resolve the feature version they read.
- Once a certified historical dataset layer exists, the first feature layer must inherit that dataset as its only canonical predictor input rather than rereading raw or normalized source asset tables.
