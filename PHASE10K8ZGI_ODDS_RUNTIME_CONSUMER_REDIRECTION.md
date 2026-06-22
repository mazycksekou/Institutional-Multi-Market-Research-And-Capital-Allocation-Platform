# PHASE10K8ZGI Odds Runtime Consumer Redirection

## Executive Summary
Phase 10K8ZGI redirects the remaining odds and sportsbook runtime consumers toward the canonical disabled connector boundary under `src.connectors.odds_data` while preserving legacy modules on disk and preserving existing runtime behavior. The redirection is import-level and metadata-level only in this phase.

## Current HEAD
`80ac25451fe46ddf35d16892c3e5ab2bc19d8d71`

## Purpose
Prove that the remaining odds live-client modules can be retired later by making the canonical disabled connector surfaces visible to the runtime consumers that still reference odds and sportsbook behavior.

## Scope
This phase covers the remaining odds runtime consumer surfaces:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `src/providers/provider_router.py`

## Non-Goals
- No deletion
- No live API calls
- No credential reads at import time
- No broker or bet execution
- No scraping
- No AI/LLM calls
- No route rewrites beyond import-only redirection
- No behavior change

## Big-Picture Architecture
- `src.connectors.odds_data` owns the disabled odds connector boundary.
- `src.providers` owns canonical provider routing and normalization.
- Legacy odds modules remain importable until later proof-backed deletion.
- Runtime consumers now point at canonical connector metadata so future deletion can be proven safely.

## Runtime Consumer Redirection
The following modules now import canonical odds connector metadata:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `src/providers/provider_router.py`

Each of these modules exposes import-safe connector metadata constants:
- `ODDS_DATA_CONNECTOR_CONFIGURATION`
- `ODDS_DATA_CONNECTOR_READINESS`

## Canonical Disabled Surfaces
The redirection points at:
- `src.connectors.odds_data.build_odds_data_connector_configuration`
- `src.connectors.odds_data.describe_odds_data_connector_readiness`

## Delete-Readiness
The odds runtime consumers are now aligned with the canonical disabled connector boundary, but the legacy live-method bodies remain on disk. That means this phase proves the path toward deletion, not deletion itself.

## Remaining Blockers
- Legacy live request bodies still exist in the odds modules.
- Runtime consumers still rely on compatibility behavior in `src.providers.provider_router`.
- API routes and enrichment paths still reference legacy provider flows indirectly.

## Compatibility Policy
legacy modules remain importable. The redirection added in this phase is additive and does not remove any public function or class.

## No-Deletion / No-Call Guarantees
- No deletion occurred
- No live calls were made
- No credentials were read at import time

## Next Recommended Phase
Redirect the remaining odds call paths that still depend on live-method bodies so the legacy odds modules become fully delete-ready.

Required statement: Odds runtime consumers are redirected toward connector-owned disabled surfaces in this phase. This phase does not authorize live API calls, credential reads, bet execution, route rewrites, or deletion of legacy odds modules.
