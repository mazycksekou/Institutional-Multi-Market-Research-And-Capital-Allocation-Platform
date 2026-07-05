# MARKET_DATA_DISABLED_BEHAVIOR_REPORT_AFTER_10K8ZG0

## Disabled Behavior
- `fetch_market_data()` raises `ConnectorDisabledError`.
- `MarketDataReadOnlyClient.fetch_market_data()` raises `ConnectorDisabledError`.
- `MarketDataReadOnlyClient.fetch_quotes()` raises `ConnectorDisabledError`.
- `MarketDataReadOnlyClient.fetch_snapshot()` raises `ConnectorDisabledError`.
- `MarketDataConnectorAdapter.fetch_market_data()` raises `ConnectorDisabledError`.
- `MarketDataConnectorAdapter.fetch_quotes()` raises `ConnectorDisabledError`.
- `MarketDataConnectorAdapter.fetch_snapshot()` raises `ConnectorDisabledError`.

## Why This Matters
The connector boundary is import-safe and inert until a later phase explicitly authorizes live market-data transport.
