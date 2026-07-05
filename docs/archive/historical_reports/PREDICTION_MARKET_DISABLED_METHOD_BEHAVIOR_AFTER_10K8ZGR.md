# Prediction-Market Disabled Method Behavior After 10K8ZGR

## Disabled Behavior
- Legacy live methods raise `ConnectorDisabledError`
- No live network access occurs
- No import-time credential reads occur
- Canonical connector/provider/service metadata is still available

## Disabled Method Proof
- `kalshi_client.get_kalshi_market()` -> raises `ConnectorDisabledError`
- `kalshi_client.get_kalshi_orderbook()` -> raises `ConnectorDisabledError`
- `kalshi_client.get_kalshi_market_snapshot()` -> raises `ConnectorDisabledError`
- `KalshiApiAdapter.get_market_events()` -> raises `ConnectorDisabledError`
- `KalshiApiAdapter.get_markets()` -> raises `ConnectorDisabledError`
- `KalshiApiAdapter.get_market_orderbook()` -> raises `ConnectorDisabledError`
- `KalshiReadonlyAdapter.fetch_snapshot()` -> raises `ConnectorDisabledError`

## Metadata / Status Preservation
- `providers.kalshi_provider.enrich_with_kalshi` now delegates to the canonical runtime bridge
- `automation_scheduler.kalshi_market_provider.get_kalshi_snapshot` returns disabled metadata when the adapter is disabled
- `normalize_*` helpers remain available for local-only normalization

## Why No Deletion Occurred
Only live behavior was retired. The modules remain as compatibility shells for later proof-backed deletion.
