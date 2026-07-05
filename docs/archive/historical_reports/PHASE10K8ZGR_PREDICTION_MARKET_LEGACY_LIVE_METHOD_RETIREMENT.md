# PHASE 10K8ZGR Prediction-Market Legacy Live-Method Retirement

## Executive Summary
This phase retires live behavior inside the legacy prediction-market shell files while keeping the public compatibility symbols on disk.

The canonical ownership remains:
- `src.connectors.prediction_market_data`
- `src.providers.prediction_markets`
- `src.services.prediction_market_runtime_bridge`

The legacy files are now disabled compatibility shells.

> Prediction-market live-method migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.

## Current HEAD
`ed4dca2f0998fb699afd117f7c0b49ad06b5753b`

## Purpose
Retire live network and signing behavior from the remaining legacy prediction-market files without deleting the files.

## Scope
Targets:
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Non-Goals
- No deletion
- No live API calls
- No credential reads at import time
- No request signing
- No network activation
- No AI/LLM
- No broker execution
- No dashboard rewrite
- No main.py rewrite

## Big-Picture Architecture
`src.services.prediction_market_runtime_bridge`
-> `src.connectors.prediction_market_data`
-> `src.providers.prediction_markets`

The legacy files now return disabled metadata or raise `ConnectorDisabledError` for live methods.

## Exact Live Methods Retired
- `kalshi_client.get_kalshi_market`
- `kalshi_client.get_kalshi_orderbook`
- `kalshi_client.get_kalshi_market_snapshot`
- `betting_providers.kalshi_api.KalshiApiAdapter.get_supported_sports`
- `betting_providers.kalshi_api.KalshiApiAdapter.get_market_events`
- `betting_providers.kalshi_api.KalshiApiAdapter.get_markets`
- `betting_providers.kalshi_api.KalshiApiAdapter.search_markets`
- `betting_providers.kalshi_api.KalshiApiAdapter.get_market_orderbook`
- `betting_providers.kalshi_api.KalshiApiAdapter._public_get`
- `automation_scheduler.kalshi_readonly_adapter.KalshiReadonlyAdapter.fetch_markets`
- `automation_scheduler.kalshi_readonly_adapter.KalshiReadonlyAdapter.fetch_events`
- `automation_scheduler.kalshi_readonly_adapter.KalshiReadonlyAdapter.fetch_snapshot`

## Compatibility Surfaces Preserved
- `normalize_kalshi_probability_market`
- `enrich_with_kalshi`
- `describe_kalshi_provider`
- `KalshiApiAdapter`
- `KalshiReadonlyAdapter`
- `get_kalshi_snapshot`
- `normalize_kalshi_snapshot`
- `validate_kalshi_snapshot`
- `write_kalshi_snapshot`
- `summarize_kalshi_snapshot`
- `describe_kalshi_client`

## Why No Deletion Occurred
This phase only disables live behavior and preserves compatibility symbols. Deletion remains a later proof-backed step.

## No-Network Guarantee
The retired methods do not perform live API calls or network activation.

## No-Credential Guarantee
The legacy files no longer read credentials at import time.

## No-Execution Guarantee
The retired methods do not execute trades, bets, or request signing.

## Next Recommended Phase
Proceed to `10K8ZGS Prediction-Market Compatibility Shell Delete-Readiness Proof`.
