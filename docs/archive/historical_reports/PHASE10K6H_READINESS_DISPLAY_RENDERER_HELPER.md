# Readiness Display Renderer Helper

## Executive Summary
This is the 10K6H Readiness Display Renderer Helper phase. It adds one tiny pure helper in `automation_scheduler/streamlit_dashboard_data.py` for future display use without changing the Streamlit UI.

The helper is `build_readiness_display_rows`, and it consumes `build_readiness_display_payload` output that already follows `READINESS_DISPLAY_FIELDS` and `build_readiness_display_contract`.

This keeps the low backend gate visible, preserves validity check only behavior, and keeps user threshold review-only semantics separate from backend validity.

It does not label quality automatically, does not hide valid results because sample size is low, uses no prediction testing, uses no live connectors, and adds no frontend pages.

## Existing Dashboard Data Owner
The existing dashboard data owner is `automation_scheduler/streamlit_dashboard_data.py`.

The helper stays dependency-free and centralized in that module.

## Helper Added
`build_readiness_display_rows` converts a readiness display payload into plain display rows.

Each row carries:

- `label`
- `value`
- `policy_note`

## Payload Reuse
The helper reuses `build_readiness_display_payload`.

The payload remains aligned with `READINESS_DISPLAY_FIELDS` and `build_readiness_display_contract`.

## Display Semantics
The row set covers:

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
- user threshold met
- threshold review-only
- validity is backend gate
- low sample size does not hide valid results
- quality not automatically labeled

The helper keeps the following semantics explicit:

- low backend gate
- validity check only
- user threshold review-only
- do not label quality automatically
- do not hide valid results because sample size is low

## Prediction Testing Boundary
no prediction testing is part of this phase.

There are no live connectors and no API calls here.

## No UI Changes Made
no frontend pages added.

streamlit_app.py unchanged.

The current Streamlit main menu remains unchanged.

## Next Phase Recommendation
implementation deferred beyond 10K6H.

The next phase should only wire this helper into UI work after the display scope is explicitly approved.
