# PHASE 10K8ZGM Odds Historical Test Redirection

## Executive Summary
This phase redirects the remaining historical odds-shell tests away from the legacy odds modules and toward the canonical odds bridge and connector surfaces.

The runtime flow remains:
- `automation_scheduler` and `src/services/enrichment_service.py`
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`

Legacy odds modules remain on disk for explicit compatibility proofs, but the historical sportsbook tests are now centered on canonical bridge/connector behavior. The prior legacy-shell references in the proof trail are now historical evidence only.

## Current HEAD
`b185a75b652543ca80387bc5bdf667c31711165a`

## Purpose
Move the remaining sportsbook historical tests off legacy odds-shell imports so delete-readiness proof can advance without depending on old shell behavior for the test body.

## Scope
In scope:
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`

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
- No connector activation

## Big-Picture Architecture
- `src.connectors.odds_data` owns the disabled connector metadata and inert live-client boundary.
- `src.services.odds_runtime_bridge` owns the compatibility-preserving sportsbook runtime bridge.
- `src.providers.sportsbooks` owns canonical sportsbook normalization and validation.
- Historical tests should validate the canonical bridge and connector behavior, not the legacy shell implementation details.

## Historical Test Redirection
The sportsbook historical tests were redirected to:
- `src/services/odds_runtime_bridge.py`
- `src/connectors/odds_data`
- `src.providers.sportsbooks.adapters`
- `src.providers.sportsbooks.contracts`

Updated tests:
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`

## Canonical Disabled Surfaces
The canonical disabled surfaces verified in this phase are:
- `src.connectors.odds_data`
- `src.connectors.odds_data.disabled_client`
- `src.connectors.odds_data.readiness`
- `src.services.odds_runtime_bridge.SharpSportsbookAdapter`

## Import Scan Summary
Before redirection, the historical sportsbook tests directly imported legacy odds shells such as:
- `automation_scheduler.sharp_sportsbook_adapter`
- `automation_scheduler.sportsbook_odds_provider`

After redirection, those test bodies now reference canonical bridge/provider surfaces.

## Test Redirection Summary
The remaining historical sportsbook tests now verify:
- disabled bridge behavior
- canonical sportsbook normalization
- canonical connector readiness
- safe snapshot writing and validation
- scheduler integration through the canonical bridge

## Remaining References After Redirection
Legacy odds shell files still exist for explicit compatibility proofs.
The remaining phase-proof files now treat the old shell references as historical evidence only rather than retention requirements.

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
The test redirection is a prerequisite for later deletion proof, not deletion itself.

## Compatibility Policy
Compatibility shells remain importable.
Historical tests now exercise canonical bridge/connector behavior first.
Legacy shell importability is checked only in the dedicated compatibility-proof tests.
Historical proof documents no longer use legacy-shell importability as a blocker.

## No-Deletion / No-Call Guarantees
- No deletion occurred
- No live API calls were made
- No credentials were read at import time
- No bet execution or broker execution was introduced
- No connector activation occurred

## Next Recommended Phase
Re-run the legacy shell delete-readiness proof after the historical references have been reclassified and the remaining compatibility-proof files have been evaluated.

## Required Statement
Odds shell deletion is authorized only after runtime imports, historical test imports, compatibility proof, and full local gate proof are clean. This phase proves readiness only and does not delete legacy odds modules.
