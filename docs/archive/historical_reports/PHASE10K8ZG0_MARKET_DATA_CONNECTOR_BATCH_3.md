# PHASE10K8ZG0 Market Data Connector Batch 3

## Executive Summary
10K8ZG0 establishes an inert read-only market-data connector wrapper under `src/connectors/market_data`.
The wrapper is vendor-neutral, import-safe, and intentionally disabled for live access.

## Current HEAD
`9b5ca82`

## Purpose
Create the first market-data connector wrapper layer without activating live market-data access.

## Scope
- Add `src/connectors/market_data` client, adapter, model, payload, and read-only surfaces.
- Keep the package vendor-neutral.
- Preserve compatibility with the existing connector scaffold.

## Non-Goals
- No live market-data API calls.
- No credentials.
- No scraping.
- No broker execution.
- No AI/LLM calls.
- No route rewrites.
- No deletion of legacy modules.

## Big-Picture Architecture
Connectors own future raw external access.
Providers normalize already-supplied payloads.
This phase only creates an inert connector boundary.

## Why market_data Exists Separately From Providers
`market_data` is the raw-access boundary for future market feeds and quote providers.
`src/providers` remains the normalization boundary for product-category meaning.
why market_data exists separately from providers.

## Future Relationship To zero_dte_stocks
`zero_dte_stocks` will consume normalized market data later.
The connector boundary stays separate so raw access does not leak into provider normalization.

## Vendor-Neutral Ownership Policy
Canonical connector names must describe the data domain, not a vendor.
That is why the package is `market_data`, not a vendor-specific module.

## What Was Created
- `src/connectors/market_data/client.py`
- `src/connectors/market_data/models.py`
- `src/connectors/market_data/payloads.py`
- `src/connectors/market_data/read_only.py`
- `src/connectors/market_data/adapter.py`
- exports in `src/connectors/market_data/__init__.py`
- exports in `src/connectors/__init__.py`

## What Remains Deferred
- Live market-data clients.
- Vendor-specific market-data transports.
- Credential loading.
- Any external API call path.
- Any execution or decision logic.

## No-Network Guarantee
The wrapper imports without network libraries and its fetch methods are disabled.

## No-Credential Guarantee
Import-time credential reads are not used.

## No-Execution Guarantee
No trade, order, or broker execution code is introduced.

## Next Recommended Phase
Extend the same inert wrapper pattern for the remaining market-data transport surfaces only after dependency proof.

## Required Statement
Market-data connector migration has begun only as an inert read-only connector wrapper. This phase does not authorize live market-data API calls, credential reads, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.
