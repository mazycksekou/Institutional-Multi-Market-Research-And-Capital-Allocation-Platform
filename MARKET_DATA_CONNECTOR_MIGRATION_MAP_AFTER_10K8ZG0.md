# MARKET_DATA_CONNECTOR_MIGRATION_MAP_AFTER_10K8ZG0

## Current Market-Data Boundary
- `src/connectors/market_data/contracts.py`
- `src/connectors/market_data/models.py`
- `src/connectors/market_data/payloads.py`
- `src/connectors/market_data/read_only.py`
- `src/connectors/market_data/client.py`
- `src/connectors/market_data/adapter.py`

## Future Relationship To zero_dte_stocks
- `market_data` is the raw-access boundary.
- `zero_dte_stocks` is the future product-category normalization boundary.

## Vendor-Neutral Ownership Policy
Canonical ownership stays product-oriented and does not adopt vendor names.

## What Was Created
- Read-only client surface.
- Disabled adapter surface.
- Quote and snapshot models.
- Payload normalization and validation.

## What Remains Deferred
- Live market-data clients.
- Vendor API transports.
- Credential reads.
- Scraping and websocket feeds.

## Compatibility Notes
- The new connector wrapper is inert.
- No legacy modules were deleted.
