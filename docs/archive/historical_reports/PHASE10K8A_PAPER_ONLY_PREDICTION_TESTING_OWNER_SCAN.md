# Paper-Only Prediction Testing Owner Scan

## Executive Summary

Phase 10K8A is review-only. It scans existing owners for later paper-only prediction testing without starting prediction testing, adding connectors, changing UI, or writing database rows.

The current implementation reviewed in 10K8A stays bounded as a `Controlled Navigation Shell` with a local `readiness display preview`. It keeps `no prediction testing`, `no live connectors`, `no API calls`, and `no database writes` in place.

This scan uses the `Full Suite Readiness Ownership Map`, the `Full Suite Readiness Gate Matrix`, and the 10K8 prediction testing entry contract as source-text guardrails. It also keeps the `no temporary git shim` boundary explicit.

## Existing Owner Rule

The existing owner rule is simple: reuse existing owners only, and keep the work paper-only.

That means the scan may accept an existing owner for later paper-only prediction testing, or defer/reject it if it is only a control-plane artifact, a shell surface, or a readiness evidence helper.

## Sports Owner Candidates

Current candidates:

- `quant_engine.py` - accepted for later paper-only testing because it is math-only and already supports odds, Kelly, and bankroll helpers.
- `risk_engine.py` - accepted for later paper-only testing because it is stateless risk sizing and bankroll control.
- `src/core/math_utils.py` - accepted for later paper-only testing because it is the canonical odds and Kelly math layer.
- `src/core/opportunity_scanner.py` - accepted for later paper-only testing because it is a pure scanner and does not require live money or production execution.

Decision:

- accepted
- paper-only prediction testing
- local fixture-backed testing
- source-text guardrails
- readiness display evidence

## 0DTE Options Owner Candidates

Current candidates:

- `research/market_research_schema.py` - deferred because it is schema ownership, not an execution owner.
- `research/market_research_store.py` - deferred because it is storage ownership, not a prediction-testing owner yet.

Decision:

- deferred until 0DTE fixture coverage is explicitly added
- no live money
- no production execution

## Prediction Markets Owner Candidates

Current candidates:

- `automation_scheduler/calibration_collector.py` - deferred because it is a control-plane collector, not a paper-only testing harness.
- `automation_scheduler/review_queue.py` - deferred because it is review-state ownership, not a prediction-testing owner.
- `automation_scheduler/prediction_market_outcome_candidates.py` - accepted for later paper-only fixture-backed testing because it already evaluates prediction-market records without adding connectors.

Decision:

- mixed, with one accepted candidate and two deferred control-plane owners

## Backtest Lab Owner Candidates

Current candidates:

- `automation_scheduler/backtest_dataset_builder.py` - accepted for later paper-only testing because it builds normalized backtest fixtures.
- `automation_scheduler/backtesting_engine.py` - accepted for later paper-only testing because it replays historical rows and computes paper outputs.
- `automation_scheduler/experiment_history_store.py` - accepted for later paper-only testing because it persists reviewable experiment history.

Decision:

- accepted
- local fixture-backed testing
- source-text guardrails

## Model Diagnostics Owner Candidates

Current candidates:

- `automation_scheduler/model_performance_report.py` - accepted for later paper-only testing because it writes reviewable performance reports.
- `automation_scheduler/experiment_report_exporter.py` - accepted for later paper-only testing because it exports offline review packs.

Decision:

- accepted
- readiness display evidence
- no live money

## Arbitrage Lab Owner Candidates

Current candidates:

- `automation_scheduler/arbitrage/two_way_arbitrage.py` - accepted for later paper-only testing because it is a pure arbitrage wrapper.
- `automation_scheduler/arbitrage/three_way_arbitrage.py` - accepted for later paper-only testing because it is a pure multi-leg arbitrage wrapper.
- `src/core/opportunity_scanner.py` - accepted for later paper-only testing because it is the shared scanner logic.
- `automation_scheduler/prediction_market_outcome_candidates.py` - accepted for later paper-only testing only as a fixture-backed evidence source.

Decision:

- accepted
- paper-only prediction testing
- local fixture-backed testing

## Data Warehouse Owner Candidates

Current candidates:

- `research/market_research_schema.py` - accepted because it is the canonical schema owner.
- `research/market_research_store.py` - accepted because it is the canonical storage owner.

Decision:

- accepted
- readiness display evidence
- no database writes

## Streamlit Shell Owner Candidates

Current candidates:

- `streamlit_app.py` - deferred because the shell is a review surface, not a prediction-testing owner.
- `automation_scheduler.streamlit_dashboard_data.py` - deferred because it supplies readiness evidence helpers, not execution.

The Streamlit shell remains evidence-only.

Decision:

- deferred
- `Controlled Navigation Shell`
- `readiness display preview`
- no prediction testing started in 10K8A

## Readiness Display Owner Candidates

Current candidates:

- `READINESS_DISPLAY_FIELDS` - deferred as evidence-only contract state.
- `build_readiness_display_contract` - deferred as evidence-only policy builder.
- `build_readiness_display_payload` - deferred as evidence-only payload builder.
- `build_readiness_display_rows` - deferred as evidence-only row builder.

Decision:

- deferred as readiness display evidence only
- `validity check only`
- `user threshold review-only`
- `low backend gate`

## Accepted Owners for Later 10K8 Work

- `quant_engine.py`
- `risk_engine.py`
- `src/core/math_utils.py`
- `src/core/opportunity_scanner.py`
- `automation_scheduler/prediction_market_outcome_candidates.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/experiment_history_store.py`
- `automation_scheduler/model_performance_report.py`
- `automation_scheduler/experiment_report_exporter.py`
- `automation_scheduler/arbitrage/two_way_arbitrage.py`
- `automation_scheduler/arbitrage/three_way_arbitrage.py`
- `research/market_research_schema.py`
- `research/market_research_store.py`

## Rejected or Deferred Owners

- `automation_scheduler/calibration_collector.py` - deferred because it is a collector control-plane owner.
- `automation_scheduler/review_queue.py` - deferred because it is queue state, not prediction testing execution.
- `streamlit_app.py` - deferred because it is the `Controlled Navigation Shell`.
- `automation_scheduler.streamlit_dashboard_data.py` - deferred because it is readiness evidence infrastructure.
- `READINESS_DISPLAY_FIELDS` - deferred because it is evidence-only.
- `build_readiness_display_contract` - deferred because it is evidence-only.
- `build_readiness_display_payload` - deferred because it is evidence-only.
- `build_readiness_display_rows` - deferred because it is evidence-only.
- `research/market_research_schema.py` and `research/market_research_store.py` for 0DTE execution - deferred until fixture coverage is explicitly added.

## Paper-Only Boundary

paper-only prediction testing

This phase only permits later paper-only testing, local fixture-backed testing, and source-text guardrails.

## Fixture-Backed Boundary

local fixture-backed testing

This phase does not add live connectors, real API pulls, or production order flow.

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

Proceed to 10K8 only with the accepted paper-only owners, the existing owner rule, and the stabilized source-text guardrails intact.

no duplicate owner created
no temporary git shim
implementation reviewed in 10K8A.
