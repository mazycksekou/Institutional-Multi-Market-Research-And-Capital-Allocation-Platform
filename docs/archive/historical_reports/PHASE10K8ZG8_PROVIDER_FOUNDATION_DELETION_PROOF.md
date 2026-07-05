# PHASE10K8ZG8 Provider Foundation Deletion Proof

## Executive Summary
10K8ZG8 proves the remaining wrapper-only provider foundation files can be deleted later, after the last test blockers are redirected. The canonical provider foundation remains `src.providers`, while the wrapper files on disk are now compatibility-only evidence.

## Current HEAD
`646946fb409e9f5f6b426c9b6e5577e7c2654172`

## Purpose
Establish delete-readiness evidence for the thin provider foundation wrappers without deleting any of them in this phase.

## Scope
Proof targets reviewed:
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `providers/base_provider.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`

## Non-Goals
- No deletion occurs in this phase.
- No runtime behavior changes.
- No live API calls, credential reads, scraping, broker execution, AI/LLM calls, dashboard rewrites, main.py rewrites, or route rewrites.

## Big-Picture Architecture
- `src.providers` is the canonical provider foundation owner.
- `automation_scheduler` remains a legacy compatibility and orchestration area.
- `providers/` and `betting_providers/` remain legacy compatibility surfaces until the next approved deletion batch.

## Imports Found Before Redirection
- `tests/test_phase10k8zft_provider_foundation_transport.py` imported the wrapper foundation modules directly.
- `tests/test_phase10k8zfu_provider_foundation_completion.py` imported `betting_providers.base`, `betting_providers.normalization`, and `providers.base_provider` directly.
- `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py` imported `betting_providers.normalization` directly before redirection.
- `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py` still records wrapper compatibility imports as historical evidence.

## Imports Redirected
- `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py` now uses canonical prediction-market and sportsbook adapters for normalization coverage instead of `betting_providers.normalization`.

## Remaining Blockers
- `automation_scheduler/provider_registry.py` is a runtime blocker because it still owns registry behavior and env-gated enablement logic.
- `automation_scheduler/provider_write_firewall.py` is a runtime blocker because it still owns provider write-safety behavior and audit logging.
- `tests/test_phase10k8zft_provider_foundation_transport.py` remains a test blocker because it still checks the legacy wrapper compatibility surface.
- `tests/test_phase10k8zfu_provider_foundation_completion.py` remains a test blocker because it still verifies legacy wrapper compatibility behavior.
- `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py` remains a compatibility audit blocker because it still records legacy wrapper imports as evidence.

## Delete-Ready Files
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `providers/base_provider.py`
- `betting_providers/base.py`
- `betting_providers/normalization.py`

## Files Not Delete-Ready
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_write_firewall.py`
- Any test file still importing the wrapper-only surface directly.

## Why No Deletion Occurred
Provider foundation wrapper deletion is not performed in this phase. This phase proves whether wrapper-only files can be deleted safely after import, compatibility, and full-test proof.

## Recommended Next Deletion Batch
- Delete the delete-ready thin wrappers listed above after the remaining test blockers are redirected to canonical `src.providers` paths and the proof gate is rerun.
- Re-audit `automation_scheduler/provider_registry.py` separately because it still owns runtime behavior.
- Re-audit `automation_scheduler/provider_write_firewall.py` separately because it still owns runtime safety logic.

No deletion occurs in this phase.
