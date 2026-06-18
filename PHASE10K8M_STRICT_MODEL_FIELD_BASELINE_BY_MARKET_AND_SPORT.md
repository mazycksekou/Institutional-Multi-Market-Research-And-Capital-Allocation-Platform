# Strict Model Field Baseline by Market and Sport

## Executive Summary
Phase 10K8M establishes the repo-wide model field baseline by market and sport. It keeps the universal math layer in `quant_engine.py`, removes `All Ready` as redundant from the active Streamlit mode selector, adds the dedicated 0DTE options trade mode, and wires a strict model data catalog into the UI.

## Existing Owner Used
This follows the existing owner rule: keep the new baseline inside existing control-plane owners and do not create duplicate owners.

This phase uses existing owners only:
- `automation_scheduler/technical_signal_fields.py`
- `automation_scheduler/model_data_field_catalog.py`
- `automation_scheduler/data_source_registry.py`
- `streamlit_app.py`

## Repo-Wide Field Inventory
The inventory covers Sports, Stock Market, Crypto Market, Prediction Market, and the dedicated 0DTE Options Trade lane. It also keeps the paper-only baseline visible with `paper_fixture_fields`, `readiness_output_fields`, `evaluation_output_fields`, `pipeline_output_fields`, `universal_math_output_fields`, `paper_arbitrage_output_fields`, and `backtest_clv_output_fields`.

## Shared Technical Signal Owner
`TECHNICAL_SIGNAL_FIELDS`, `TECHNICAL_SIGNAL_FIELDS_BY_MARKET`, and `technical_fields_for_market` now live in `automation_scheduler/technical_signal_fields.py`. The shared technical signal owner is deliberately limited to OHLCV, indicator, and market-participation style fields. `arbitrage stays out of TECHNICAL_SIGNAL_FIELDS`.

## Universal Math Boundary
The universal math layer stays in `quant_engine.py`. EV stays in `quant_engine.py`, edge stays in `quant_engine.py`, Kelly stays in `quant_engine.py`, implied probability stays in `quant_engine.py`, fair odds stays in `quant_engine.py`, and bankroll / confidence / no-bet logic stays there as well.

- EV stays in quant_engine.py
- edge stays in quant_engine.py
- Kelly stays in quant_engine.py
- implied probability stays in quant_engine.py
- fair odds stays in quant_engine.py

## Data Source Registry Wiring
`automation_scheduler/data_source_registry.py` now pulls `technical_fields_for_market` from `automation_scheduler/technical_signal_fields.py` and extends lane optional inputs for stocks, crypto, prediction markets, odds, and 0DTE options.

## Model Data Field Catalog
`automation_scheduler/model_data_field_catalog.py` is the UI-facing catalog owner. It exposes `SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT`, `MODEL_DATA_FIELD_GROUPS_BY_MODE`, `fields_for_model_mode`, `field_groups_for_model_mode`, and `fields_for_sport`.

## Sports Common Fields
Sports includes the shared odds, market, line movement, volatility, team context, player context, injury, rest, weather, matchup, form, sport specific, technical signal, and paper fixture groups.

## Sports By Sport Fields
`basketball_nba`, `basketball_wnba`, `basketball_ncaab`, `basketball_ncaaw`, `americanfootball_nfl`, `americanfootball_ncaaf`, `baseball_mlb`, `icehockey_nhl`, `soccer`, `tennis`, `ufc_mma`, `boxing`, and `golf` each have a sport-specific field catalog.

## Basketball Fields
Basketball catalogs include `minutes_projection`, `usage_rate`, `pace`, `offensive_rating`, `defensive_rating`, `rebound_rate`, `assist_rate`, and `three_point_rate`.

## Football Fields
Football catalogs include `quarterback_status`, `offensive_line_status`, `skill_player_availability`, `explosive_play_rate`, and `red_zone_rate`.

## Baseball Fields
Baseball catalogs include `starting_pitcher`, `bullpen_usage`, `lineup_confirmed`, `park_factor`, and `umpire_context`.

## Hockey Fields
Hockey catalogs include `starting_goalie`, `goalie_confirmed`, `expected_goals_for`, `expected_goals_against`, and `line_combinations`.

