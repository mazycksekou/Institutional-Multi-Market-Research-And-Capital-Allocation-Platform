# PHASE10K8ZFW Runtime Provider Migration Batch 2

## Executive Summary
10K8ZFW moves the remaining read-only provider helper layer into canonical `src/providers` ownership and introduces a router split plan that classifies providers by product category first. The phase keeps legacy live router behavior intact and preserves compatibility wrappers.

## Current HEAD
`31c2656`

## Purpose
Move pure helper logic and local router classification logic into canonical product-category-owned modules without changing runtime behavior.

## Scope
- `src/providers/compat.py`
- `src/providers/categories.py`
- `src/providers/routing.py`
- `betting_providers/base.py`
- `providers/base_provider.py`
- `betting_providers/provider_router.py`
- supporting tests and reports

## Non-Goals
- No live connectors
- No scraping
- No broker execution
- No AI/LLM calls
- No credential access
- No deletion of legacy runtime modules
- No main.py rewrite
- No streamlit_app.py rewrite
- No broad API route rewrite

## Relationship to 10K8ZFV
10K8ZFV introduced the first read-only category adapters. 10K8ZFW extends that work by centralizing the pure helper layer and adding category-based router classification.

## What Helper Logic Moved
- `env_bool`
- compatibility error helpers
- `ProviderAdapter`
- `available`
- `unavailable`
- `provider_error`
- product-category classification helpers
- category-to-package resolution helpers

## What Router Logic Moved
- Product-category resolution now lives in `src.providers.routing`
- Legacy router default-provider resolution reuses canonical routing helpers
- Legacy router compatibility behavior remains unchanged

## What Was Intentionally Deferred
- Live adapter migration
- Network client migration
- Scraping
- Broker/execution logic
- AI/LLM logic
- Broad route rewrites
- `main.py`
- `streamlit_app.py`
- API route ownership changes

## Which Legacy Routers Remain
- `betting_providers.provider_router`
- `providers.odds_provider_router`
- legacy live provider adapters

## Which Import Paths Are Now Compatibility Wrappers
- `betting_providers.base`
- `providers.base_provider`
- legacy provider router import paths continue to resolve

## Why Main, Streamlit, and API Routes Were Not Rewritten
They still depend on the legacy router/runtime assembly and are not part of the safe read-only helper migration boundary.
API routes remain unchanged.

## Deletion Readiness Status
Not ready. Legacy runtime modules remain required until later migration batches prove replacement coverage.

## Test Summary
- New helper/router migration test added
- Existing provider foundation and adapter compatibility tests remain green

## Next Recommended Migration Batch
Proceed to the next safe runtime provider batch or the router compatibility verification phase.

## Required Statement
Runtime provider migration is still limited to read-only helper and adapter layers. This phase does not authorize live connectors, scraping, brokerage execution, AI/LLM calls, credential access, broad route rewrites, or deletion of legacy runtime modules.
