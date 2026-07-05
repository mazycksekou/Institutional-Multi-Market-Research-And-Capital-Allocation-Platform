
# Feature Store Architecture

## Contract

Every feature record must include:

- `feature_id`
- `owner`
- `market`
- `sport`
- `asset_class`
- `raw_or_derived`
- `required_inputs`
- `calculation_stage`
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

## Notes

- The feature store must stay market-agnostic.
- Domain logic can compute features, but the store owns persistence and versioning.
- Backtest and dashboard consumers must resolve the feature version they read.
