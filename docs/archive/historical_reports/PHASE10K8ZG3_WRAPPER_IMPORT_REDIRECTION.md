# PHASE10K8ZG3 Wrapper Import Redirection

## Executive Summary
This phase redirects downstream imports away from wrapper-only legacy modules and toward canonical `src.providers` paths.

Wrapper-only modules are not deleted in this phase. This phase redirects downstream imports and produces deletion proof only.

## Current HEAD
- `4ed2c2c`

## Purpose
Reduce the live dependency surface on wrapper-only modules while preserving compatibility wrappers for later proof and deletion batches.

## Scope
Redirected:
- provider contract/registry/health/base/normalization/policy imports in general tests
- `main.py` import of `PREDICTION_MARKET`
- `screenshot_intake.py` import of ticket enrichment
- sportsbook and Kalshi registry-based tests

## Non-Goals
- No deletion
- No runtime behavior change
- No live API calls
- No credentials read
- No scraping
- No broker execution

## Big Picture
Canonical ownership already lives under `src/providers` and `src/connectors`.
Wrapper-only modules remain only because some compatibility tests and legacy runtime owners still reference them.

## Imports Redirected
- `tests/test_provider_contracts.py` -> `src.providers.contracts`
- `tests/test_provider_registry.py` -> `src.providers.registry`
- `tests/test_provider_health.py` -> `src.providers.contracts` + `src.providers.health`
- `tests/test_provider_payload_validator.py` -> `src.providers.validation`
- `tests/test_provider_normalization_contract.py` -> `src.providers.normalization` + `src.providers.sportsbooks`
- `tests/test_provider_secret_policy.py` -> `src.providers.policy.secret_policy`
- `tests/test_provider_adapter_base.py` -> `src.providers.base` + `src.providers.contracts`
- `tests/test_sportsbook_odds_provider.py` -> `src.providers.registry`
- `tests/test_kalshi_market_provider.py` -> `src.providers.registry`
- `tests/test_security_framework.py` -> `src.providers.policy.write_firewall`
- `main.py` -> `src.providers.compat`
- `screenshot_intake.py` -> `src.services.enrichment_service.EnrichmentService`

## Imports Remaining and Why
- `main.py` still imports `betting_providers.provider_router.ProviderRouter` because that router is not a wrapper-only module and remains a runtime bridge.
- `src/api/model_card_service.py` still imports `betting_providers.provider_router.ProviderRouter` for the same reason.
- Compatibility tests still import wrapper-only modules intentionally to prove backward compatibility.
- `providers/odds_provider_router.py` remains referenced by legacy compatibility tests until those tests are retired or redirected.

## Deletion-Ready Wrappers
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

## Still-Blocked Wrappers
- `providers/odds_provider_router.py`
- any wrapper still referenced by compatibility-only phase tests

## Why No Deletion Occurred
The wrappers remain in place until the compatibility test surface is reduced or retired. This phase only proves that downstream code can be redirected safely.

## Next Recommended Deletion Batch
The next batch should target the deletion-ready wrapper-only foundation modules first, after the compatibility test surface is updated.
