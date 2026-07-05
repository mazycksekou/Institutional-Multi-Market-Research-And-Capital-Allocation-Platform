# 10K8 Prediction Testing Entry Contract

## Executive Summary

Phase 10K7D is review-only. It defines the 10K8 prediction testing entry contract without starting prediction testing, adding connectors, changing UI, or writing database rows.

The current implementation reviewed in 10K7D stays bounded as a `Controlled Navigation Shell` with a local `readiness display preview`. It keeps `no prediction testing`, `no live connectors`, `no API calls`, and `no database writes` in place.

This contract builds on the `Full Suite Readiness Ownership Map` and the `Full Suite Readiness Gate Matrix` while preserving the stabilized source-text guardrail and the `no temporary git shim` boundary.

## 10K8 Scope

The allowed 10K8 work is future work only:

- paper-only prediction testing
- local fixture-backed testing
- source-text guardrails
- readiness display evidence
- no live money
- no production execution

## Sports Prediction Testing Entry

- Current owner: `automation_scheduler.historical_odds_sqlite` and `automation_scheduler.historical_line_movement`
- Current status: sports readiness remains review-only
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing source rows, missing row counts, unresolved readiness warnings
- Prediction testing disabled: yes

## 0DTE Options Prediction Testing Entry

- Current owner: `research.market_research_schema` and `research.market_research_store`
- Current status: 0DTE warehouse support remains review-only
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing `raw_option_chains`, `raw_option_quotes`, `features_0dte_options`, or `option_backtest_trades`
- Prediction testing disabled: yes

## Prediction Markets Testing Entry

- Current owner: `automation_scheduler.calibration_collector` and `automation_scheduler.review_queue`
- Current status: prediction-market readiness remains review-only
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing evidence, unsupported source identity, unresolved queue warnings
- Prediction testing disabled: yes

## Backtest Lab Entry

- Current owner: `automation_scheduler.backtest_dataset_builder`, `automation_scheduler.backtesting_engine`, `automation_scheduler.experiment_history_store`
- Current status: backtest lab artifacts remain read-only
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing artifacts or unreviewed summary gaps
- Prediction testing disabled: yes

## Model Diagnostics Entry

- Current owner: `automation_scheduler.model_performance_report`, `automation_scheduler.experiment_report_exporter`, `automation_scheduler.experiment_history_store`
- Current status: model diagnostics remain review artifacts
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing export fields or unresolved quality warnings
- Prediction testing disabled: yes

## Arbitrage Lab Entry

- Current owner: `automation_scheduler.arbitrage.two_way_arbitrage`, `automation_scheduler.arbitrage.three_way_arbitrage`, `automation_scheduler.prediction_market_outcome_candidates`
- Current status: arbitrage lab remains review-only
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: unsupported arbitrage inputs or unresolved spread checks
- Prediction testing disabled: yes

## Data Warehouse Entry

- Current owner: `research.market_research_schema` and `research.market_research_store`
- Current status: the warehouse remains the canonical storage owner
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: schema mismatch or missing review coverage
- Prediction testing disabled: yes

## Streamlit Shell Entry

- Current owner: `streamlit_app.py` and `automation_scheduler.streamlit_dashboard_data`
- Current status: `Controlled Navigation Shell`
- Streamlit shell remains read-only.
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: any expansion beyond `readiness display preview`
- Prediction testing disabled: yes

## Readiness Display Entry

- Current owner: `automation_scheduler.streamlit_dashboard_data.READINESS_DISPLAY_FIELDS`, `build_readiness_display_contract`, `build_readiness_display_payload`, `build_readiness_display_rows`
- Current status: readiness display preview remains the review surface
- Required readiness display fields: `READINESS_DISPLAY_FIELDS`, `row counts`, `rows tested`, `rows valid`, `rows invalid`, `missing field reasons`, `warning reasons`
- Review-only threshold policy: `user threshold review-only`
- Backend validity policy: `validity check only; low backend gate`
- Blocking conditions before 10K8 execution: missing display fields or policy mismatch
- Prediction testing disabled: yes

## Allowed 10K8 Work

Allowed 10K8 work is future work only:

- paper-only prediction testing
- local fixture-backed testing
- source-text guardrails
- readiness display evidence
- no live money
- no production execution

## Forbidden 10K8 Work Until Explicit Approval

- live vendor connectors
- real API pulls
- database writes
- production betting
- production order routing
- automatic quality labels
- hiding valid results because sample size is low
- duplicate owners

## Required Evidence Before 10K8 Execution

- `Full Suite Readiness Ownership Map`
- `Full Suite Readiness Gate Matrix`
- `READINESS_DISPLAY_FIELDS`
- `build_readiness_display_contract`
- `build_readiness_display_payload`
- `build_readiness_display_rows`
- `readiness display preview`
- `Controlled Navigation Shell`
- `validity check only`
- `user threshold review-only`
- `low backend gate`
- `row counts`
- `rows tested`
- `rows valid`
- `rows invalid`
- `missing field reasons`
- `warning reasons`

## Prediction Testing Boundary

no prediction testing

This phase does not start prediction testing. `no prediction testing started in 10K7D`.

## Connector Boundary

no live connectors

This phase does not add live vendor connectors, scraper actions, or live data wiring.

## API Boundary

no API calls

This phase does not add API actions or remote calls.

## Database Write Boundary

no database writes

This phase does not write warehouse rows, runtime rows, or dashboard rows.

## Next Phase Recommendation

Proceed to 10K8 only after the readiness display evidence remains review-only, the shell stays bounded, and the entry contract remains aligned with the stabilized guardrails.

no duplicate owner created
no temporary git shim
implementation reviewed in 10K7D.

