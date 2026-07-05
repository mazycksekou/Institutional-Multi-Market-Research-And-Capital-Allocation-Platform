# Dashboard Navigation Plan Contract

## Executive Summary
This is the 10K6B dashboard navigation plan contract. It defines the future navigation structure without changing the UI yet.

Current Streamlit main menu remains unchanged and still contains Feature Ablation Lab, Bankroll Settings, and Instructions.

This is a readiness-gated plan only. It uses a low backend gate, a validity check only posture, user threshold review-only semantics, row counts, and missing field reasons. It must do not label quality automatically and do not hide valid results because sample size is low.

No prediction testing was started, no live connectors were added, and no frontend pages added.

## Current Menu Contract
The current menu contract is fixed for this phase:

- Feature Ablation Lab
- Bankroll Settings
- Instructions

These are the only current top-level entries. The future labels in this contract are planning-only and are not added to `streamlit_app.py` in this phase.

## Future Navigation Contract
The future dashboard navigation contract defines these areas:

- Sports
- 0DTE Options
- Prediction Markets
- Data Warehouse
- Backtest Lab
- Model Diagnostics
- Arbitrage Lab
- Settings / Instructions

These labels belong in the 10K6B report only. implementation deferred to 10K6C.

## Page Responsibility Map
Feature Ablation Lab remains the experimental field testing surface.

Bankroll Settings remains the operator risk and stake control surface.

Instructions remains the operator guidance and safety surface.

Sports is the future sport-scoped analysis entry point.

0DTE Options is the future options-specific analysis entry point.

Prediction Markets is the future prediction-market analysis entry point.

Data Warehouse is the future data access and warehouse inspection entry point.

Backtest Lab is the future backtest execution and review entry point.

Model Diagnostics is the future model health and debugging entry point.

Arbitrage Lab is the future cross-market opportunity inspection entry point.

Settings / Instructions is the future operator configuration and help entry point.

## Readiness Gate Display Contract
readiness gate display contract:

- low backend gate
- validity check only
- user threshold review-only
- row counts
- missing field reasons
- do not label quality automatically
- do not hide valid results because sample size is low

The display contract should present review guidance, not automatic quality judgments.

## Data Warehouse Display Contract
The Data Warehouse view is reserved for local warehouse inspection, source auditing, and read-only review of stored outputs. It should be presented as a planning label only until implementation deferred to 10K6C.

The warehouse surface must remain aligned with the current read-only contract and must not imply live connectors or live API behavior.

## Arbitrage Display Contract
The Arbitrage Lab view is reserved for future cross-market inspection and operator review. It should remain a planning label only in this phase.

The display contract for arbitrage must avoid implying automated execution, live connectors, or prediction testing.

## Prediction Testing Boundary
no prediction testing is permitted in this phase. The navigation contract does not create a testing workflow, does not wire new model pages, and does not add live connectors.

## No UI Changes Made
No frontend pages added. The current Streamlit main menu remains unchanged.

## Next Phase Recommendation
implementation deferred to 10K6C. The next phase should only translate this contract into UI work after an explicit readiness review and should preserve the current menu contract until then.
