# PHASE 10K8ZGO Odds Compatibility Test Retirement

## Executive Summary
This phase retires the final explicit compatibility-proof tests that used to preserve legacy odds-shell imports.

The canonical odds runtime flow remains:
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`

Legacy odds modules remain on disk, but the active compatibility tests no longer need to preserve them as runtime dependencies.

## Current HEAD
`a7cb4b503480018129209a6233dbe63e086c2bf4`

## Purpose
Retire the last compatibility-proof assertions that intentionally touched legacy odds shells, then prove that final delete readiness is still intact.

## Scope
In scope:
- retire compatibility-only import assertions
- reclassify historical references
- prove canonical bridge/provider behavior
- prove legacy-shell importability as historical evidence only

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
- Behavior unchanged
- No live API calls
- No credential reads at import time

## Big-Picture Architecture
- `src.connectors.odds_data` owns the inert odds connector boundary.
- `src.services.odds_runtime_bridge` owns the compatibility-preserving runtime bridge.
- `src.providers.sportsbooks` owns canonical sportsbook normalization and validation.
- Explicit compatibility tests should not remain as shell-retention mechanisms once their proof value has been captured.

## Compatibility Test Retirement
The final compatibility-proof assertions were redirected away from legacy shell ownership.

Updated tests:
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`

These files now validate canonical bridge/provider behavior instead of preserving legacy-shell import requirements.

## Delete Readiness
Current status for the legacy odds shells:
- `sharp_client.py`: delete-ready now
- `providers/sharp_provider.py`: delete-ready now
- `betting_providers/sharp_api.py`: delete-ready now
- `betting_providers/the_odds_api.py`: delete-ready now
- `betting_providers/sportsgameodds.py`: delete-ready now
- `automation_scheduler/sharp_sportsbook_adapter.py`: delete-ready now
- `automation_scheduler/sportsbook_odds_provider.py`: delete-ready now

No shell is deleted in this phase.

## Historical Evidence Policy
Legacy-shell references that remain in docs are historical evidence only.
No active test requires legacy odds shell imports unless explicitly documented as historical evidence in the final delete-proof test.

## No-Deletion / No-Call Guarantees
- No deletion occurred
- No live API calls were made
- No credentials were read at import time
- No bet execution or broker execution was introduced
- No connector activation occurred

## Next Recommended Phase
If deletion is desired, remove the now-delete-ready legacy odds shells in the next batch after keeping the final proof artifacts intact.

## Required Statement
Explicit compatibility-proof tests must not preserve legacy odds shells unnecessarily. This phase proves final delete readiness only and does not delete legacy odds modules.
