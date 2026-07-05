# PHASE 10K8ZHV Analytics Downstream Redirection

## Scope
This batch redirects the safest downstream analytics consumer to canonical `src.analytics` ownership.

## Canonical ownership
- `src.analytics` owns deterministic reporting, attribution, calibration, governance, and model-evaluation summaries.
- `model_governance/governance_health.py` now delegates its summary composition to `src.analytics.governance.build_governance_health`.
- `model_governance/governance_report.py` and `model_governance/model_validation_report.py` remain compatibility wrappers over canonical analytics helpers.

## What changed
- `model_governance/governance_health.py` no longer owns the summary composition logic.
- Local file scanning stays local-only and unchanged in behavior.
- Canonical helpers now build the health payload, while the legacy module preserves the public import path.

## Compatibility and safety
- No live API calls were introduced.
- No credential reads were introduced.
- No connector imports were introduced.
- No enforcement or gating behavior moved out of `model_governance`.

## Remaining blockers
- `model_governance` enforcement and gate modules remain preserved for later proof.
- Compatibility tests still reference legacy wrappers, so deletion is not attempted here.

## Next step
Redirect the remaining safe research descriptor consumers, then revisit wrapper deletion after proof.
