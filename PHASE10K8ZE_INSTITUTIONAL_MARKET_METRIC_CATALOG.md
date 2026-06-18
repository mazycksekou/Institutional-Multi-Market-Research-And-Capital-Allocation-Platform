# Institutional Market Metric Catalog

## Executive Summary
The dashboard now has an institutional metric catalog for `Sports`, `Stocks / 0DTE`, and `Predictions`. Each lane exposes output metric groups plus the shared core backtest validation metrics while staying `paper-only`, `readiness only`, and `review-only`.

## Existing Owner Used
The existing owner rule is preserved in `automation_scheduler/model_data_field_catalog.py`, `automation_scheduler/streamlit_dashboard_data.py`, and `streamlit_app.py`.

## Institutional Market Metric Catalog
The institutional catalog is defined by `SPORTS_BETTING_OUTPUT_METRICS`, `ZERO_DTE_OUTPUT_METRICS`, `PREDICTION_MARKET_OUTPUT_METRICS`, and `CORE_BACKTEST_VALIDATION_METRICS`.

## Sports Output Metrics
`Sports` includes `Expected Value / EV`, `CLV`, `arbitrage`, `Kelly Growth Rate`, and `Risk of Ruin`, plus the supporting sports metrics in `SPORTS_BETTING_OUTPUT_METRICS`.

## Stocks / 0DTE Output Metrics
`Stocks / 0DTE` includes `Execution Cost Ratio`, `Fill Probability`, `Adverse Selection Rate`, `Variance Risk Premium`, `Deflated Sharpe Ratio`, `Probability of Backtest Overfitting`, `Walk-Forward Stability`, `Capacity Analysis`, and `Cost Sensitivity Analysis`, plus the supporting 0DTE metrics in `ZERO_DTE_OUTPUT_METRICS`.

## Predictions Output Metrics
`Predictions` includes `Brier Score`, `Log Loss`, `calibration`, `liquidity elasticity`, and `binary outcome risk`, plus the supporting prediction metrics in `PREDICTION_MARKET_OUTPUT_METRICS`.

## Core Backtest Validation Metrics
`CORE_BACKTEST_VALIDATION_METRICS` carries the shared institutional backtest contract for net profit, return, drawdown, expectancy, risk, overfitting checks, and capacity review.

## UI Display Contract
`build_market_metric_display_payload` and `output_metrics_for_product_lane` provide the read-only dashboard contract for displaying metric groups under each public product lane.

## Product Lane Mapping
`Sports`, `Stocks / 0DTE`, and `Predictions` are the public lanes. Legacy internal aliases remain separate compatibility values and do not change the product surface.

## Paper-Only Boundary
No live execution was added.

## Readiness-Only Boundary
No readiness claim is made without data.

## Review-Only Boundary
Do not label quality automatically.
Do not hide valid results because sample size is low.
do not label quality automatically
do not hide valid results because sample size is low

## Trade Execution Boundary
No real trade execution was added.

## Broker Boundary
No broker execution was added.

## Connector Boundary
No live connectors were added.

## API Boundary
No API calls were added.

## Database Write Boundary
No database writes were added.

## Unsupported Claim Boundary
No guaranteed profit language was added.
No assured profit language was added.
no guaranteed profit language
no assured profit language

## Guardrails Preserved
`paper-only`, `readiness only`, `review-only`, `local fixture-backed testing`, `no broker execution`, `no real trade execution`, `no live connectors`, `no API calls`, and `no database writes` remain in force.

## Test Plan
Verify the metric constants, the product-lane helper, the dashboard payload helper, and the UI captions that surface each lane’s metric groups.

## Next Phase Recommendation
Proceed to `10K8ZF Controlled Local Data Loader / Backtest Input Contract`.

## implementation reviewed in 10K8ZE
`streamlit_app.py` and the metric catalog were reviewed in 10K8ZE.
