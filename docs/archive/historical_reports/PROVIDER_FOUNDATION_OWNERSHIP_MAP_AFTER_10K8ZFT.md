# PROVIDER_FOUNDATION_OWNERSHIP_MAP_AFTER_10K8ZFT

## Executive Summary
The pure provider foundation has been transported into `src.providers`. Legacy modules are now compatibility wrappers where applicable. Runtime provider implementations were not moved.

## Ownership Map
| Old Owner | New Owner | Compatibility Wrapper Location | Migration Status | Deletion Eligibility |
| --- | --- | --- | --- | --- |
| `automation_scheduler/provider_contracts.py` | `src/providers/contracts.py` | `automation_scheduler/provider_contracts.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_registry.py` | `src/providers/registry.py` | `automation_scheduler/provider_registry.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_health.py` | `src/providers/health.py` | `automation_scheduler/provider_health.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_adapter_base.py` | `src/providers/base.py` | `automation_scheduler/provider_adapter_base.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_normalization_contract.py` | `src/providers/normalization.py` | `automation_scheduler/provider_normalization_contract.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_payload_validator.py` | `src/providers/validation.py` | `automation_scheduler/provider_payload_validator.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_secret_policy.py` | `src/providers/policy/secret_policy.py` | `automation_scheduler/provider_secret_policy.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_allowlist.py` | `src/providers/policy/allowlist.py` | `automation_scheduler/provider_allowlist.py` | transported and wrapped | not yet |
| `automation_scheduler/provider_write_firewall.py` | deferred runtime policy gate | none yet | deferred | no |
| `automation_scheduler/kalshi_adapter_contract.py` | deferred runtime adapter contract | none yet | deferred | no |
| `automation_scheduler/sportsbook_adapter_contract.py` | deferred runtime adapter contract | none yet | deferred | no |
| `betting_providers/base.py` | deferred runtime adapter base | none yet | deferred | no |
| `providers/base_provider.py` | deferred compatibility utility | none yet | deferred | no |
| `betting_providers/normalization.py` | deferred runtime normalization helper | none yet | deferred | no |

## Notes
- The transported foundation is import-safe and local-only.
- Legacy wrappers preserve old import paths.
- `src/providers/policy/write_firewall.py` exists as a scaffold, but the runtime gate remains deferred because it is coupled to owner approval and risk-gate behavior.

## Deletion Eligibility Summary
- Foundation wrappers: not yet, because importer redirection still needs proof.
- Runtime modules: not yet.
- Deferred modules: not eligible in this phase.
