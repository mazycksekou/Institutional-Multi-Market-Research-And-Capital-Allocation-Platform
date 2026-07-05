# Connector Disabled Behavior Report After 10K8ZFY

## Executive Summary
The new prediction-market connector wrapper is inert. Its live fetch methods raise explicit disabled errors rather than attempting any external access.

## Disabled Behavior
- fetch_markets() raises ConnectorDisabledError.
- `PredictionMarketReadOnlyClient.fetch_markets()` raises ConnectorDisabledError.
- `PredictionMarketReadOnlyClient.fetch_markets()` raises `ConnectorDisabledError`.
- `PredictionMarketReadOnlyClient.fetch_events()` raises `ConnectorDisabledError`.
- `PredictionMarketReadOnlyClient.fetch_snapshot()` raises `ConnectorDisabledError`.
- `PredictionMarketConnectorAdapter.fetch_markets()` raises `ConnectorDisabledError`.
- `PredictionMarketConnectorAdapter.fetch_events()` raises `ConnectorDisabledError`.
- `PredictionMarketConnectorAdapter.fetch_snapshot()` raises `ConnectorDisabledError`.

## Why This Matters
The connector boundary is proven import-safe without permitting live access. Future phases can replace the disabled methods only after connector transport is explicitly approved.
