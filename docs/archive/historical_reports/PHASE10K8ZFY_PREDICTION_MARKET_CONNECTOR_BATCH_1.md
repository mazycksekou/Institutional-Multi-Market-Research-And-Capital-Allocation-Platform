# PHASE10K8ZFY Prediction Market Connector Batch 1

## Executive Summary
10K8ZFY begins the prediction-market connector migration using an inert read-only wrapper only. The new canonical connector surface lives under `src/connectors/prediction_market_data` and provides local-only models, payload normalization, disabled fetch methods, and compatibility-safe adapter/client entrypoints without enabling live access.

## Current HEAD
`f300a1f`

## Purpose
Prove the connector-wrapper pattern for prediction-market data while keeping live access disabled and preserving legacy imports.

## Scope
- Create inert prediction-market connector modules.
- Add disabled read-only client and adapter surfaces.
- Add local-only payload normalization and validation helpers.
- Document compatibility and deferred live behavior.
- Verify legacy imports still resolve.

## Non-Goals
- No live API calls.
- No credential reads.
- No scraping.
- No AI/LLM calls.
- No broker execution.
- No route rewrites.
- No deletion of legacy modules.

## Big-Picture Architecture
- `src/connectors` owns raw external-access boundaries.
- `src.providers` owns read-only product-category normalization.
- `src.services` will orchestrate later.
- `src.core` will own math/risk/statistics later.
- `src.ai` will own reasoning later.
- `src.brokerage` will own execution later.

## What Connector Wrapper Means
connector wrapper means a vendor-neutral, inert boundary that can represent external data access without enabling it. It may define models, adapters, payload helpers, and disabled client methods, but it does not fetch live data or read secrets.

## What Moved Or Was Created
- `src/connectors/prediction_market_data/client.py`
- `src/connectors/prediction_market_data/read_only.py`
- `src/connectors/prediction_market_data/adapter.py`
- `src/connectors/prediction_market_data/models.py`
- `src/connectors/prediction_market_data/payloads.py`
- `src/connectors/prediction_market_data/__init__.py` exports
- `src/connectors/errors.py` gained `ConnectorDisabledError`
- `src/connectors/__init__.py` exports updated

## Reviewed Legacy Modules
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `kalshi_client.py`

## Live Behavior Remains Deferred
- Live prediction-market API calls.
- Credential reads.
- Signature generation for live requests.
- External transport and retry logic.
- Any scraper, websocket, or broker behavior.

## Why Vendor-Neutral Naming Was Used
The canonical connector package must not be owned by vendor names. `prediction_market_data` is the product-category boundary; Kalshi remains legacy evidence only.

## What Compatibility Remains
- Legacy prediction-market imports continue to resolve.
- Existing runtime provider modules remain unchanged.
- No legacy deletion occurred.
- No compatibility break was introduced.

## Why No Deletion Occurred
The connector wrapper is still the first inert migration batch. Deletion can only be considered after dependency proof, wrapper verification, and test redirection.

## No-Network Guarantee
The new connector modules do not import live network libraries and do not perform live access at import time.

## No-Credential Guarantee
The new connector modules do not read environment credentials at import time and do not require secrets to import or validate local-only payloads.

## Test Summary
The phase test verifies import safety, disabled fetch behavior, legacy import compatibility, and canonical naming rules.

## Next Recommended Phase
Proceed to the next connector migration batch for odds data, using the same inert wrapper pattern before any live client transport.

## Required Statement
Prediction-market connector migration has begun only as an inert read-only connector wrapper. This phase does not authorize live API calls, credential reads, scraping, AI/LLM calls, broker execution, route rewrites, or deletion of legacy modules.
