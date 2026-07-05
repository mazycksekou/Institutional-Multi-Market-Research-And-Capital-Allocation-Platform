# ZERO_DTE_STOCKS_PROVIDER_MIGRATION_MAP_AFTER_10K8ZG1

## Provider Boundary
- `src/providers/zero_dte_stocks/provider.py`
- `src/providers/zero_dte_stocks/normalization.py`
- `src/providers/zero_dte_stocks/models.py`
- `src/providers/zero_dte_stocks/adapters.py`

## Connector Consumption
The provider consumes supplied `MarketDataQuote` and `MarketDataSnapshot` objects from `src.connectors.market_data`.

## What Was Created
- Read-only provider wrapper.
- Provider-owned quote and snapshot normalization.
- Provider status model.
- Disabled live-fetch methods.

## What Remains Deferred
- Live market-data clients.
- Vendor-specific transports.
- Any execution or strategy decision layer.

## Compatibility Notes
- Existing adapter imports remain available.
- The canonical provider boundary stays read-only.
