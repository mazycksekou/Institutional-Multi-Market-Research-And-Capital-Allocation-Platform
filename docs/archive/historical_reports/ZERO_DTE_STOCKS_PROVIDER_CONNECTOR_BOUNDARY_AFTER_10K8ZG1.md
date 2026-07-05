# ZERO_DTE_STOCKS_PROVIDER_CONNECTOR_BOUNDARY_AFTER_10K8ZG1

## Boundary Rule
`src.connectors.market_data` supplies raw payload objects.
`src.providers.zero_dte_stocks` consumes those supplied objects and normalizes them.

## What Must Not Cross the Boundary
- No live fetch calls from provider code.
- No credential reads.
- No broker execution.
- No strategy decisions.

## Consumption Paths
- Raw mapping payloads.
- `MarketDataQuote`
- `MarketDataSnapshot`

## Safety Statement
The provider boundary is read-only and import-safe.

## Compatibility Notes
- Legacy provider adapter behavior remains available.
- No deletion occurred.
