# FIRST_SAFE_TRANSPORT_BATCH_AFTER_10K8ZFS

## Summary
The first safe transport batch should move only pure provider foundations. The goal is to relocate local-only contract, registry, health, normalization, error, and adapter-base logic from scheduler-owned surfaces into the canonical `src/providers/` package while keeping behavior unchanged.

## Exact Files / Modules To Migrate Later
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `betting_providers/base.py`
- `providers/base_provider.py`
- `betting_providers/normalization.py`

## Exact Destination
- `src/providers/contracts.py`
- `src/providers/registry.py`
- `src/providers/health.py`
- `src/providers/base.py`
- `src/providers/normalization.py`
- `src/providers/errors.py`
- `src/providers/policy.py` if policy is introduced later, otherwise `src/providers/errors.py` plus `src/providers/health.py`

## Why This Is the Safest First Batch
- These modules are pure or nearly pure scaffolds.
- They do not need live API calls.
- They do not need credentials.
- They do not submit orders, fetch raw external data, or scrape.
- They are already heavily covered by contract-style tests.
- They are the least risky way to prove the canonical provider package can own behavior.

## Required Contract Tests
- Import-safe tests for every migrated module.
- Registry-empty and scaffold-only tests.
- Health and redaction tests.
- Normalization parity tests with static fixtures.
- Wrapper tests proving the old import paths still return the same outputs.

## Required Import Redirection
- Repoint provider tests to `src/providers` canonical modules first.
- Keep legacy import paths as wrappers until importer scans are clean.
- Do not repoint `main.py`, `src/api/*`, or `screenshot_intake.py` until the canonical package is stable.

## Required Compatibility Shims
- `betting_providers/*` adapter surfaces that still expose the old imports.
- `providers/*` compatibility shells until `src/services/enrichment_service.py` and `screenshot_intake.py` are repointed.
- `automation_scheduler/provider_*` until the canonical package proves equivalent.

## No-Network Guarantee
The batch must remain local-only. Tests should use fixed fixtures, fake clients, or in-memory scaffolds only.

## No-Credential Guarantee
The batch must not read `OPENAI_*`, `KALSHI_*`, `SHARP_*`, broker, or connector credentials at import time or test time.

## Rollback Plan
If a migrated symbol changes output shape or import behavior:
1. Restore the wrapper.
2. Keep the legacy module intact.
3. Re-run parity tests.
4. Only proceed after the canonical owner matches legacy behavior exactly.

## Expected Deletion Candidates After Successful Migration
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- legacy wrapper implementations in `betting_providers/base.py` and `providers/base_provider.py` once all importers are repointed

## Next Suggested Move
Implement Batch 1 with wrapper-first transport and keep every legacy path importable until the test suite proves the canonical provider package is stable.
