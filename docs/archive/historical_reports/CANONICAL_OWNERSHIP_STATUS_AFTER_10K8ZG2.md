# CANONICAL_OWNERSHIP_STATUS_AFTER_10K8ZG2

## Executive Summary
Canonical ownership is now visibly split between:
- `src/providers` for product-category provider logic
- `src/connectors` for inert raw-access boundaries

Legacy ownership still remains in `providers/`, `betting_providers/`, and `automation_scheduler/`, but much of that surface is now shim-only or compatibility-only.

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Canonical Owners
| Area | Canonical owner | File-count status | Notes |
| --- | --- | --- | --- |
| Provider foundations | `src/providers` | `60` files | Contracts, registry, health, routing, validation, policy |
| Connector boundaries | `src/connectors` | `62` files | Inert wrappers for prediction markets, odds data, market data, feeds, web scraping |
| 0DTE/stocks provider | `src/providers/zero_dte_stocks` | included in `src/providers` | Read-only normalization over supplied market-data payloads |
| Prediction markets provider | `src/providers/prediction_markets` | included in `src/providers` | Category-owned adapters and models |
| Sportsbooks provider | `src/providers/sportsbooks` | included in `src/providers` | Category-owned adapters and models |

## Provider Ownership Estimate
Reviewed provider-family files:
- `src/providers`: `60`
- `providers`: `5`
- `betting_providers`: `9`
- automation scheduler provider-related files: `36`

Estimate:
- canonical provider ownership under `src/providers`: `60 / 110 = ~55%`

Interpretation:
- The canonical provider boundary is now real and usable.
- The remaining ~45% is a mixture of compatibility wrappers and runtime legacy ownership.

## Connector Ownership Estimate
Reviewed connector-family files:
- `src/connectors`: `62`
- direct legacy live connector/client modules reviewed: `12`

Estimate:
- canonical connector ownership under `src/connectors`: `62 / 74 = ~84%`

Interpretation:
- The connector boundary is largely canonical in file count.
- Live connector behavior is still deferred in legacy modules, so runtime ownership is lower than the file count suggests.

## Legacy Ownership Still Present
### `providers/`
- `providers/__init__.py` is compatibility-only.
- `providers/base_provider.py` is compatibility-only.
- `providers/odds_provider_router.py` is a compatibility wrapper.
- `providers/kalshi_provider.py` and `providers/sharp_provider.py` still own live enrichment behavior.

### `betting_providers/`
- `betting_providers/__init__.py` is compatibility-facing.
- `betting_providers/base.py`, `betting_providers/normalization.py`, and `betting_providers/provider_router.py` are bridging wrappers.
- `betting_providers/kalshi_api.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, and `betting_providers/sportsgameodds.py` still own vendor runtime behavior.

### `automation_scheduler/`
- Provider foundation wrapper modules are canonical redirects.
- Scheduler provider adapters and snapshot helpers still own runtime behavior.
- Orchestration, dashboard-data helpers, and research workflows still depend on this package.

## Canonical Replacement Summary
### CANONICAL_REPLACED
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`
- `providers/base_provider.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`
- `betting_providers/provider_router.py`

### SHIM_ONLY
- `providers/__init__.py`
- `betting_providers/__init__.py`
- `providers/odds_provider_router.py`

### LEGACY_RUNTIME_OWNER
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `kalshi_client.py`
- `sharp_client.py`

## Compatibility and Deletion Status
- `src/providers` is canonical.
- `src/connectors` is canonical.
- `providers/` and `betting_providers/` are transitional and mixed.
- `automation_scheduler/` is transitional and still runtime-heavy.
- Deletion readiness is improving, but not yet sufficient for legacy runtime owners.

## Acceptance Results
- Canonical ownership snapshot recorded: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes

## Next Phase Recommendation
Only the wrapper-only layer should be considered for deletion proof next.
