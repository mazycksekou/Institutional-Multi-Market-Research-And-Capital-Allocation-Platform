# Odds Data Disabled Behavior Report After 10K8ZFZ

## Executive Summary
The new odds-data connector wrapper is inert. Its live fetch methods raise explicit disabled errors rather than attempting any external access.

## Disabled Behavior
- fetch_odds() raises ConnectorDisabledError.
- `OddsDataReadOnlyClient.fetch_odds()` raises `ConnectorDisabledError`.
- `OddsDataReadOnlyClient.fetch_events()` raises `ConnectorDisabledError`.
- `OddsDataReadOnlyClient.fetch_snapshot()` raises `ConnectorDisabledError`.
- `OddsDataConnectorAdapter.fetch_odds()` raises `ConnectorDisabledError`.
- `OddsDataConnectorAdapter.fetch_events()` raises `ConnectorDisabledError`.
- `OddsDataConnectorAdapter.fetch_snapshot()` raises `ConnectorDisabledError`.

## Why This Matters
The connector boundary is proven import-safe without permitting live access. Future phases can replace the disabled methods only after connector transport is explicitly approved.
