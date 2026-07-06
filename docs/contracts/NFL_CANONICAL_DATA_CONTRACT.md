# NFL Canonical Data Contract

This contract defines the canonical NFL-shaped data entities the repository should support.
It is a discovery contract only and does not imply a fully built ingestion pipeline.

## Contract Rules

- point-in-time records only
- no fabricated fields
- no live provider activation in this phase
- no hidden proprietary logic in the contract surface
- every record should carry lineage and version information
- storage must remain reproducible and auditable

## 1. Raw NFL Record

### Required fields

- `source_id`
- `source_type`
- `record_id`
- `sport`
- `season`
- `week`
- `record_ts`
- `raw_payload`
- `raw_hash`
- `schema_version`

### Notes

Raw records are immutable source captures.
They are the starting point for lineage and replay.

## 2. Normalized NFL Record

### Required fields

- `normalized_record_id`
- `source_record_id`
- `sport`
- `game_id`
- `team`
- `opponent`
- `season`
- `week`
- `record_ts`
- `normalized_payload`
- `schema_version`

### Notes

Normalized records are the canonical internal representation used for downstream feature generation.

## 3. Roster Record

### Required fields

- `team`
- `season`
- `player_id`
- `player_name`
- `position`
- `starter_status`
- `status`
- `jersey_number`

### Optional fields

- `college`
- `years_experience`
- `height`
- `weight`
- `age`

## 4. Depth Chart Record

### Required fields

- `team`
- `season`
- `week`
- `depth_position`
- `depth_rank`
- `player_id`
- `player_name`

### Notes

Depth chart data is relevant for both player-level and unit-level modeling.

## 5. Player Profile Record

### Required fields

- `player_id`
- `player_name`
- `position`
- `team`
- `season`

### Optional fields

- `height`
- `weight`
- `age`
- `years_experience`
- `college`
- `handedness`

## 6. Officials Record

### Required fields

- `game_id`
- `official_id`
- `official_name`
- `position`

## 7. Injury Record

### Required fields

- `team`
- `season`
- `week`
- `player_id`
- `player_name`
- `injury_status`
- `practice_status`
- `report_status`

## 8. Weather Record

### Required fields

- `game_id`
- `stadium`
- `roof`
- `surface`
- `temp`
- `wind`
- `weather`

## 9. Odds Snapshot

### Required fields

- `game_id`
- `market`
- `selection`
- `line_value`
- `american_odds`
- `implied_probability`
- `source_ts`

### Notes

Open, close, and current snapshot times must remain explicit.

## 10. Market Snapshot

### Required fields

- `market_type`
- `game_id`
- `team`
- `opponent`
- `opening_line`
- `closing_line`
- `current_line`
- `source_ts`

## 11. Feature Snapshot

### Required fields

- `feature_snapshot_id`
- `feature_name`
- `feature_version`
- `feature_pack_version`
- `source_record_id`
- `input_snapshot_id`
- `cutoff_ts`
- `data_tier`
- `values`

### Notes

Feature snapshots must be point-in-time and reproducible.

## 12. Backtest Row

### Required fields

- `backtest_row_id`
- `run_id`
- `feature_snapshot_id`
- `market`
- `selection`
- `line_value`
- `open_odds`
- `close_odds`
- `settled_outcome`
- `clv`
- `roi`

## 13. Research Row

### Required fields

- `experiment_id`
- `hypothesis_id`
- `sample_id`
- `feature_snapshot_id`
- `research_result`
- `created_at`

## 14. Model Input / Output

### Model input required fields

- `model_input_id`
- `model_version`
- `feature_snapshot_id`
- `target_horizon`
- `input_payload`

### Model output required fields

- `model_output_id`
- `model_version`
- `prediction`
- `confidence`
- `output_payload`

## 15. Provider Metadata

### Required fields

- `provider_id`
- `provider_type`
- `owner`
- `coverage`
- `terms_status`
- `blocked_reason`
- `schema_version`

## 16. Lineage Record

### Required fields

- `lineage_id`
- `source_record_id`
- `normalized_record_id`
- `feature_snapshot_id`
- `model_run_id`
- `backtest_run_id`
- `created_at`

## 17. Versioning Fields

Every canonical record family should be versioned with:

- `schema_version`
- `dataset_version`
- `feature_pack_version`
- `model_version`
- `pipeline_version`

## Contract Boundary

This contract is about external shape and lineage only.
It does not expose:

- internal algorithms
- proprietary feature engineering details
- model weights
- provider credentials
- execution logic