## Soccer Fields
Soccer catalogs include `draw_line`, `double_chance`, `draw_no_bet`, `expected_goals`, and `expected_lineup`.

## Tennis Fields
Tennis catalogs include `game_spread`, `set_spread`, `total_games`, `serve_hold_rate`, and `break_rate`.

## Combat Sports Fields
`ufc_mma` and `boxing` include `fighter_a`, `fighter_b`, `method_prop`, `round_prop`, `reach`, and `weight_cut_context`.

## Golf Fields
Golf includes `tournament`, `course`, `outright_price`, `strokes_gained_approach`, and `course_fit`.

## Stock Market Fields
Stock Market includes `ETF_market_data`, `earnings_call_text`, `insider_transactions`, `institutional_ownership`, `options_context`, `revenue`, `eps`, `pe_ratio`, `price_target`, `put_call_ratio`, and `term_structure`.

## Crypto Market Fields
Crypto Market includes `order_book_depth`, `funding_rates`, `dex_liquidity`, `gas_fees`, `stablecoin_flows`, `whale_activity_proxy`, `active_addresses`, `exchange_inflows`, `fear_greed_index`, and `paper_only_strategy_replay`.

## Prediction Market Fields
Prediction Markets include `contract_id`, `market_id`, `market_title`, `contract_title`, `settlement_rules`, `resolution_criteria`, `yes_price`, `no_price`, `orderbook_depth`, `equivalent_contract`, `arbitrage_gap`, and `settlement_risk`.

## Dedicated 0DTE Options Trade Mode
The dedicated 0DTE Options Trade mode exposes `underlying_identity_fields`, `options_contract_fields`, `greeks_fields`, `expiration_fields`, `liquidity_spread_fields`, and `intraday_context_fields`. `0DTE is the primary active trading lane`.

## 0DTE Primary Active Trading Lane
0DTE stays separate from generic stocks. The mode is explicit and controlled, not inferred from the old combined selector.

## Paper Arbitrage Output Fields
Paper arbitrage is a review-only output. `paper_arbitrage_percentage` records the paper arbitrage percentage within tested timeframe. Related outputs include `paper_arbitrage_window`, `paper_arbitrage_timeframe`, `paper_arbitrage_best_percentage`, `paper_arbitrage_liquidity_adjusted_percentage`, `paper_arbitrage_after_spread_percentage`, and `paper_arbitrage_after_fees_percentage`.

## Backtest CLV Output Fields
Backtest CLV review fields include `final_result`, `profit_loss`, `pnl`, `roi`, `yield`, `profit_factor`, `closing_line`, `closing_price`, `clv`, `clv_percent`, `closing_line_value`, `closing_line_value_pct`, `paper_profit_loss`, and `paper_stake`.

## All Ready Removed
All Ready removed as redundant from the active model mode selector. The UI now uses exactly:
- One Sport
- One Stock Market
- One Crypto Market
- One Prediction Market
- One 0DTE Options Trade

## Streamlit UI Wiring
`streamlit_app.py` now reads from the model data field catalog and surfaces the baseline field groups in a paper-only, readiness-only shell.

## Paper-Only Boundary
This is paper-only prediction testing support. It is paper-only prediction testing and local fixture-backed testing support only. It does not authorize live money or production execution.

## Readiness-Only Boundary
The UI remains readiness only. This is user threshold review-only and validity check only. The review threshold is user-controlled and review-only.

## Prediction Testing Boundary
No live prediction testing was started in 10K8M.

## Trade Execution Boundary
No real trade execution is added.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Guardrails Preserved
- no live connectors
- no API calls
- no database writes
- no broker execution
- no real trade execution
- no duplicate owner created
- no temporary git shim
- do not label quality automatically
- do not hide valid results because sample size is low

## Test Plan
Run the targeted baseline test, then `test`, `smoke`, and `stat` before commit.

## Next Phase Recommendation
Proceed only after the field baseline is confirmed clean. The next work can use the catalog without reintroducing `All Ready` or moving universal math out of `quant_engine.py`.

implementation reviewed in 10K8M
