# Feature Usage By Market

| Product lane | Feature groups | Output groups | Primary consumers |
|---|---|---|---|
| Sports | core_event, line_core, line_movement, settlement, team_stats, player_stats, projection_control | market_output_metrics, core_backtest_validation_metrics | `streamlit_app.py`, `src.services.streamlit_dashboard_data`, `src.backtesting` |
| Stocks / 0DTE | technical / macro / volatility / risk groups | market_output_metrics, core_backtest_validation_metrics | `streamlit_app.py`, `src.services.streamlit_dashboard_data`, `src.backtesting` |
| Predictions | core_event, line_core, settlement, projection_control | market_output_metrics, core_backtest_validation_metrics | `streamlit_app.py`, `src.services.streamlit_dashboard_data`, `src.backtesting` |

## Market-specific feature notes

- Sports uses the richest field coverage because it mixes team, player, and line movement features.
- Prediction markets share the cleanest backtest boundary because settlement is explicit.
- Stocks / 0DTE rely heavily on volatility, spread, and execution-cost metrics.
