# PHASE 10K8ZGQ Prediction-Market Runtime Consumer Redirection

## Executive Summary
This phase redirects the remaining prediction-market runtime consumer away from the legacy Kalshi provider shell and into canonical service, connector, and provider boundaries.

Prediction-market runtime consumers are now routed through `src.services.prediction_market_runtime_bridge`, which composes `src.connectors.prediction_market_data` and `src.providers.prediction_markets`.

> Prediction-market runtime consumers are redirected away from legacy prediction-market shells in this phase. This phase does not authorize live API calls, credential reads, trade execution, connector activation, or deletion.

## Current HEAD
`0663a8ef9e0169c3844e0326986e84133aae3ca2`

## Purpose
Move runtime coupling off `providers.kalshi_provider` while keeping the current enrichment contract stable.

## Scope
- `src/services/enrichment_service.py`
- `src/services/prediction_market_runtime_bridge.py`
- Canonical connector and provider imports only

## Non-Goals
- No deletion
- No live API calls
- No credential reads at import time
- No scraping
- No broker execution
- No bet/trade execution
- No AI/LLM calls
- No dashboard rewrite
- No main.py rewrite
- No broad route rewrite
- No connector activation

## Relationship to 10K8ZGP
10K8ZGP removed the odds compatibility shells and left the odds flow intact. This phase follows that cleanup by redirecting the remaining prediction-market runtime consumer away from the legacy Kalshi shell.

## Runtime Consumer Redirection
`src/services/enrichment_service.py` now imports:
- `src.services.odds_runtime_bridge.enrich_with_sharp`
- `src.services.prediction_market_runtime_bridge.enrich_with_kalshi`

The legacy import:
- `from providers.kalshi_provider import enrich_with_kalshi`

is no longer used by the runtime service.

## Canonical Prediction-Market Flow After Redirection
`src.services.prediction_market_runtime_bridge`
-> `src.connectors.prediction_market_data`
-> `src.providers.prediction_markets`

## Legacy Modules Preserved
These files remain on disk for compatibility and future proof/deletion work:
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Delete-Readiness Status
The legacy prediction-market shells are **not deleted** in this phase. They remain blocked by legacy compatibility history, direct shell references, and live-method retirement work that has not yet been completed for prediction-market surfaces.

## No-Network Guarantee
The bridge and service redirect are import-safe and do not initiate network access.

## No-Credential Guarantee
The bridge and service redirect do not read credentials or environment secrets at import time.

## No-Execution Guarantee
The bridge is read-only and does not execute trades, bets, or live prediction-market actions.

## Next Recommended Phase
Proceed to `10K8ZGR Prediction-Market Legacy Live-Method Retirement Proof`.
