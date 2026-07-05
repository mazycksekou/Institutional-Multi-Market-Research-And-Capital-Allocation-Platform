# Service Layer Function Inventory After 10K8ZHB

## Canonical Service Functions

- `src/services/decision_engine.py`
  - `build_decision_context`
  - `evaluate_decision`
  - `build_decision_summary`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/enrichment_service.py`
  - `EnrichmentService.enrich_ticket`
  - `EnrichmentService.enrich_ticket_async`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/action_betting_service.py`
  - `ActionBettingService`
  - `analyze_betting_event_pipeline`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/bet_csv_service.py`
  - `_stringify`
  - `_read_existing`
  - `append_bet`
  - `_float_from`
  - `summarize_bets`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/model_backtest_service.py`
  - `sports_master_db_path`
  - `run_model_backtest`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/odds_runtime_bridge.py`
  - `SharpSportsbookAdapter`
  - `enrich_with_sharp`
  - `get_sportsbook_snapshot`
  - `normalize_sportsbook_snapshot`
  - `validate_sportsbook_snapshot`
  - `get_valid_normalized_records`
  - `write_sportsbook_snapshot`
  - `summarize_sportsbook_snapshot`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

- `src/services/prediction_market_runtime_bridge.py`
  - `PredictionMarketReadonlyAdapter`
  - `enrich_with_kalshi`
  - `enrich_with_prediction_market`
  - `get_prediction_market_snapshot`
  - `normalize_prediction_market_snapshot`
  - `validate_prediction_market_snapshot`
  - `write_prediction_market_snapshot`
  - `summarize_prediction_market_snapshot`
  - Classification: `SERVICE_ORCHESTRATION_OWNER`

## Compatibility Shells

- `screenshot_intake.py`
  - `parse_ticket`
  - `analyze_screenshot_ticket`
  - `_cleanup_confirmed_selection_no_bets`
  - Classification: `COMPATIBILITY_SHIM_CANDIDATE`

- `bet_log.py`
  - `create_bet_log_entry`
  - `append_bet_log_entry`
  - `read_bet_log_entries`
  - `update_bet_result`
  - `get_performance_summary`
  - `get_bankroll_summary`
  - `get_clv_report`
  - Classification: `COMPATIBILITY_SHIM_CANDIDATE`

- `bet_decision_engine.py`
  - `evaluate_lines_payload`
  - `decision_label`
  - `risk_grade_from_kelly`
  - `kelly_fraction_multiplier`
  - `no_vig_probability_for_line`
  - Classification: `COMPATIBILITY_SHIM_CANDIDATE`

## Misplacement Check

- No remaining canonical service module is directly implementing pricing, probability, risk, or portfolio math.
- Any future pure math cleanup belongs in `src/core`, not in `src/services`.
- Any future screenshot workflow cleanup belongs in `src/services/screenshot_workflow.py`.

## Ownership Note
The service layer is now mostly orchestration, bridge management, and local storage shell work. No live execution is authorized here.
