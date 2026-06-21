# NEXT_PROVIDER_FOUNDATION_DELETION_BATCH_AFTER_10K8ZG8

## Recommended Next Batch
1. Delete the thin compatibility wrappers that are already delete-ready:
   - `automation_scheduler/provider_contracts.py`
   - `automation_scheduler/provider_health.py`
   - `automation_scheduler/provider_adapter_base.py`
   - `automation_scheduler/provider_normalization_contract.py`
   - `automation_scheduler/provider_payload_validator.py`
   - `automation_scheduler/provider_secret_policy.py`
   - `providers/base_provider.py`
   - `betting_providers/base.py`
   - `betting_providers/normalization.py`
2. Redirect or retire the remaining test blockers that still mention those wrapper paths.
3. Re-audit `automation_scheduler/provider_registry.py` and `automation_scheduler/provider_write_firewall.py` as separate runtime-blocker batches.

## Safest Batch Definition
- Thin wrappers only.
- No runtime registry or write-firewall logic.
- No connector, AI, brokerage, dashboard, or entrypoint changes.

## Why This Batch Is Next
- Import proof is complete for the canonical `src.providers` foundation.
- Compatibility proof remains on disk.
- The remaining blockers are isolated to runtime registry/write-firewall logic and a few test references.

No deletion occurs in this phase.
