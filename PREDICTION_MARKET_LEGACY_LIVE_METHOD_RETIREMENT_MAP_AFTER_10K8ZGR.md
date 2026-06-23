# Prediction-Market Legacy Live-Method Retirement Map After 10K8ZGR

## Legacy Target Map

| Legacy file | Retired live methods | Compatibility symbols preserved | Status |
| --- | --- | --- | --- |
| `kalshi_client.py` | `get_kalshi_market`, `get_kalshi_orderbook`, `get_kalshi_market_snapshot` | `describe_kalshi_client`, module constants | disabled shell |
| `providers/kalshi_provider.py` | network-backed enrichment path | `normalize_kalshi_probability_market`, `enrich_with_kalshi`, `describe_kalshi_provider` | disabled shell |
| `betting_providers/kalshi_api.py` | `get_supported_sports`, `get_market_events`, `get_markets`, `search_markets`, `get_market_orderbook`, `_public_get` | `KalshiApiAdapter`, normalization aliases | disabled shell |
| `automation_scheduler/kalshi_readonly_adapter.py` | `fetch_markets`, `fetch_events`, `fetch_snapshot` | `KalshiReadonlyAdapter`, local config/status helpers | disabled shell |
| `automation_scheduler/kalshi_market_provider.py` | live snapshot acquisition path | `get_kalshi_snapshot`, `normalize_kalshi_snapshot`, `validate_kalshi_snapshot`, `write_kalshi_snapshot`, `summarize_kalshi_snapshot` | compatibility wrapper |

## Canonical Ownership
- `src.connectors.prediction_market_data`
- `src.providers.prediction_markets`
- `src.services.prediction_market_runtime_bridge`

## Status Notes
- No deletion occurred.
- The live methods now reject direct use.
- Compatibility symbols remain importable.
