# LEGACY_SHIM_STATUS_AFTER_10K8ZG2

## Executive Summary
Legacy shim status is now mixed:
- Some modules are pure compatibility redirects.
- Some modules still own live behavior.
- Some modules are mixed compatibility plus runtime owner.

That split is the reason deletion is not yet safe.

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Shim-Only Files
- `providers/__init__.py`
- `providers/base_provider.py`
- `providers/odds_provider_router.py`
- `betting_providers/__init__.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`
- `betting_providers/provider_router.py`
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_write_firewall.py`

## Legacy Runtime Owners
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

## Compatibility Wrappers Preserved
- The legacy imports still resolve for the wrapper-only modules listed above.
- The wrapper-only modules now point toward canonical owners under `src/providers` or `src/services`.
- Runtime owners still remain in place because downstream code has not been rewritten yet.

## Mixed Files
- `providers/odds_provider_router.py` is compatibility-only, but it still sits on a runtime path via `screenshot_intake.py`.
- `betting_providers/provider_router.py` is compatibility-facing, but `main.py`, `src/api/model_card_service.py`, and services still route through it.
- `automation_scheduler` provider wrappers are compatibility-only, but the package still owns runtime scheduler flow and dashboard data.

## Deletion Readiness
- Shim-only files are the nearest-term deletion candidates.
- Runtime owners are not deletion-safe yet.
- Mixed files are not deletion-safe until import redirection is complete.

## Acceptance Results
- Shim status classified: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes

## Next Phase Recommendation
Delete only after import proof, wrapper retirement, and downstream consumer rewrites.
