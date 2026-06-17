# Paper-Only Fixture Testing Contract

## Executive Summary

Phase 10K8B is review-only. It defines the paper-only fixture testing contract for later 10K8 implementation without starting prediction testing, adding connectors, changing UI, or writing database rows.

The current implementation reviewed in 10K8B stays bounded as a `Controlled Navigation Shell` with a local `readiness display preview`. It keeps `no prediction testing`, `no live connectors`, `no API calls`, and `no database writes` in place.

This contract builds on the `Paper-Only Prediction Testing Owner Scan`, the `10K8 Prediction Testing Entry Contract`, and the `Full Suite Readiness Gate Matrix` while preserving `source-text guardrails` and the `no temporary git shim` boundary.

## Existing Owner Rule

The existing owner rule is to reuse existing owners only, keep the work paper-only, and avoid creating duplicate owners.

That means the contract may accept an existing owner for later local fixture-backed testing, or defer/reject it if it is only evidence, shell, or control-plane state.

## Fixture Testing Scope

The allowed scope is future work only:

- paper-only prediction testing
- local fixture-backed testing
- source-text guardrails
- readiness display evidence
- no live money
- no production execution

## Fixture Field Contract

The shared fixture contract uses the following fields:

- `fixture_id`
- `sport_or_market`
- `event_id`
- `prediction_target`
- `selection`
- `model_probability`
- `market_odds_american`
- `implied_probability`
- `expected_value`
- `stake_units`
- `bankroll_snapshot`
- `result_label`
- `outcome_known`
- `rows_tested`
- `rows_valid`
- `rows_invalid`
- `missing_field_reasons`
- `warning_reasons`
- `source_type`
- `execution_mode`

These fields are the paper-only bridge between fixture rows, readiness evidence, and later execution-adjacent review logic.

## Sports Fixture Contract

Accepted future implementation owners:

- `quant_engine.py`
- `risk_engine.py`
- `src/core/math_utils.py`
- `src/core/opportunity_scanner.py`

Fixture contract notes:

- Sports fixtures can derive `model_probability`, `market_odds_american`, `implied_probability`, `expected_value`, and `stake_units`.
- Sports fixtures can carry `bankroll_snapshot`, `result_label`, and `outcome_known` for paper review.
- Sports fixtures remain paper-only prediction testing and local fixture-backed testing only.

## 0DTE Options Fixture Contract

Accepted future implementation owners:

- `research/market_research_schema.py`
- `research/market_research_store.py`
- `quant_engine.py`
- `risk_engine.py`

Fixture contract notes:

- 0DTE fixtures stay contract-level and paper-only.
- 0DTE fixtures may carry `fixture_id`, `event_id`, `prediction_target`, `selection`, `model_probability`, `market_odds_american`, `implied_probability`, and `expected_value`.
- 0DTE fixtures do not authorize live money or production execution.

## Prediction Markets Fixture Contract

Accepted future implementation owners:

- `automation_scheduler/prediction_market_outcome_candidates.py`
- `research/market_research_schema.py`
- `research/market_research_store.py`

Deferred owners:

- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/review_queue.py`

Fixture contract notes:

- Prediction-market fixtures must stay local and paper-only.
- Prediction-market fixtures may use `source_type` and `execution_mode` to distinguish fixture-backed review from any later execution path.
- Prediction-market fixtures remain evidence only until explicit approval.

## Backtest Lab Contract

Accepted future implementation owners:

- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/experiment_history_store.py`

Fixture contract notes:

- Backtest fixtures can supply normalized rows that support `rows_tested`, `rows_valid`, and `rows_invalid`.
- Backtest fixtures can carry `missing_field_reasons` and `warning_reasons` for source-text guardrails.
- Backtest fixtures remain local fixture-backed testing only.

## Model Diagnostics Contract

Accepted future implementation owners:

- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/experiment_report_exporter.py`
- `automation_scheduler/experiment_history_store.py`

Fixture contract notes:

- Model diagnostics fixtures are read-only evidence.
- Diagnostics may report `result_label`, `outcome_known`, and `bankroll_snapshot` for review only.
- Diagnostics do not enable production execution.

## Arbitrage Lab Contract

Accepted future implementation owners:

- `automation_scheduler/arbitrage/two_way_arbitrage.py`
- `automation_scheduler/arbitrage/three_way_arbitrage.py`
- `src/core/opportunity_scanner.py`
- `src/core/math_utils.py`

Fixture contract notes:

- Arbitrage fixtures may use `fixture_id`, `sport_or_market`, `selection`, `market_odds_american`, `implied_probability`, and `expected_value`.
- Arbitrage fixtures remain paper-only prediction testing with no live money.
- Arbitrage fixtures do not add live connectors or production order routing.

## Readiness Display Evidence

Accepted future implementation owners:

- `READINESS_DISPLAY_FIELDS`
- `build_readiness_display_contract`
- `build_readiness_display_payload`
- `build_readiness_display_rows`

Evidence requirements:

- `Controlled Navigation Shell`
- `readiness display preview`
- `readiness display`
- `rows_tested`
- `rows_valid`
- `rows_invalid`
- `missing_field_reasons`
- `warning_reasons`
- `validity check only`
- `user threshold review-only`
- `low backend gate`

## Accepted Future Implementation Owners

- Data Warehouse
- `quant_engine.py`
- `risk_engine.py`
- `src/core/math_utils.py`
- `src/core/opportunity_scanner.py`
- `research/market_research_schema.py`
- `research/market_research_store.py`
- `automation_scheduler/prediction_market_outcome_candidates.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/experiment_report_exporter.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/arbitrage/two_way_arbitrage.py`
- `automation_scheduler/arbitrage/three_way_arbitrage.py`
- `READINESS_DISPLAY_FIELDS`
- `build_readiness_display_contract`
- `build_readiness_display_payload`
- `build_readiness_display_rows`

## Deferred Owners

- Streamlit shell
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/review_queue.py`
- `streamlit_app.py`
- `automation_scheduler.streamlit_dashboard_data.py`
- `Controlled Navigation Shell`
- `readiness display preview`

These remain deferred because they are shell, control-plane, or evidence surfaces rather than execution owners.

## Paper-Only Boundary

paper-only prediction testing

This phase only defines later fixture-backed review behavior. It does not start prediction testing.

## Fixture-Backed Boundary

local fixture-backed testing

This phase only describes future fixture use. It does not add live connectors, real API pulls, or production order flow.

## Prediction Testing Boundary

no prediction testing

This phase does not start prediction testing.

## Connector Boundary

no live connectors

This phase does not add vendor connectors, scraper actions, or live data wiring.

## API Boundary

no API calls

This phase does not add API actions or remote calls.

## Database Write Boundary

no database writes

This phase does not write warehouse rows, runtime rows, or dashboard rows.

## Next Phase Recommendation

Proceed to 10K8 only with the accepted fixture-backed owners, the existing owner rule, and the preserved source-text guardrails.

no prediction testing started in 10K8B
no duplicate owner created
no temporary git shim
implementation reviewed in 10K8B.
