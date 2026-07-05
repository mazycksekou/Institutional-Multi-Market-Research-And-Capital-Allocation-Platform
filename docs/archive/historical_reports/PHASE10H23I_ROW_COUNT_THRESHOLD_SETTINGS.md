# Phase 10H23I – Row Count Threshold Settings

## Summary

- Backend readiness remains low; testing is not blocked by sample size.
- "Data Validity Check" protects against broken rows.
- User Row Threshold is a review setting only.
- The dashboard shows rows tested versus the user's selected threshold.
- The threshold does not automatically define quality or production readiness.
- No named readiness modes were added (no "Exploratory", "Standard", "Strict", "Production Grade", "Great Run").
- No connector, scraper, model math, bankroll math, or schema changes were made.
- `Phase 10H24` remains blocked until UI review is complete.

## Files Changed

1. **automation_scheduler/feature_ablation_lab.py**
   - `apply_field_ablation` accepts optional `user_row_threshold` (default `1`).
   - Returns metadata fields: `rows_tested`, `rows_needed_before_trust`, `row_threshold_met`, `row_threshold_note`, `user_row_threshold`.
   - `run_feature_ablation_lab` accepts `user_row_threshold` and passes it to `apply_field_ablation`.
   - Final result dict includes the same row‑count threshold metadata.

2. **streamlit_app.py**
   - Sidebar checkbox relabeled to **Data Validity Check** with updated help text.
   - Readiness Filter expander no longer mentions "Require core fields" as a block; uses the Data Validity Check description.
   - Added **Rows needed before I trust this result** number input inside the Feature Ablation Lab page.
   - Both baseline and normal ablation calls pass the user‑entered threshold.
   - Run Summary shows **User Row Threshold**, **Row Threshold Met**, and the threshold note.

3. **tests/test_feature_ablation_lab.py**
   - Four new test cases verify:
     - Default threshold does not block a single‑row run.
     - Threshold met when rows ≥ threshold.
     - Threshold not met when rows < threshold (still includes sport).
     - Empty rows produce `no rows` reason regardless of threshold.

4. **tests/test_streamlit_dashboard_data.py**
   - Added source‑text checks for:
     - "Data Validity Check" and its helper.
     - "Rows needed before I trust this result".
     - Personal review threshold note.
     - "User Row Threshold", "Row Threshold Met", "selected by user".
     - Below‑threshold warning.
     - Absence of named readiness modes.

5. **PHASE10H23I_ROW_COUNT_THRESHOLD_SETTINGS.md** (this file)
   - Documentation of the change.

## Backward Compatibility

- All existing tests pass.
- True Code Baseline and other run types are unaffected.
- The `_last_ablation_result` session_state guard is preserved.
- Main menu unchanged.
- No vendor connectors, API calls, or scraper logic were added.
