# PHASE10K8ZFQ_VENDOR_MODULE_AUDIT

## Executive Summary
This phase performed a vendor-module and vendor-reference audit across the repository before any provider migration, automation_scheduler retirement, AI planning, or live connector work. The repository contains multiple vendor-specific adapters, compatibility shells, API routes, tests, docs, and config references. Useful functionality should be transported into canonical product-category packages; non-goal vendor code should be isolated or marked for future deletion after safe verification.

## Why This Phase Exists
Vendor-specific code is still distributed across `betting_providers/`, `providers/`, `automation_scheduler/`, root-level helpers, API routes, and tests. The audit creates a transport and deletion plan so later migration batches can move functionality into product-category ownership without guessing which modules still matter.

## Scope of Vendor Audit
- Tracked files only.
- Vendor names, exchange names, sportsbook names, broker names, market-data vendor names, client names, adapter names, provider routers, registry entries, tests, docs, config/env keys, and string literals.
- Product-goal mapping for prediction markets, 0DTE/stocks, sportsbooks, and non-goal references.

## Search Methodology
- Scanned tracked files with vendor-name and provider-pattern searches.
- Reviewed file names, imports, classes, functions, config keys, doc strings, and test names.
- Grouped findings by product category, runtime criticality, compatibility status, and deletion readiness.

## High-Risk Vendor Dependencies
- Live-call adapters in `betting_providers/*` and legacy `providers/*`.
- `automation_scheduler/kalshi_*` and `automation_scheduler/sharp_*` adapter surfaces.
- Root-level live clients such as `kalshi_client.py` and `sharp_client.py`.
- Legacy consumers such as `src/services/enrichment_service.py`, `screenshot_intake.py`, and API route bridges.
- Vendor-specific env/key surfaces in `.env.example`, `src/api/debug_routes.py`, and scheduler policy modules.

## Product-Category Mapping Summary
- `prediction_markets`: Kalshi and Polymarket references, plus prediction-market scoring and readiness helpers.
- `zero_dte_stocks`: Robinhood, Alpaca, Polygon, IEX, Tradier, Schwab, Yahoo/yfinance, Nasdaq, CME, and related stock/data-source references.
- `sportsbooks`: Sharp, The Odds API, SportsGameOdds, and sportsbook brand references.
- `non-goal / delete candidate`: AI vendors, crypto/exchange vendors, and any broker/trading/external-connector code not required by the product goal.

## Migration / Deletion Policy
- Transport useful vendor functionality into canonical product-category packages.
- Preserve temporary shims until importer scans and wrapper tests are clean.
- Delete vendor-named runtime modules only after their useful functionality is owned by the canonical category package.
- Do not delete or rewrite anything in this phase.

## What Was Not Changed
- No files were deleted.
- No files were moved.
- No source migrations were performed.
- No runtime behavior changed.
- No live API calls were made.
- No credentials were printed or committed.

## Safety Guarantees
- The audit is evidence-only.
- The canonical provider landing zone remains vendor-neutral and product-category based.
- `automation_scheduler` remains a decommission target, not a permanent owner.
- AI, broker, trading, and scraper work remain out of scope.
- This phase does not authorize deletion.

## Test / Smoke Summary
- Local-only vendor inventory and file-content review completed successfully.
- Existing provider skeleton and taxonomy documents were retained and used as context.
- No network-dependent checks were run.

## Next Recommended Phase
Proceed with the first safe transport batch that targets one product category at a time, preserves wrappers, and proves import safety with fake-client tests before any legacy vendor module removal.

## Production Domain Clarification
AI/LLM, brokerage/live-trading, and scraper/live-connector functionality are future production domains, not automatic deletion categories. Delete or isolate labels in this audit apply only to vendor-specific ownership or duplicate legacy implementations. Preserve scaffold boundaries under `src/ai`, `src/brokerage`, and `src/connectors` so later phases can transport useful functionality into the correct production domains without implementing live behavior yet.
