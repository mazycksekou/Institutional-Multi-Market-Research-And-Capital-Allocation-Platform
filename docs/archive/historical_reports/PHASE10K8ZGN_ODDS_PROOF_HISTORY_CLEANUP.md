# PHASE 10K8ZGN Odds Proof-History Cleanup

## Executive Summary
This phase reclassifies the odds proof-history trail so legacy sportsbook shell names are no longer retained as a reason to keep the shells around.

The canonical odds runtime path remains:
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`

Legacy odds modules still exist on disk only for the dedicated compatibility-proof tests.

## Current HEAD
`68a5070dad91a21fcb097bcab63087b0ed7c81a7`

## Purpose
Clean up the proof-history trail, remove the idea that old redirection tests are retention requirements, and re-run delete-readiness against the remaining explicit compatibility proofs.

## Scope
In scope:
- proof-history reclassification
- historical test/doc cleanup
- delete-readiness recheck
- canonical bridge/provider import safety

Out of scope:
- deletion
- live calls
- credential reads
- connector activation
- broker or bet execution
- dashboard rewrites
- main entrypoint rewrites

## Non-Goals
- No files deleted
- No files moved
- No source-function migrations
- No public functions removed
- No behavior expansion
- No live API calls
- No credential reads at import time

## Big-Picture Architecture
- `src.connectors.odds_data` owns the inert odds connector boundary.
- `src.services.odds_runtime_bridge` owns the compatibility-preserving odds runtime bridge.
- `src.providers.sportsbooks` owns canonical sportsbook normalization and validation.
- Historical proof files are evidence only; they should not keep shell modules alive by accident.

## Proof-History References Before Cleanup
Before cleanup, the newer proof-history files still referenced legacy shell importability as part of the delete trail:
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py`
- `tests/test_phase10k8zgm_odds_historical_test_redirection.py`
- `PHASE10K8ZGM_ODDS_HISTORICAL_TEST_REDIRECTION.md`
- `ODDS_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGM.md`
- `ODDS_SHELL_IMPORT_SCAN_AFTER_10K8ZGM.md`
- `ODDS_SHELL_DELETE_READINESS_AFTER_10K8ZGM.md`

## References Updated or Reclassified
- The redirection tests now point at canonical bridge/connector/provider modules.
- The old shell references in the historical docs are now labeled historical evidence only.
- The remaining blockers are the dedicated compatibility-proof tests, not the historical redirection tests.

## Remaining References After Cleanup
The only intentional remaining legacy-shell references belong to the explicit compatibility-proof tests:
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`

## Delete-Readiness
Current status for the legacy odds shells:
- `sharp_client.py`: blocked
- `providers/sharp_provider.py`: blocked
- `betting_providers/sharp_api.py`: blocked
- `betting_providers/the_odds_api.py`: blocked
- `betting_providers/sportsgameodds.py`: blocked
- `automation_scheduler/sharp_sportsbook_adapter.py`: blocked
- `automation_scheduler/sportsbook_odds_provider.py`: blocked

No shell is deleted in this phase.
The delete-readiness result is still negative because compatibility-proof coverage remains in place.

## Compatibility Policy
Compatibility proofs remain separate and explicit.
Historical proof files now describe evidence, not retention requirements.
The legacy shells stay on disk until the compatibility-proof tests are redirected or retired in a later phase.

## No-Deletion / No-Call Guarantees
- No deletion occurred
- No live API calls were made
- No credentials were read at import time
- No bet execution or broker execution was introduced
- No connector activation occurred

## Next Recommended Phase
Re-run the odds shell delete-readiness proof once the explicit compatibility-proof tests are redirected or retired.

## Required Statement
Proof-history references must not preserve legacy odds shells unnecessarily. This phase reclassifies historical evidence and proves delete readiness, but does not delete legacy odds modules.
