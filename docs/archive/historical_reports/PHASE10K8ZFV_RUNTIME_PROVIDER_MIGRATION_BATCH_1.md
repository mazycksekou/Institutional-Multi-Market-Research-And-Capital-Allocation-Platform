# PHASE10K8ZFV Runtime Provider Migration Batch 1

## Executive Summary
Runtime provider migration has begun at the read-only adapter layer only. This phase does not authorize live connectors, scraping, brokerage execution, AI/LLM calls, credential access, or deletion of legacy runtime modules.

The first safe slice moved into canonical ownership is local-only category adapter logic for prediction markets, sportsbooks, and zero-DTE stocks. Legacy imports remain available through compatibility wrappers.

## Big-Picture Architecture
- `src/connectors/` fetches raw external data later.
- `src/providers/` normalizes product-category meaning.
- `src/core/` keeps math and risk logic.
- `src/ai/` remains a future reasoning boundary.
- `src/brokerage/` remains a future execution boundary.

## What Read-Only Means
Read-only adapter logic may:
- normalize payloads
- validate payloads
- map vendor-shaped data into canonical category contracts
- shape provider health/status objects
- construct local quote/model objects

Read-only adapter logic may not:
- call live APIs
- read credentials
- scrape
- submit orders
- place bets
- execute trades
- own orchestration
- make strategy decisions

## What Adapter-Level Means
Adapter-level code translates external-shaped payloads into internal canonical objects. It does not fetch network data or perform execution. It belongs beside the product category contract, not beside live clients.

## Files Reviewed
- `providers/kalshi_provider.py`
- `betting_providers/normalization.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/the_odds_api.py`
- `src/providers/contracts.py`
- `src/providers/normalization.py`
- `src/providers/validation.py`
- `src/providers/prediction_markets/contracts.py`
- `src/providers/sportsbooks/contracts.py`
- `src/providers/zero_dte_stocks/contracts.py`

## Files Migrated Or Copied
- `src/providers/prediction_markets/models.py`
- `src/providers/prediction_markets/adapters.py`
- `src/providers/sportsbooks/models.py`
- `src/providers/sportsbooks/adapters.py`
- `src/providers/zero_dte_stocks/models.py`
- `src/providers/zero_dte_stocks/adapters.py`
- `providers/kalshi_provider.py` normalization now delegates to canonical prediction-market adapter logic
- `betting_providers/normalization.py` now delegates sportsbook and prediction-market normalization to canonical adapter logic

## Files Deferred
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/provider_router.py`
- `providers/sharp_provider.py`
- `providers/odds_provider_router.py`
- `src/services/enrichment_service.py`
- `screenshot_intake.py`

## Compatibility Wrappers Preserved
Legacy imports remain operational, including:
- `providers.kalshi_provider.normalize_kalshi_probability_market`
- `betting_providers.normalization.normalize_kalshi_event`
- `betting_providers.normalization.normalize_kalshi_market`
- `betting_providers.normalization.normalize_sportsbook_event`
- `betting_providers.normalization.normalize_sportsbook_odds`

## No-Network Guarantee
The new canonical adapter/model modules are import-safe and local-only. They do not import `requests`, `httpx`, `yfinance`, `selenium`, `playwright`, or broker SDKs.

## No-Credential Guarantee
The new canonical adapter/model modules do not read environment credentials at import time.

## No-Execution Guarantee
The new canonical adapter/model modules do not submit orders, place bets, trade, scrape, or call AI systems.

## Test Summary
- Targeted provider-migration tests passed.
- Existing provider foundation tests passed.
- Compatibility output checks passed for prediction-market and sportsbook normalization.

## Next Recommended Phase
Proceed to the next runtime provider migration batch for the remaining safe read-only adapter surfaces. Keep live client behavior deferred.

