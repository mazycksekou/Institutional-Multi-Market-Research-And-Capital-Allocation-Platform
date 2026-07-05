# Readiness Display Data Helper

## Executive Summary
This is the 10K6E Readiness Display Data Helper phase. It adds a tiny pure helper for future display use without changing the UI.

The existing owner is `automation_scheduler/streamlit_dashboard_data.py`, and `streamlit_app.py` remains unchanged.

This is still a low backend gate contract only. It keeps validity check only behavior, user threshold review-only semantics, row counts, rows tested, rows valid, rows invalid, missing field reasons, and warning reasons visible.

It does not label quality automatically, does not hide valid results because sample size is low, uses no prediction testing, uses no live connectors, and adds no frontend pages.

## Existing Dashboard Data Owner
The existing dashboard data owner is `automation_scheduler/streamlit_dashboard_data.py`.

The helper was added there instead of creating a new helper module so the contract stays small and dependency-free.

## Helper Added Or Reused
`READINESS_DISPLAY_FIELDS` was added in `automation_scheduler/streamlit_dashboard_data.py`.

`build_readiness_display_contract` was added in `automation_scheduler/streamlit_dashboard_data.py`.

The helper is pure data only and returns a plain dict for future UI panels.

## Readiness Display Fields
The readiness display field contract includes:

- market_name
- data_source_name
- validation_status
- row_counts
- rows_tested
- rows_valid
- rows_invalid
- missing_field_reasons
- warning_reasons
- user_threshold_value
- user_threshold_met
- threshold_review_only
- validity_is_backend_gate
- low_sample_size_does_not_hide_valid_results
- quality_not_automatically_labeled

## Backend Gate Policy
The backend gate is low backend gate behavior and validity check only.

This keeps backend validity separate from presentation-time review text.

## User Threshold Policy
The user threshold policy is user threshold review-only.

The helper treats the user threshold as a display signal, not an automatic block.

## Sample Size Policy
The sample size policy is do not hide valid results because sample size is low.

Valid results stay visible even when sample size is small.

## Quality Label Policy
The quality label policy is do not label quality automatically.

The contract avoids automatic quality labeling so future panels can present review context instead.

## Prediction Testing Boundary
`prediction_testing_enabled` is `False`.

There is no prediction testing, no live connectors, and no API calls in this phase.

## No UI Changes Made
no frontend pages added.

`streamlit_app.py` unchanged.
streamlit_app.py unchanged.

The current Streamlit main menu remains unchanged.

## Next Phase Recommendation
implementation deferred beyond 10K6E.

The next phase should wire this contract into UI work only after the display scope is explicitly approved.
