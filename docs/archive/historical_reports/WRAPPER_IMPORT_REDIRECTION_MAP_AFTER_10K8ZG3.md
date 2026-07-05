# WRAPPER_IMPORT_REDIRECTION_MAP_AFTER_10K8ZG3

## Executive Summary
This map records the canonical import paths that now replace wrapper-only legacy imports in normal downstream code.

Wrapper-only modules are not deleted in this phase. This phase redirects downstream imports and produces deletion proof only.

## Canonical Targets
- `src.providers.contracts`
- `src.providers.registry`
- `src.providers.health`
- `src.providers.base`
- `src.providers.normalization`
- `src.providers.validation`
- `src.providers.policy.secret_policy`
- `src.providers.policy.write_firewall`
- `src.providers.policy.allowlist`
- `src.providers.compat`
- `src.providers.routing`
- `src.providers.categories`

## Redirected Files
- `tests/test_provider_contracts.py`
- `tests/test_provider_registry.py`
- `tests/test_provider_health.py`
- `tests/test_provider_payload_validator.py`
- `tests/test_provider_normalization_contract.py`
- `tests/test_provider_secret_policy.py`
- `tests/test_provider_adapter_base.py`
- `tests/test_sportsbook_odds_provider.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_security_framework.py`
- `main.py`
- `screenshot_intake.py`

## Compatibility-Only Remaining Imports
- `tests/test_phase10k8zft_provider_foundation_transport.py`
- `tests/test_phase10k8zfu_provider_foundation_completion.py`
- `tests/test_phase10k8zfw_runtime_provider_migration_batch_2.py`
- `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`
- `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`
- `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py`

## Notes
- Canonical imports now carry the non-compatibility provider tests.
- Wrapper imports are preserved only in compatibility-oriented phase tests and in runtime bridge code that is not yet part of the wrapper-only deletion batch.

## Next Phase Recommendation
Move from redirection proof to wrapper-only deletion proof.
