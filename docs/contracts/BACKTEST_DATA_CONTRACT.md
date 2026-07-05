# Backtest Data Contract

## Required fields

- `event_id`
- `contract_id`
- `sport`
- `league`
- `market`
- `decision_time`
- `odds_at_decision_time`
- `features_known_at_decision_time`
- `model_probability`
- `market_implied_probability`
- `edge`
- `stake`
- `final_result`
- `profit_loss`
- `closing_line`
- `clv`

## Leakage fields that must stay out of model features

- `final_result`
- `winner`
- `home_score`
- `away_score`
- `profit_loss`
- `closing_odds`
- `closing_line`
- `clv`
- `result`
- `settled_result`
- `bet_result`
- `outcome`

## Backtest storage contract

- Canonical schema: `src.backtesting.backtest_schema`
- Canonical historical bridge: `src.backtesting.historical_bridge`
- Canonical dataset contract: `src.backtesting` exports
- Canonical storage path family: `data/backtests/`

## Reproducibility rules

- Capture decision-time features only.
- Preserve snapshot / replay ordering.
- Store the model version with every backtest output.
- Keep settlement and closing data for evaluation only, not for feature construction.
