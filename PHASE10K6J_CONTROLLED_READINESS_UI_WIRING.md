# Controlled Readiness UI Wiring

## Executive Summary
This is the 10K6J Controlled Readiness UI Wiring phase.

It wires `streamlit_app.py` to the existing readiness helpers in `automation_scheduler.streamlit_dashboard_data` so the controlled shell labels can show a readiness display preview without turning on execution paths.

The UI remains shell-only, with no prediction testing, no live connectors, no API calls, and no database writes.

## UI Wiring Added
The controlled navigation shell now shows a readiness display preview for:

- Sports
- 0DTE Options
- Prediction Markets
- Data Warehouse
- Backtest Lab
- Model Diagnostics
- Arbitrage Lab

The preview is generic and local-only.

## Existing Helper Usage
This phase reuses `build_readiness_display_payload` and `build_readiness_display_rows` from `automation_scheduler.streamlit_dashboard_data`.

The display path stays aligned with the existing readiness display contract.

## Controlled Shell Pages Covered
The controlled shell preview covers:

- Sports
- 0DTE Options
- Prediction Markets
- Data Warehouse
- Backtest Lab
- Model Diagnostics
- Arbitrage Lab

The existing shell labels remain:

- Feature Ablation Lab
- Bankroll Settings
- Instructions

## Readiness Display Boundary
The shell shows a readiness display preview only.

It remains a shell-only readiness display preview, not an operator execution surface.

## Prediction Testing Boundary
no prediction testing is enabled.

The wiring does not add model tests, backtest execution, or decision-scoring actions.

## Live Connector Boundary
no live connectors are enabled.

The wiring does not add vendor pulls, scrapers, or API actions.

## Database Write Boundary
no API calls and no database writes are added.

The wiring is read-only.

## Guardrails Preserved
user threshold review-only

validity check only

do not label quality automatically

do not hide valid results because sample size is low

connector guardrails remain active.

## Test Plan
The regression test checks the report text and verifies the `streamlit_app.py` source contains the helper usage, shell labels, and guardrail text.

It also checks that no separate frontend page files added.
no frontend page files added.

## Next Phase Recommendation
implementation controlled in 10K6J.

The next phase should only expand the shell if the UI scope is explicitly approved and the guardrails stay intact.
