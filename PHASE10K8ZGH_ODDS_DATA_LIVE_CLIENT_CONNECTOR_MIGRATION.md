# PHASE 10K8ZGH Odds-Data Live Client Connector Migration

## Executive Summary
Phase 10K8ZGH is a connector-owned, disabled migration phase. The odds/sportsbook live-client shape has been represented under `src.connectors.odds_data` using vendor-neutral, import-safe, disabled surfaces. No live API calls were authorized, no credentials were read at import time, and no legacy modules were deleted.

## Current HEAD
`6b7d2922adece8b1dc3493f1b4582a9acb4fbb9f`

## Purpose
Move the odds-data live-client shape into canonical connector ownership without activating live access.

## Scope
Reviewed legacy surfaces:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

Canonical connector surfaces created or retained in this batch:
- `src/connectors/odds_data/__init__.py`
- `src/connectors/odds_data/client.py`
- `src/connectors/odds_data/read_only.py`
- `src/connectors/odds_data/adapter.py`
- `src/connectors/odds_data/contracts.py`
- `src/connectors/odds_data/models.py`
- `src/connectors/odds_data/payloads.py`
- `src/connectors/odds_data/configuration.py`
- `src/connectors/odds_data/auth.py`
- `src/connectors/odds_data/transport.py`
- `src/connectors/odds_data/readiness.py`
- `src/connectors/odds_data/source_profile.py`
- `src/connectors/odds_data/live_client.py`
- `src/connectors/odds_data/disabled_client.py`

## Non-Goals
- No deletion
- No source migration of live behavior
- No live API calls
- No credential reads at import time
- No request signing execution
- No scraping
- No broker execution
- No bet execution
- No AI/LLM calls
- No dashboard rewrite
- No main.py rewrite
- No route rewrite

## Big-Picture Architecture
- `src.connectors` owns raw external access boundaries.
- `src.providers` owns normalized provider/category logic.
- `src.services` orchestrates later.
- `src.core` calculates later.
- `src.ai` reasons later.
- `src.brokerage` executes later.
- `src.connectors.market_data` remains reserved for future stock / 0DTE live access.

## Classification Tags
- `CONNECTOR_READY_INERT`
- `CONNECTOR_READY_WITH_STUBS`
- `PROVIDER_NORMALIZATION_ONLY`
- `SERVICE_ORCHESTRATION_ONLY`
- `RUNTIME_LIVE_CLIENT_OWNER`
- `CREDENTIAL_RISK`
- `NETWORK_RISK`
- `DELETE_READY_AFTER_CONNECTOR_MIGRATION`
- `UNSAFE_TO_TOUCH`

## Live-Client Shape Transported
The connector boundary now carries the live-client shape as disabled ownership metadata and inert method shells:
- configuration boundaries
- auth requirement boundaries
- transport boundaries
- readiness/status boundaries
- source profile metadata
- disabled live-client shells
- payload handling already present in the read-only connector scaffold

## Connector-Owned Modules Created
The new canonical connector-owned modules in this phase are:
- `configuration.py`
- `auth.py`
- `transport.py`
- `readiness.py`
- `source_profile.py`
- `live_client.py`
- `disabled_client.py`

These modules are import-safe and contain no live network calls or credential reads.

## Credentials as Data Only
Credential names are represented as configuration metadata only. No secret values are loaded at import time. Live access stays disabled until a future phase explicitly authorizes it.
No credentials were read at import time.

## Disabled Live Methods
The connector-owned live methods raise `ConnectorDisabledError` instead of performing live access. That keeps the boundary import-safe while preserving the callable surface for later migration.

## Legacy Modules Reviewed
- `sharp_client.py` remains the legacy live client owner.
- `betting_providers/sharp_api.py` remains a legacy vendor adapter.
- `betting_providers/the_odds_api.py` remains a legacy sportsbook adapter.
- `betting_providers/sportsgameodds.py` remains a legacy sportsbook adapter.
- `automation_scheduler/sharp_sportsbook_adapter.py` remains a legacy read-only bridge.
- `automation_scheduler/sportsbook_odds_provider.py` remains a legacy snapshot bridge.
- `providers/sharp_provider.py` remains split between normalization and live enrichment.

## Compatibility Policy
Legacy modules remain importable. They are preserved for compatibility and proof only. No file was deleted in this phase.

## Delete-Readiness
The legacy odds/sportsbook live-client modules are not deleted yet. They remain delete-ready only after downstream import redirection, compatibility proof, and connector transport proof are complete.

## Remaining Work
- Redirect any remaining odds/sportsbook runtime consumers to connector-owned disabled surfaces.
- Split any remaining mixed legacy normalization from live-access behavior.
- Prove deletion safety for legacy live-client modules in a later phase.

## Next Recommended Phase
Odds-data consumer redirection and deletion proof for the remaining legacy bridge surfaces.

## Required Statement
Odds-data live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, scraping, broker execution, bet execution, AI/LLM calls, route rewrites, or deletion of legacy modules.

## Safety Summary
No deletion occurred. No source migration of live behavior occurred. No live calls were made.
