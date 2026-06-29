# PROVIDER_FOUNDATION_WRAPPER_STATUS_AFTER_10K8ZG8

## Wrapper Status
| File | Status | Notes |
| --- | --- | --- |
| `automation_scheduler/provider_contracts.py` | Delete-ready | Thin compatibility shim around `src.providers.contracts` |
| `automation_scheduler/provider_registry.py` | Runtime blocker | Still owns env-gated registry behavior |
| `automation_scheduler/provider_health.py` | Delete-ready | Thin compatibility shim around `src.providers.health` |
| `automation_scheduler/provider_adapter_base.py` | Delete-ready | Thin compatibility shim around `src.providers.base` |
| `automation_scheduler/provider_normalization_contract.py` | Delete-ready | Thin compatibility shim around `src.providers.normalization` |
| `automation_scheduler/provider_payload_validator.py` | Delete-ready | Thin compatibility shim around `src.providers.validation` |
| `automation_scheduler/provider_secret_policy.py` | Delete-ready | Thin compatibility shim around `src.providers.policy.secret_policy` |
| `automation_scheduler/provider_write_firewall.py` | Runtime blocker | Owns provider write-safety behavior and audit logging |
| `providers/base_provider.py` | Delete-ready | Legacy alias to `src.providers.compat` |
| `betting_providers/base.py` | Delete-ready | Legacy alias to `src.providers.compat` |
| `betting_providers/normalization.py` | Delete-ready | Legacy normalization alias to canonical adapters |

## Relocated Legacy Path Equivalents
- `src/automation_scheduler_legacy/provider_contracts.py`
- `src/automation_scheduler_legacy/provider_health.py`
- `src/automation_scheduler_legacy/provider_adapter_base.py`
- `src/automation_scheduler_legacy/provider_normalization_contract.py`
- `src/automation_scheduler_legacy/provider_payload_validator.py`
- `src/automation_scheduler_legacy/provider_secret_policy.py`

## Compatibility-Only Notes
- Wrapper files remain on disk for the proof phase.
- Test-only compatibility references still exist in older audit files.

## Files Not Delete-Ready
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_write_firewall.py`
- `src/automation_scheduler_legacy/provider_registry.py`
- `src/automation_scheduler_legacy/provider_write_firewall.py`

## Why No Deletion Occurred
The goal is proof, not removal. The wrapper files stay in place until the next approved deletion batch.

No deletion occurs in this phase.
