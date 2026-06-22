# PHASE 10K8ZGL Odds Runtime Consumer Redirection Batch 2

## Executive Summary
This phase redirects the remaining runtime odds consumers away from legacy odds shells and into canonical boundary surfaces.
The canonical odds connector boundary lives under `src.connectors.odds_data`, the canonical sportsbook/provider normalization boundary lives under `src.providers.sportsbooks`, and the runtime orchestration bridge now lives under `src.services.odds_runtime_bridge`.

The legacy odds shells remain on disk for compatibility and proof history, but they are no longer the preferred runtime dependency for the redirected service and scheduler paths.

## Current HEAD
`308112593407b0feaeee74670c4de58f990e8918`

## Purpose
Create a redirection-only phase that moves runtime odds consumers away from legacy odds shells without deleting any file or changing runtime behavior.

## Scope
In scope:
- `src/services/enrichment_service.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/__init__.py`
- `src/services/odds_runtime_bridge.py`

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
- `src.connectors.odds_data` owns the inert connector boundary and disabled live-client metadata.
- `src.providers.sportsbooks` owns read-only sportsbook normalization and validation.
- `src.services` owns application-facing orchestration and compatibility bridges.
- `automation_scheduler` remains a legacy orchestration surface, but runtime odds access should flow through canonical services instead of legacy odds shells.

## Runtime Consumer Redirection
The following runtime consumers now point at the canonical service bridge instead of legacy odds shells:
- `src/services/enrichment_service.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/__init__.py`

The new canonical runtime bridge is:
- `src/services/odds_runtime_bridge.py`

## Canonical Disabled Surfaces
The bridge and connector surfaces used in this phase are disabled by design:
- `src.connectors.odds_data`
- `src.connectors.errors.ConnectorDisabledError`
- `src.providers.sportsbooks.adapters`
- `src.providers.sportsbooks.contracts`
- `src.providers.policy.secret_policy`

## Runtime Import Scan
Before redirection, runtime consumers still depended on legacy odds shells such as:
- `providers.sharp_provider`
- `automation_scheduler.sharp_sportsbook_adapter`
- `automation_scheduler.sportsbook_odds_provider`

After redirection, runtime consumer imports now point to:
- `src.services.odds_runtime_bridge`

## Remaining Legacy Odds Shells
The legacy odds shells remain importable:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

They are preserved for compatibility and deletion-proof history, but they are no longer the runtime dependency of the redirection targets in this phase.

## Delete-Readiness
This phase does not delete legacy odds shells.
The runtime consumers were redirected first so later deletion-proof phases can focus on remaining shell usage and test references.

Current status:
- runtime consumers redirected: yes
- legacy shells still present: yes
- delete-ready for this phase: no
- delete-proof only: yes

## Compatibility Policy
Legacy imports remain available while the canonical bridge is adopted.
The bridge returns disabled metadata and read-only snapshots only.
That keeps the old runtime shape importable without restoring live odds access.

## No-Deletion / No-Call Guarantees
- No deletion occurred
- No live API calls were made
- No credentials were read at import time
- No bet execution or broker execution was introduced
- No connector activation occurred

## Next Recommended Phase
Move the remaining odds-shell tests and historical compatibility references onto the canonical bridge surfaces, then prove whether the legacy odds shells themselves can be retired safely.

## Required Statement
Odds runtime consumers are redirected away from legacy odds shells in this phase. This phase does not authorize live API calls, credential reads, bet execution, connector activation, or deletion.
