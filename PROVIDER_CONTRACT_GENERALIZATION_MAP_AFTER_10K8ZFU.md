# PROVIDER_CONTRACT_GENERALIZATION_MAP_AFTER_10K8ZFU

## Overview
This map records how vendor-specific adapter contracts were generalized into vendor-neutral product-category contracts.

## Generalization Map

| Old Owner | New Owner | Compatibility Wrapper | Migration Status | Deletion Eligibility |
| --- | --- | --- | --- | --- |
| `automation_scheduler/kalshi_adapter_contract.py` | `src/providers/prediction_markets/contracts.py` | `automation_scheduler/kalshi_adapter_contract.py` | generalized to product category | not yet |
| `automation_scheduler/sportsbook_adapter_contract.py` | `src/providers/sportsbooks/contracts.py` | `automation_scheduler/sportsbook_adapter_contract.py` | generalized to product category | not yet |
| `automation_scheduler/provider_write_firewall.py` | `src/providers/policy/write_firewall.py` | `automation_scheduler/provider_write_firewall.py` | foundation policy generalized | not yet |
| `automation_scheduler/provider_allowlist.py` | `src/providers/policy/allowlist.py` | `automation_scheduler/provider_allowlist.py` | canonical helper generalized | not yet |
| `automation_scheduler/provider_secret_policy.py` | `src/providers/policy/secret_policy.py` | `automation_scheduler/provider_secret_policy.py` | canonical helper generalized | not yet |
| `src/providers/policy/write_firewall.py` | `src/providers/policy/write_firewall.py` | `ProviderWriteFirewallPolicy` alias | canonical owner established | not applicable |

## Canonical Contract Surfaces
- `PredictionMarketProviderContract`
- `ZeroDteStockProviderContract`
- `SportsbookProviderContract`
- `ProviderAdapterContract`
- `ReadOnlyProviderContract`
- `ProviderPayloadValidator`
- `ProviderWritePolicy`

## Notes
- Vendor names remain only in compatibility wrappers.
- Vendor-specific names do not define canonical ownership.
- The canonical path is vendor-neutral and product-category based.

