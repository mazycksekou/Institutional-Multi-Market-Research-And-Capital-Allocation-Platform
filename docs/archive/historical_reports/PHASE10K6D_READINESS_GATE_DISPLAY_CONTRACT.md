# Readiness Gate Display Contract

## Executive Summary
This is the 10K6D readiness gate display contract. It defines how future readiness output should be displayed later without changing the UI yet.

Current Streamlit main menu remains unchanged and still contains Feature Ablation Lab, Bankroll Settings, and Instructions.

This phase is a low backend gate contract only. It uses validity check only behavior, user threshold review-only semantics, row counts, rows tested, rows valid, rows invalid, missing field reasons, and warning reasons. It must do not label quality automatically and do not hide valid results because sample size is low.

no prediction testing, no live connectors, and no frontend pages added.

## Readiness Gate Display Contract
The readiness gate display contract applies to Sports, 0DTE Options, Prediction Markets, Data Warehouse, Backtest Lab, Model Diagnostics, and Arbitrage Lab.

The display behavior should show review context rather than automatic judgment. The backend gate is validity check only, while user threshold review-only stays a human review signal.

## Cross-Market Display Fields
Every future readiness panel should show:

- market name
- data source name
- validation status
- row counts
- rows tested
- rows valid
- rows invalid
- missing field reasons
- warning reasons
- user threshold value
- whether user threshold was met
- clear text that threshold is review-only
- clear text that validity is the backend gate
- clear text that low sample size does not hide valid results
- clear text that quality is not automatically labeled

## Sports Readiness Display
Sports should show the same readiness gate fields and should surface row counts, rows tested, rows valid, rows invalid, missing field reasons, and warning reasons alongside the threshold status.

## 0DTE Options Readiness Display
0DTE Options should show the same readiness gate fields and should make the validity check only path visible without implying automatic quality labeling.

## Prediction Markets Readiness Display
Prediction Markets should show the same readiness gate fields and should keep user threshold review-only messaging separate from backend validity status.

## Data Warehouse Readiness Display
Data Warehouse should show the same readiness gate fields and should present read-only warehouse state without implying live connectors or automatic data quality scoring.

## Backtest Lab Readiness Display
Backtest Lab should show the same readiness gate fields and should display whether the run met the user threshold while keeping the low backend gate explicit.

## Model Diagnostics Readiness Display
Model Diagnostics should show the same readiness gate fields and should expose missing field reasons and warning reasons as review-only diagnostics.

## Arbitrage Lab Readiness Display
Arbitrage Lab should show the same readiness gate fields and should present the low backend gate contract without hiding valid rows because sample size is low.

## User Threshold Boundary
The user threshold is review-only. It is a display-time signal, not an automatic gate that blocks valid results.

## Prediction Testing Boundary
no prediction testing is permitted in this phase. The contract does not add live connectors, does not add API calls, and does not create new frontend pages.

## No UI Changes Made
No frontend pages added. The current Streamlit main menu remains unchanged and still contains Feature Ablation Lab, Bankroll Settings, and Instructions.

## Next Phase Recommendation
implementation deferred beyond 10K6D. The next phase should translate this display contract into UI work only after the navigation and readiness scopes are approved.
