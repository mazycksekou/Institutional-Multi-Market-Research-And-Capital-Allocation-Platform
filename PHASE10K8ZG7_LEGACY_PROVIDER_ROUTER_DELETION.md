# PHASE10K8ZG7 Legacy Provider Router Deletion

## Executive Summary
10K8ZG7 deletes only the proof-backed legacy provider router compatibility hooks: `betting_providers/provider_router.py` and `providers/odds_provider_router.py`. The canonical router remains `src/providers/provider_router.py`.

## Current HEAD
1b8ffeeb10387ae4f39137fafb6db5519e8afbf3 before deletion.

## Purpose
Remove obsolete router wrappers after import proof, compatibility proof, and full test proof were established in 10K8ZG6.

## Scope
- Files deleted:
  - `betting_providers/provider_router.py`
  - `providers/odds_provider_router.py`
- No other files are deleted.

## Non-Goals
- No runtime provider behavior changes.
- No connector, AI, brokerage, dashboard, or entrypoint rewrites.

## Proof Source From 10K8ZG6
- `src/providers/provider_router.py` is canonical.
- Runtime consumers were redirected to the canonical router.
- The legacy router files were marked delete-ready.

## Import Scan Before Deletion
- No tracked runtime file required `betting_providers.provider_router` as a live dependency.
- No tracked runtime file required `providers.odds_provider_router` as a live dependency.

## Import Scan After Deletion
- No tracked Python file imports either legacy router module.
- Canonical imports continue to resolve from `src.providers.provider_router`.

## Tests Run
- `tests/test_phase10k8zg7_legacy_provider_router_deletion.py`
- `tests/test_phase10k8zg6_legacy_provider_router_delete_proof.py`
- `tests/test_phase10k8zg5_provider_router_independence.py`
- `tests/test_phase10k8zg4_runtime_bridge_import_redirection.py`
- `tests/test_phase10k8zg3_wrapper_import_redirection.py`

## Behavior Preserved
- Canonical provider routing behavior is unchanged.
- `main.py` still uses `src.providers.provider_router`.
- `src/api/model_card_service.py` still uses `src.providers.provider_router`.

## Remaining Legacy Provider Deletion Candidates
- Historical docs may still mention the deleted compatibility hooks.
- No additional runtime router deletions are authorized in this phase.

## Next Recommended Phase
- Review the next legacy compatibility queue only after the post-deletion test gate is green.

Only proof-backed legacy provider router compatibility hooks are deleted in this phase. No runtime provider owners, live clients, dashboard files, entrypoints, AI modules, brokerage modules, or connector scaffolds are deleted.
