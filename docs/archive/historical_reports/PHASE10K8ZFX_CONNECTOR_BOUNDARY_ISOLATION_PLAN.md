# PHASE10K8ZFX Connector Boundary Isolation Plan

## Executive Summary
10K8ZFX establishes `src/connectors` as the future home for raw external access while keeping `src.providers` focused on read-only normalization. This is an isolation and planning phase only. It identifies live-fetch, credential, scraper, websocket, and feed behavior that still lives in legacy provider or scheduler modules and maps it to future connector categories without activating anything.

## Current HEAD
`e58b1f3`

## Purpose
Separate provider normalization from live external access before any connector implementation begins. Providers normalize already-supplied data. Connectors own future live external access.

## Scope
- Audit live-fetch/network/client/credential/scraper/feed candidates.
- Map each candidate to a future connector category or mark it deferred.
- Introduce inert connector contracts and category scaffolds.
- Document which provider modules still depend on live-fetch behavior.

## Non-Goals
- No live API calls.
- No scraping implementation.
- No websocket feed implementation.
- No credential reads.
- No broker execution.
- No AI/LLM calls.
- No deletion of legacy runtime modules.
- No broad API route rewrites.

## Big-Picture Architecture
- `src/connectors` = raw external access, future APIs, feeds, scraping, websocket clients.
- `src/providers` = read-only product-category normalization and routing.
- `src/core` = math, risk, statistics.
- `src/services` = application orchestration.
- `src/api` = HTTP routes.
- `src/ai` = future AI/LLM reasoning.
- `src/brokerage` = future execution.

## What Belongs in `src/connectors`
- Contracts for raw external data access.
- Inert models for connector requests, responses, and health.
- In-memory registry scaffolds.
- Boundary policies that prohibit live access in the scaffold stage.
- Category contract surfaces for `market_data`, `odds_data`, `prediction_market_data`, `web_scraping`, and `feeds`.

## What Belongs in `src/providers`
- Product-category normalization.
- Read-only adapter models.
- Routing by product category.
- Validation and health summaries that assume payloads already exist.
- No live-fetch ownership.

## Boundary Rules
The connector boundary is strict:
- Providers do not own live fetch behavior.
- Connectors own future live external access.
- Live fetch behavior may only move once the corresponding connector contract is stable.
- Network behavior stays out of the provider package.

## Live-Fetch / Network / Client / Credential / Scraper / Feed Candidates

| Module | Observed behavior | Future connector category | Status |
| --- | --- | --- | --- |
| `providers/kalshi_provider.py` | `requests`, env-gated live call | `src/connectors/prediction_market_data` | unsafe until split |
| `providers/sharp_provider.py` | `requests`, env-gated live call | `src/connectors/odds_data` | unsafe until split |
| `betting_providers/kalshi_api.py` | live Kalshi client, credential reads | `src/connectors/prediction_market_data` | unsafe until split |
| `betting_providers/sharp_api.py` | live Sharp client, credential reads | `src/connectors/odds_data` | unsafe until split |
| `betting_providers/the_odds_api.py` | live odds API client | `src/connectors/odds_data` | unsafe until split |
| `betting_providers/sportsgameodds.py` | live odds API client | `src/connectors/odds_data` | unsafe until split |
| `automation_scheduler/kalshi_readonly_adapter.py` | live read-only client plus normalization | split between `src/connectors/prediction_market_data` and `src/providers/prediction_markets` | deferred |
| `automation_scheduler/kalshi_market_provider.py` | read-only provider normalization | `src/providers/prediction_markets` | safe later |
| `automation_scheduler/sharp_sportsbook_adapter.py` | live odds access plus shaping | split between `src/connectors/odds_data` and `src/providers/sportsbooks` | deferred |
| `automation_scheduler/sportsbook_odds_provider.py` | live odds shaping | `src/providers/sportsbooks` or `src/connectors/odds_data` depending split | deferred |
| `automation_scheduler/calibration_collector.py` | `httpx`, credential/env reads, live pull | `src/connectors/market_data` | unsafe until split |
| `automation_scheduler/ncaaf_collegefootballdata_adapter.py` | `urllib`, live college football data pulls | `src/connectors/market_data` | unsafe until split |
| `automation_scheduler/collector_scheduled_runner.py` | token-gated operational endpoint | `src/services` / `src/api` orchestration only | deferred |
| `automation_scheduler/institutional_deepseek_review.py` | external AI/LLM request path | `src/ai/evaluation` | not a connector owner |
| `screenshot_intake.py` | screenshot/scraping intake path | `src/connectors/web_scraping` | unsafe until split |
| `src/services/enrichment_service.py` | service-layer orchestration | `src/services` | not a connector owner |

## Future Connector Category Map
- `src/connectors/market_data` for raw market and calibration feeds.
- `src/connectors/odds_data` for odds and sportsbook feed access.
- `src/connectors/prediction_market_data` for prediction-market vendor access.
- `src/connectors/web_scraping` for scrape/intake boundaries.
- `src/connectors/feeds` for feed-style push or polling contracts.

## Deferred Modules
- Live clients.
- Credential readers.
- Scraper entrypoints.
- Websocket/feed implementations.
- Any module that mixes live fetch with normalization.

## Safe Future Connector Migration Targets
- `src/connectors/contracts.py`
- `src/connectors/errors.py`
- `src/connectors/models.py`
- `src/connectors/registry.py`
- `src/connectors/policy.py`
- `src/connectors/market_data/contracts.py`
- `src/connectors/odds_data/contracts.py`
- `src/connectors/prediction_market_data/contracts.py`
- `src/connectors/web_scraping/contracts.py`
- `src/connectors/feeds/contracts.py`

## Unsafe Modules
- Any module that reads credentials at import time.
- Any module that executes network calls at import time.
- Any module that performs scraping or websocket access.
- Any module that performs broker or trade execution.
- Any module that mixes live access with provider normalization.

## Provider / Connector Split Summary
Providers normalize already-supplied data. Connectors own future live external access. This phase does not authorize live API calls, scraping, websocket feeds, credential reads, broker execution, AI/LLM calls, or deletion of legacy runtime modules.

## Next Recommended Phase
Move the pure live-fetch boundary surfaces into inert connector contracts first, then split the first live client batch into `src/connectors` with compatibility wrappers.

