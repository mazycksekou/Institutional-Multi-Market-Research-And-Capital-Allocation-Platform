# PROVIDER_LEGACY_WRAPPER_STATUS_AFTER_10K8ZFU

## Overview
Legacy wrappers remain in place so existing imports continue to work while the canonical provider boundary stays vendor-neutral.

## Wrapper Status

| Wrapper Path | Redirect Target | Importer / Reference Count | Safe Deletion Phase |
| --- | --- | ---: | --- |
| `automation_scheduler/provider_contracts.py` | `src/providers/contracts.py` | 26 | after runtime contract migration |
| `automation_scheduler/provider_registry.py` | `src/providers/registry.py` | 41 | after registry migration proof |
| `automation_scheduler/provider_health.py` | `src/providers/health.py` | 42 | after health migration proof |
| `automation_scheduler/provider_adapter_base.py` | `src/providers/base.py` | 20 | after runtime adapter migration |
| `automation_scheduler/provider_normalization_contract.py` | `src/providers/normalization.py` | 20 | after normalization migration proof |
| `automation_scheduler/provider_payload_validator.py` | `src/providers/validation.py` | 30 | after validator migration proof |
| `automation_scheduler/provider_secret_policy.py` | `src/providers/policy/secret_policy.py` | 24 | after secret-policy migration proof |
| `automation_scheduler/provider_allowlist.py` | `src/providers/policy/allowlist.py` | 26 | after allowlist migration proof |
| `automation_scheduler/kalshi_adapter_contract.py` | `src/providers/prediction_markets/contracts.py` | 16 | after prediction-market runtime migration |
| `automation_scheduler/sportsbook_adapter_contract.py` | `src/providers/sportsbooks/contracts.py` | 22 | after sportsbook runtime migration |
| `automation_scheduler/provider_write_firewall.py` | `src/providers/policy/write_firewall.py` | 22 | after write-policy migration proof |

## Compatibility Notes
- Legacy wrappers keep old names for compatibility.
- Canonical modules expose vendor-neutral contracts.
- Legacy wrappers are not deletion candidates yet.

