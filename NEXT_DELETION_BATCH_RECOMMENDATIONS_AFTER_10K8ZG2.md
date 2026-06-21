# NEXT_DELETION_BATCH_RECOMMENDATIONS_AFTER_10K8ZG2

## Executive Summary
The safest deletion batch is the wrapper-only batch that has already been replaced by canonical ownership under `src/providers` and `src/connectors`.

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Recommended Batch 1
Delete only after import proof:
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
- `providers/odds_provider_router.py`

Why this is the safest batch:
- these files are already forwarding to canonical owners
- they do not define the long-term architecture
- they are the most obvious shim-only surface

## Recommended Batch 2
Delete after downstream rewrites:
- `betting_providers/provider_router.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`

Prerequisites:
- `src/services/enrichment_service.py` no longer imports them
- `screenshot_intake.py` no longer depends on them
- tests are redirected to canonical paths

## Recommended Batch 3
Delete after live-client replacement:
- `kalshi_client.py`
- `sharp_client.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

Prerequisites:
- connector/provider boundaries are fully established
- no runtime import sites remain
- no test or API path still depends on the legacy modules

## Safest Batch Definition
The safest deletion batch is the one that removes only wrapper-only modules after all import sites have been redirected and the test suite proves the canonical modules are the only owners.

## Acceptance Results
- Next batch recommendations produced: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes

## Next Phase Recommendation
Begin only the wrapper-only deletion proof batch.
