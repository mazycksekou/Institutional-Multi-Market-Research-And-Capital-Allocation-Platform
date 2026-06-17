# Readiness Display Payload Builder

## Executive Summary
This is the 10K6F Readiness Display Payload Builder phase. It adds one tiny pure helper for future readiness display use without changing the UI.

The existing owner is `automation_scheduler/streamlit_dashboard_data.py`, and `streamlit_app.py` remains unchanged.

This keeps the low backend gate contract explicit, with validity check only behavior, user threshold review-only semantics, row counts, rows tested, rows valid, rows invalid, missing field reasons, and warning reasons visible.

It does not label quality automatically, does not hide valid results because sample size is low, uses no prediction testing, uses no live connectors, and adds no frontend pages.

## Existing Dashboard Data Owner
The existing dashboard data owner is `automation_scheduler/streamlit_dashboard_data.py`.

The payload builder was added there so the readiness contract stays dependency-free and centralized.

## Helper Added
`build_readiness_display_payload` was added in `automation_scheduler/streamlit_dashboard_data.py`.

The helper returns a plain dict matching `READINESS_DISPLAY_FIELDS`.

The helper reuses `READINESS_DISPLAY_FIELDS` and stays aligned with `build_readiness_display_contract`.

## Payload Fields
The payload includes:

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

The required semantic keys are `threshold_review_only`, `validity_is_backend_gate`, `low_sample_size_does_not_hide_valid_results`, and `quality_not_automatically_labeled`.

## Backend Gate Policy
The backend gate is low backend gate behavior and validity check only.

The payload keeps validity separate from presentation-time review context.

## User Threshold Policy
The user threshold policy is user threshold review-only.

The payload preserves the threshold as a display signal instead of an automatic block.

## Sample Size Policy
The sample size policy is do not hide valid results because sample size is low.

Valid rows stay visible even when sample size is small.

## Quality Label Policy
The quality label policy is do not label quality automatically.

The helper avoids automatic quality labeling so future panels can remain review-focused.

## Prediction Testing Boundary
`prediction_testing_enabled` stays out of the payload path, and there is no prediction testing in this phase.

There are no live connectors and no API calls here.

## No UI Changes Made
no frontend pages added.

`streamlit_app.py` unchanged.
streamlit_app.py unchanged.

The current Streamlit main menu remains unchanged.

## Next Phase Recommendation
implementation deferred beyond 10K6F.

The next phase should wire this payload into UI work only after the display scope is explicitly approved.
