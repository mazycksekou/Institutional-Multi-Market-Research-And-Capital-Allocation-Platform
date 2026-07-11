# Feature Snapshot Contract

## Snapshot contract primitives

- `dataset_id`
- `batch_id`
- `dataset_row_id`
- `decision_context_id`
- `feature_id`
- `feature_version`
- `entity_scope`
- `decision_cutoff_time`
- `cutoff_policy_version`
- `transformation_version`
- `source_certification_ids`
- `source_lineage_ids`
- `features_known_at_decision_time`
- `model_probability`
- `market_implied_probability`
- `edge`
- `stake`
- `decision_time`
- `odds_at_decision_time`

## Snapshot sources

- `src.data.feature_registry`
- `src.backtesting.backtest_schema.get_backtest_feature_snapshot`
- `src.services.streamlit_dashboard_data.build_readiness_display_payload`
- `src.services.streamlit_dashboard_data.build_readiness_display_rows`

## Contract goal

A snapshot must recreate the exact feature set that was available when the decision was made, and nothing from settlement or future outcomes may leak into it.
For the first reusable NFL feature layer, that means inheriting the certified
Phase 5.0 historical dataset row and its selected evidence rather than
reselecting records from the underlying source asset tables.
