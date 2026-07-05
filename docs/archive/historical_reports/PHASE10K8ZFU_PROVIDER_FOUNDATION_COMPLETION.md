# PHASE10K8ZFU Provider Foundation Completion

## Executive Summary
src/providers now owns provider foundations. This phase does not migrate runtime provider logic, does not delete legacy provider modules, and does not change production behavior.

We generalize vendor-specific adapter contracts into vendor-neutral contracts.
The remaining vendor-specific adapter contracts were generalized into vendor-neutral, product-category surfaces for prediction markets, 0DTE/stocks, and sportsbooks. Legacy wrappers remain in place for compatibility.

## Files Reviewed
- `src/providers/contracts.py`
- `src/providers/validation.py`
- `src/providers/policy/allowlist.py`
- `src/providers/policy/secret_policy.py`
- `src/providers/policy/write_firewall.py`
- `src/providers/prediction_markets/contracts.py`
- `src/providers/sportsbooks/contracts.py`
- `src/providers/zero_dte_stocks/contracts.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sportsbook_adapter_contract.py`

## Files Transported
- `ProviderAdapterContract` and `ReadOnlyProviderContract` aliases now live in `src/providers/contracts.py`.
- `ProviderPayloadValidator` now lives in `src/providers/validation.py`.
- `ProviderWritePolicy` now lives in `src/providers/policy/write_firewall.py`.
- Product-category contract surfaces now exist in:
  - `src/providers/prediction_markets/contracts.py`
  - `src/providers/sportsbooks/contracts.py`
  - `src/providers/zero_dte_stocks/contracts.py`

## Files Generalized
- Canonical allowlist and secret-policy helpers are now vendor-neutral.
- Vendor-specific contract naming was removed from the canonical `src/providers` path.
- Product categories are now the canonical naming layer:
  - `prediction_markets`
  - `zero_dte_stocks`
  - `sportsbooks`

## Files Deferred
- Runtime provider implementations remain deferred.
- Live clients remain deferred.
- Legacy compatibility surfaces remain deferred:
  - `betting_providers/base.py`
  - `betting_providers/normalization.py`
  - `providers/base_provider.py`
- `automation_scheduler` runtime orchestration remains a decommission target.

## Compatibility Strategy
- Legacy wrappers continue to resolve.
- Legacy wrapper modules preserve old import paths and old provider names.
- Canonical modules expose product-category contracts and generic policies only.
- Existing runtime behavior is preserved through wrappers, not through new live code.

## Rollback Strategy
- Revert the canonical policy and category contract additions.
- Restore the legacy wrapper files to their prior delegation state.
- Keep the legacy runtime modules untouched if rollback is required.

## Risks
- Wrapper divergence is now possible if a future change updates canonical behavior without updating the legacy compatibility layer.
- Runtime provider code still depends on legacy modules, so migration must remain incremental.
- Import parity must be rechecked before any runtime provider migration batch.

## Test Results
- New phase test added for provider foundation completion.
- Existing provider foundation tests remain in the acceptance slice.
- No network calls are required for the canonical provider foundation imports.
- No credentials are read at import time by the canonical provider modules.

## Next Recommended Phase
Proceed to the next runtime provider migration batch.
