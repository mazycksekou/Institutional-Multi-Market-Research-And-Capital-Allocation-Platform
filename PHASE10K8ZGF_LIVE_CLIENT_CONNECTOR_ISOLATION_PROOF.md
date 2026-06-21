# PHASE 10K8ZGF Live Client Connector Isolation Proof

## Executive Summary
Phase 10K8ZGF is a proof/planning phase only. No deletion occurred. No source migration occurred. No live calls were made.

The repository has already completed the provider foundation cleanup. The remaining live-client surfaces now need to be isolated into `src.connectors` before any legacy live-client modules can be deleted.

## Current HEAD
`0e4d5e6e68e4609a5ef390fed46360cbc3a3886d`

## Purpose
Audit and isolate the remaining live-client, adapter, and vendor API surfaces before any connector migration or deletion batch.

## Scope
Reviewed targets:
- `kalshi_client.py`
- `sharp_client.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `src/api/market_metadata_routes.py`
- `src/api/model_card_service.py`
- `screenshot_intake.py`
- `main.py`
- `streamlit_app.py`

## Non-Goals
- No deletion
- No source migration
- No behavior changes
- No live API calls
- No credential reads
- No env secret reads
- No scraping
- No broker execution
- No AI/LLM calls
- No dashboard rewrite
- No main.py rewrite
- No route rewrite
- No connector activation

## Big-Picture Architecture
- `src.connectors` owns future raw external data access.
- `src.providers` owns normalized provider/category logic.
- `src.services` orchestrates later.
- `src.core` calculates later.
- `src.ai` reasons later.
- `src.brokerage` executes later.

## Required Statement
Live-client functionality must be isolated into src.connectors before legacy live-client modules are deleted. This phase does not authorize live API calls, credential reads, scraping, broker execution, AI/LLM calls, source migration, or deletion.

## Live-Client Surfaces Reviewed

### Prediction-Market Surfaces
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

### Odds / Sportsbook Surfaces
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

### Bridge / Orchestration Surfaces
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `src/api/market_metadata_routes.py`
- `src/api/model_card_service.py`
- `screenshot_intake.py`
- `main.py`
- `streamlit_app.py`

## Connector Destinations

### `src.connectors.prediction_market_data`
Future home for:
- `kalshi_client.py` raw market/orderbook fetches
- `providers/kalshi_provider.py::enrich_with_kalshi`
- `betting_providers/kalshi_api.py::KalshiApiAdapter`
- `automation_scheduler/kalshi_readonly_adapter.py::KalshiReadonlyAdapter`
- `automation_scheduler/kalshi_market_provider.py::get_kalshi_snapshot`

### `src.connectors.odds_data`
Future home for:
- `sharp_client.py`
- `providers/sharp_provider.py::enrich_with_sharp`
- `betting_providers/sharp_api.py::SharpApiAdapter`
- `betting_providers/the_odds_api.py::TheOddsApiAdapter`
- `betting_providers/sportsgameodds.py::SportsGameOddsAdapter`
- `automation_scheduler/sharp_sportsbook_adapter.py::SharpSportsbookAdapter`
- `automation_scheduler/sportsbook_odds_provider.py::get_sportsbook_snapshot`

### `src.connectors.market_data`
No reviewed live-client surface currently belongs directly here in this batch. It remains reserved for future stock / 0DTE live-access wrappers.

## Provider Normalization Only
These surfaces should live in `src.providers` rather than `src.connectors`:
- `providers/kalshi_provider.py::normalize_kalshi_probability_market`
- `betting_providers/kalshi_api.py` normalization of Kalshi events/markets
- `betting_providers/the_odds_api.py` normalization of sportsbook events/odds
- `automation_scheduler/kalshi_market_provider.py::normalize_kalshi_snapshot`, `validate_kalshi_snapshot`, `summarize_kalshi_snapshot`
- `automation_scheduler/sharp_sportsbook_adapter.py::normalize_sportsbook_snapshot`, `validate_sportsbook_snapshot`, `summarize_sportsbook_snapshot`

## Service Orchestration Only
These surfaces should live in `src.services` or remain thin API shells:
- `src/services/enrichment_service.py`
- `src/api/provider_status_routes.py`
- `src/api/market_metadata_routes.py`
- `src/api/model_card_service.py`
- `screenshot_intake.py`

## Credential-Risk Findings
- `kalshi_client.py` reads `KALSHI_BASE_URL` at import time.
- `providers/kalshi_provider.py` reads `KALSHI_ENABLED` and `KALSHI_BASE_URL`.
- `providers/sharp_provider.py` reads `SHARP_API_KEY` and `SHARP_API_BASE_URL`.
- `betting_providers/kalshi_api.py` reads `KALSHI_ENV`, `KALSHI_BASE_URL`, `KALSHI_API_KEY_ID`, and `KALSHI_PRIVATE_KEY`.
- `betting_providers/sharp_api.py` reads `SHARP_API_KEY` and `SHARP_API_BASE_URL`.
- `betting_providers/the_odds_api.py` reads `THE_ODDS_API_KEY`, `ODDS_API_KEY`, and multiple default env vars.
- `betting_providers/sportsgameodds.py` reads `SPORTSGAMEODDS_API_KEY` and `SPORTSGAMEODDS_BASE_URL`.
- `automation_scheduler/kalshi_readonly_adapter.py` reads `KALSHI_API_KEY`, `KALSHI_API_SECRET`, and related env vars.
- `automation_scheduler/sharp_sportsbook_adapter.py` reads `SHARP_API_KEY`, `SHARP_API_BASE_URL`, and related env vars.
- `main.py` reads `ACTION_API_KEY`, which keeps it in entrypoint/orchestration territory, not deletion territory.

## Network-Risk Findings
- `kalshi_client.py` uses `requests`.
- `sharp_client.py` uses `requests`.
- `providers/kalshi_provider.py` uses `requests`.
- `providers/sharp_provider.py` uses `requests`.
- `betting_providers/kalshi_api.py` uses `requests`.
- `betting_providers/sharp_api.py` uses `requests`.
- `betting_providers/the_odds_api.py` uses `httpx.AsyncClient`.
- `betting_providers/sportsgameodds.py` uses `httpx.AsyncClient`.
- `automation_scheduler/kalshi_readonly_adapter.py` uses `httpx`.
- `automation_scheduler/sharp_sportsbook_adapter.py` uses `httpx`.
- `src/api/provider_status_routes.py` and `src/api/market_metadata_routes.py` are bridge layers to legacy runtime state, not live network clients themselves.
- `main.py` imports `yfinance`, but it remains an orchestration shell and is not an automatic deletion candidate.

## Delete-Readiness Findings
- `kalshi_client.py` and `sharp_client.py` are `DELETE_READY_AFTER_CONNECTOR_MIGRATION`.
- `providers/kalshi_provider.py` and `providers/sharp_provider.py` are `DELETE_READY_AFTER_CONNECTOR_MIGRATION` after the normalization half and live half are split.
- `betting_providers/kalshi_api.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, and `betting_providers/sportsgameodds.py` are `DELETE_READY_AFTER_CONNECTOR_MIGRATION` after connector transport and test redirection.
- `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/kalshi_market_provider.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, and `automation_scheduler/sportsbook_odds_provider.py` are `CONNECTOR_READY_WITH_STUBS` candidates, not delete-ready yet.
- `main.py` and `streamlit_app.py` are not deletion candidates.

## Recommended Next 3 Phases
1. Prediction-market connector transport batch for `kalshi_client.py`, `providers/kalshi_provider.py`, `betting_providers/kalshi_api.py`, and `automation_scheduler/kalshi_*`.
2. Odds-data connector transport batch for `sharp_client.py`, `providers/sharp_provider.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, `betting_providers/sportsgameodds.py`, and `automation_scheduler/sharp_*`.
3. Service bridge thinning for `src/services/enrichment_service.py`, `src/api/provider_status_routes.py`, `src/api/market_metadata_routes.py`, `src/api/model_card_service.py`, and `screenshot_intake.py`.

## Safety Summary
No deletion occurred. No source migration occurred. No live imports were introduced by this phase.

## Why No Deletion Occurred
The live-client and adapter surfaces still own credential-gated and network-gated behavior, so this phase documents transport paths and delete-readiness only. `main.py` and `streamlit_app.py` are not deletion candidates.
