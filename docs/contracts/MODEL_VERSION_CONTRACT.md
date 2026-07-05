# Model Version Contract

## Canonical version metadata discovered

- `sport_key`
- `market`
- `model_type`
- `model_version`
- `status`
- `trained_at`
- `training_rows`
- `qualified_bets`
- `roi`
- `avg_clv_percent`
- `calibrator.method`
- `calibrator.requested_method`
- `calibrator.positive_count`
- `calibrator.sample_size`
- `calibrator.reason`
- `feature_columns`

## Concrete artifact evidence

- Model artifact directory: `src/sports/models/compressed/`
- Example artifact: `basketball_nba_v1`
- Example metadata status: `backtest_complete`

## Versioning rule

Every future model artifact should carry the same metadata surface so that backtests, dashboards, and reports can compare versions without guesswork.
