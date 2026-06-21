# LEGACY_DELETE_CANDIDATE_QUEUE_AFTER_10K8ZG2

## Executive Summary
This is a queue of future deletion candidates only.

No deletion occurs in this phase.
No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Delete-Ready-After-Import-Proof
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

## Requires Dependency Migration First
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/provider_router.py`
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

## Requires Test Rewrite First
- `tests/test_screenshot_analysis.py`
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`
- `tests/test_automation_scheduler_endpoints.py`
- `tests/test_provider_registry.py`
- `tests/test_provider_secret_policy.py`

## Must Not Delete Yet
- `main.py`
- `streamlit_app.py`
- `src/api/provider_status_routes.py`
- `src/api/model_card_service.py`
- `src/services/enrichment_service.py`
- `src/services/action_betting_service.py`
- `screenshot_intake.py`

## Non-Goal but Still Requires Proof
- any live adapter that still reads credentials
- any legacy client that still calls `requests` or `httpx`
- any route that still depends on the scheduler wrapper layer

## Recommended Deletion Phase
1. wrapper-only scheduler/provider foundation modules
2. legacy compatibility provider wrappers
3. legacy runtime client/adapters after import redirection

## Acceptance Results
- Candidate queue built: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes

## Next Phase Recommendation
Delete only after downstream import redirection and test updates are complete.
