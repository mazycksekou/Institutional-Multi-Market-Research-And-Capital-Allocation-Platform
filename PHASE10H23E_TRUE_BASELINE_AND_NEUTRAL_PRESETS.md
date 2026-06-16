# Phase 10H23E – True Baseline + Neutral Presets

## Summary

This phase introduces an explicit **True Code Baseline** concept for the Feature Ablation Lab and adds **None** options for Risk Preset and Regression Tactic, removing operator confusion.

## Changes

### 1. True Code Baseline

- A **True Code Baseline** run uses:
  - all safe available fields (none removed)
  - no custom feature weights
  - no regression tactic override
  - no risk preset adjustment
  - chance override forced off
  - only current‑code model path

- The baseline **may be unstable**, and the interface does not hide that fact.
- A dedicated `"Run True Code Baseline"` button sits beside the normal `"Run Ablation Lab"` button.
- Result display shows the **Baseline Type** label (`True Code Baseline`) and includes `risk_preset`, `regression_tactic`, `chance_override` and `custom_weights` fields.

### 2. Risk Preset None

- A `"None - no risk preset adjustment"` entry now appears first in the Risk Preset selectbox.
- When selected, no risk preset logic is applied; the model uses its base stake/risk behavior.
- The Bankroll Settings table includes this option as the first row.
- A UI note explains that risk preset affects stake sizing only, not feature usefulness.

### 3. Regression Tactic None

- A `"None - no regression tactic"` entry appears first in the Regression Tactic selectbox.
- When selected, no regression tactic is applied; the run uses the current model probability as coded.
- The `"Let tactic replace old model chance"` checkbox is forced to `False` when the tactic is `None`.
- UI text explains that `None` means no regression tactic is applied.

### 4. Baseline vs Ablation Labeling

- The result area now shows:
  - `Run Type` (True Code Baseline or Ablation Test)
  - `Baseline Type`
  - `Risk Preset`
  - `Regression Tactic`
  - `Chance Override`
  - `Custom Weights Applied`
- A plain‑English note: *Compare ablation runs against True Code Baseline before trusting improvements.*

### 5. Backend Metadata

- `run_feature_ablation_lab` in `feature_ablation_lab.py` now attaches fields:
  - `run_type`, `baseline_type`, `risk_preset_used`, `regression_tactic_used`, `chance_override_used`, `custom_weights_used`, `true_baseline_mode`, `baseline_warning`
- When a call has zero removed fields, no custom weights, no tactic, and no risk preset, it is automatically marked as `true_code_baseline`.

### 6. Tests

- **`tests/test_feature_ablation_lab.py`** now contains tests verifying:
  - True baseline uses all safe fields.
  - True baseline has zero removed fields.
  - True baseline reports `risk_preset_used` as `None`.
  - True baseline reports `regression_tactic_used` as `None`.
  - True baseline reports `custom_weights_used` as `False`.
  - True baseline reports `chance_override_used` as `False`.
  - Removing a field changes the run type to `ablation_test`.
- **`tests/test_streamlit_dashboard_data.py`** now contains source‑text tests verifying the required UI strings are present and forbidden connector text is absent.

### 7. No New Connectors

No vendor APIs, scrapers, synthetic data pipelines, or paid data controls were added. Phase 10H24 remains blocked until baseline behavior is reviewed.

## Files Changed

- `automation_scheduler/feature_ablation_lab.py` – added Phase 10H23E metadata fields and baseline detection.
- `streamlit_app.py` – added True Code Baseline button, None presets, updated risk preset and tactic UI, updated result display.
- `tests/test_feature_ablation_lab.py` – new baseline tests.
- `tests/test_streamlit_dashboard_data.py` – added source‑text presence tests.
- `PHASE10H23E_TRUE_BASELINE_AND_NEUTRAL_PRESETS.md` – this report.
