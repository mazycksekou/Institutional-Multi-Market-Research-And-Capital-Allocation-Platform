# PHASE10K8ZFZ Odds Data Connector Batch 2

## Executive Summary
10K8ZFZ applies the inert connector-wrapper pattern to sportsbook and odds data. The canonical odds-data connector boundary lives under `src/connectors/odds_data` and provides local-only models, payload normalization, disabled fetch methods, and compatibility-safe adapter/client entrypoints without enabling live access.

## Current HEAD
`f18bcc6`

## Purpose
Prove the connector-wrapper pattern for odds data while keeping live access disabled and preserving legacy imports.

## Scope
- Create inert odds-data connector modules.
- Add disabled read-only client and adapter surfaces.
- Add local-only payload normalization and validation helpers.
- Document compatibility and deferred live behavior.
- Verify legacy imports still resolve.

## Non-Goals
- No live odds API calls.
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

## What Odds-Data Connector Wrapper Means
odds-data connector wrapper means a vendor-neutral, inert boundary that can represent external odds access without enabling it. It may define models, adapters, payload helpers, and disabled client methods, but it does not fetch live data or read secrets.

## What Moved Or Was Created
- `src/connectors/odds_data/client.py`
- `src/connectors/odds_data/read_only.py`
- `src/connectors/odds_data/adapter.py`
- `src/connectors/odds_data/models.py`
- `src/connectors/odds_data/payloads.py`
- `src/connectors/odds_data/__init__.py` exports

## Reviewed Legacy Modules
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `sharp_client.py`
- `providers/odds_provider_router.py`
- `betting_providers/provider_router.py`

## Live Behavior Remains Deferred
- Live odds API calls.
- Credential reads.
- External transport and retry logic.
- Vendor-specific runtime behavior.

## Why Vendor-Neutral Naming Was Used
The canonical connector package must not be owned by vendor names. `odds_data` is the product-category boundary; Sharp, The Odds API, and SportsGameOdds remain legacy evidence only.

## What Compatibility Remains
- Legacy sportsbook/odds imports continue to resolve.
- Existing runtime provider modules remain unchanged.
- No legacy deletion occurred.
- No compatibility break was introduced.

## Why No Deletion Occurred
The connector wrapper is still the first inert migration batch. Deletion can only be considered after dependency proof, wrapper verification, and test redirection.

## No-Network Guarantee
The new connector modules do not import live network libraries and do not perform live access at import time.

## No-Credential Guarantee
The new connector modules do not read environment credentials at import time and do not require secrets to import or validate local-only payloads.

## No-Execution Guarantee
The new connector modules do not place bets, execute trades, or make strategy decisions.

## Test Summary
The phase test verifies import safety, disabled fetch behavior, legacy import compatibility, and canonical naming rules.

## Next Recommended Phase
Proceed to the market-data connector wrapper batch using the same inert pattern before any live client transport.

## Required Statement
Odds-data connector migration has begun only as an inert read-only connector wrapper. This phase does not authorize live odds API calls, credential reads, scraping, AI/LLM calls, broker execution, route rewrites, or deletion of legacy modules.
