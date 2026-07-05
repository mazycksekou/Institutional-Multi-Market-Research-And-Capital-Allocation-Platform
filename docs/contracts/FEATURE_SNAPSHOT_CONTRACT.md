# Feature Snapshot Contract

## Snapshot contract primitives

- `features_known_at_decision_time`
- `model_probability`
- `market_implied_probability`
- `edge`
- `stake`
- `decision_time`
- `odds_at_decision_time`

## Snapshot sources

- `src.backtesting.backtest_schema.get_backtest_feature_snapshot`
- `src.services.streamlit_dashboard_data.build_readiness_display_payload`
- `src.services.streamlit_dashboard_data.build_readiness_display_rows`

## Contract goal

A snapshot must recreate the exact feature set that was available when the decision was made, and nothing from settlement or future outcomes may leak into it.
