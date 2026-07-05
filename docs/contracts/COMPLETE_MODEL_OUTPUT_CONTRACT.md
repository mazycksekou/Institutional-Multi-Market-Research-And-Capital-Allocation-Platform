# Complete Model Output Contract

| Product lane | Market output metrics | Backtest validation metrics | All output metrics | Sample metrics |
|---|---:|---:|---:|---|
| Sports | 25 | 33 | 58 | `expected_value`, `expected_closing_edge`, `clv_implied_probability`, `kelly_fraction`, `risk_of_ruin`, `closing_line_value` |
| Stocks / 0DTE | 21 | 33 | 54 | `execution_cost_ratio`, `fill_probability`, `adverse_selection_rate`, `gamma_regime_pnl`, `theta_decay_capture`, `delta_exposure_pnl` |
| Predictions | 19 | 33 | 52 | `brier_score`, `log_loss`, `calibration_error`, `liquidity_elasticity`, `probability_edge`, `settlement_risk_flag` |

## Contract summary

- Sports outputs emphasize edge, CLV, bankroll, and backtest validation.
- Stocks / 0DTE outputs emphasize execution cost, volatility capture, and gamma/theta/vega behavior.
- Prediction market outputs emphasize calibration, liquidity elasticity, arbitration windows, and settlement risk.

## Canonical owner

`src.data.model_data_field_catalog` owns the output metric catalog, while `src.services.streamlit_dashboard_data` and `src.analytics` consume it for display and reporting.
