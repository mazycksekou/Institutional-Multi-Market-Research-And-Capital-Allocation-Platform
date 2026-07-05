# Complete Metric Catalog

## Raw input / contract metrics

- Backtest snapshot fields: `event_id`, `contract_id`, `sport`, `league`, `market`, `decision_time`, `odds_at_decision_time`, `features_known_at_decision_time`, `model_probability`, `market_implied_probability`, `edge`, `stake`, `final_result`, `profit_loss`, `closing_line`, `clv`
- Leakage guard fields: `final_result`, `winner`, `home_score`, `away_score`, `profit_loss`, `closing_odds`, `closing_line`, `clv`, `result`, `settled_result`, `bet_result`, `outcome`
- Universal feature groups: `core_event`, `line_core`, `line_movement`, `settlement`, `team_stats`, `player_stats`, `projection_control`
- Provider readiness fields: lane status, source count, auth type, access type

## Derived feature metrics

- `market_implied_probability`
- `model_probability`
- `edge`
- `clv`
- `closing_line_value`
- `odds_movement`
- `expected_value`
- `expected_closing_edge`
- `kelly_fraction`
- `bankroll_drawdown`
- `risk_of_ruin`
- `volatility`
- `pace`
- `offensive_rating`
- `defensive_rating`
- `liquidity`
- `spread`
- `funding_pressure`
- `open_interest_pressure`

## Model-output metric families

| Product lane | Market output metrics | Backtest validation metrics |
|---|---:|---:|
| Sports | 25 | 33 |
| Stocks / 0DTE | 21 | 33 |
| Predictions | 19 | 33 |

## Calibration metrics discovered

- `brier_score`
- `log_loss`
- `calibration_error`
- `implied_probability_calibration_curve`
- `odds_bucket_calibration`
- `deflated_sharpe_ratio`
- `probability_of_backtest_overfitting`

## Performance metrics discovered

- `net_profit`
- `net_return_percent`
- `profit_factor`
- `sharpe_ratio`
- `sortino_ratio`
- `max_drawdown`
- `expectancy`
- `average_r`
- `trade_count`
- `win_rate`
- `loss_rate`
- `alpha_decay_half_life`
- `time_under_water`

## Governance / reporting metrics discovered

- readiness and coverage flags from `src.services.streamlit_dashboard_data`
- source counts and phase allowances from `src.data.data_source_registry`
- model registry metadata from `src/sports/models/compressed/*.metadata.json`
