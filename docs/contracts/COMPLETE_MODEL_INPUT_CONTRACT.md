# Complete Model Input Contract

## Discovered model modes

| Mode | Field count | Field groups |
|---|---:|---|
| `one_sport` | 162 | `backtest_clv_output_fields`, `evaluation_output_fields`, `form_fields`, `injury_availability_fields`, `line_movement_fields`, `market_fields`, `matchup_fields`, `odds_fields`, `paper_arbitrage_output_fields`, `paper_fixture_fields`, `pipeline_output_fields`, `player_context_fields`, `readiness_output_fields`, `rest_schedule_fields`, `sport_specific_fields`, `team_context_fields`, `technical_signal_fields`, `universal_math_output_fields`, `universal_row_identity_fields`, `volatility_fields`, `weather_environment_fields` |
| `one_stock_market` | 188 | `backtest_clv_output_fields`, `earnings_calendar_fields`, `evaluation_output_fields`, `fundamentals_fields`, `line_data_fields`, `macro_context_fields`, `options_chain_fields`, `paper_arbitrage_output_fields`, `paper_fixture_fields`, `pipeline_output_fields`, `price_action_fields`, `quote_fields`, `readiness_output_fields`, `risk_fields`, `sector_context_fields`, `technical_indicator_fields`, `technical_signal_fields`, `universal_math_output_fields`, `universal_row_identity_fields`, `volatility_fields`, `volume_liquidity_fields` |
| `one_crypto_market` | 160 | `backtest_clv_output_fields`, `chain_fields`, `evaluation_output_fields`, `funding_fields`, `liquidity_fields`, `macro_context_fields`, `orderbook_fields`, `paper_arbitrage_output_fields`, `paper_fixture_fields`, `pipeline_output_fields`, `quote_fields`, `readiness_output_fields`, `risk_fields`, `sentiment_fields`, `technical_indicator_fields`, `technical_signal_fields`, `universal_math_output_fields`, `universal_row_identity_fields`, `volatility_fields` |
| `one_prediction_market` | 149 | `arbitrage_fields`, `backtest_clv_output_fields`, `contract_fields`, `evaluation_output_fields`, `event_context_fields`, `line_movement_fields`, `liquidity_fields`, `market_fields`, `orderbook_fields`, `paper_arbitrage_output_fields`, `paper_fixture_fields`, `pipeline_output_fields`, `price_probability_fields`, `readiness_output_fields`, `resolution_criteria_fields`, `risk_fields`, `settlement_fields`, `technical_signal_fields`, `universal_math_output_fields`, `universal_row_identity_fields`, `volatility_fields` |
| `one_0dte_options_trade` | 189 | `backtest_clv_output_fields`, `earnings_event_fields`, `evaluation_output_fields`, `expiration_fields`, `gex_fields`, `greeks_fields`, `intraday_context_fields`, `liquidity_execution_fields`, `liquidity_spread_fields`, `macro_context_fields`, `macro_event_fields`, `options_contract_fields`, `options_quote_fields`, `paper_arbitrage_output_fields`, `paper_fixture_fields`, `pipeline_output_fields`, `readiness_output_fields`, `risk_fields`, `strategy_fields`, `technical_signal_fields`, `underlying_identity_fields`, `underlying_line_data_fields`, `underlying_price_action_fields`, `underlying_quote_fields`, `universal_math_output_fields`, `universal_row_identity_fields`, `volatility_fields`, `volume_profile_fields` |

## Contract summary

- The canonical input contract is defined in `src.data.model_data_field_catalog`.
- Each mode is a different projection of the same underlying canonical field universe.
- The repo already models sports, stocks, crypto, prediction markets, and 0DTE separately rather than forcing one generic schema.

## Important contract rules

- `features_known_at_decision_time` is mandatory wherever decision-time leakage matters.
- Settlement and closing fields are not safe feature inputs.
- Output metrics are separate from input features and should stay in the output contract.
