# Readiness Display Renderer Contract

## Executive Summary
This is the 10K6G Readiness Display Renderer Contract phase. It defines future renderer-only behavior for readiness display panels without implementing the renderer yet.

The existing payload owner is `automation_scheduler/streamlit_dashboard_data.py`, and the contract reuses `READINESS_DISPLAY_FIELDS`, `build_readiness_display_contract`, and `build_readiness_display_payload`.

This is future renderer only. It keeps the low backend gate visible, preserves validity check only behavior, and keeps user threshold review-only semantics separate from backend validity.

It does not label quality automatically, does not hide valid results because sample size is low, uses no prediction testing, uses no live connectors, and adds no frontend pages.

## Existing Payload Owner
The existing payload owner is `automation_scheduler/streamlit_dashboard_data.py`.

The renderer contract stays aligned with `READINESS_DISPLAY_FIELDS`, `build_readiness_display_contract`, and `build_readiness_display_payload` without changing the payload helper itself.

## Future Renderer Contract
A future renderer should display the readiness payload as a clear review panel rather than a hidden gate.

It should show:

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
- clear text that user threshold is review-only
- clear text that validity is the backend gate
- clear text that low sample size does not hide valid results
- clear text that quality is not automatically labeled

## Required Display Rows
The renderer should preserve the display rows for row counts, rows tested, rows valid, rows invalid, missing field reasons, and warning reasons.

The renderer should keep `threshold_review_only`, `validity_is_backend_gate`, `low_sample_size_does_not_hide_valid_results`, and `quality_not_automatically_labeled` visible as explicit contract rows or labels.

## Backend Gate Display Rule
The backend gate display rule is low backend gate behavior and validity check only.

The renderer should show validity as the backend gate and not as an automatic quality score.

## User Threshold Display Rule
The user threshold display rule is user threshold review-only.

The renderer should display the threshold value and whether it was met, but it should present threshold results as review context only.

## Sample Size Display Rule
The sample size display rule is do not hide valid results because sample size is low.

The renderer should not suppress valid rows when sample size is small.

## Quality Label Display Rule
The quality label display rule is do not label quality automatically.

The renderer should keep quality labeling explicit and manual rather than inferred.

## Cross-Market Renderer Scope
The renderer contract applies across Sports, 0DTE Options, Prediction Markets, Data Warehouse, Backtest Lab, Model Diagnostics, and Arbitrage Lab.

Each market should render the same readiness display fields and preserve the same display semantics.

## Prediction Testing Boundary
no prediction testing is part of this contract. The renderer contract does not add live connectors, does not add API calls, and does not create new frontend pages.

## No UI Changes Made
no frontend pages added.

streamlit_app.py unchanged.

The current Streamlit main menu remains unchanged.

## Next Phase Recommendation
implementation deferred beyond 10K6G.

The next phase should implement the renderer only after the UI surface is approved and the display scope is explicitly accepted.
