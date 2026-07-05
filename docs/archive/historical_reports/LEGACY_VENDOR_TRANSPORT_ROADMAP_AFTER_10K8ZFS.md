# LEGACY_VENDOR_TRANSPORT_ROADMAP_AFTER_10K8ZFS

## Executive Summary
This roadmap converts the vendor audit and production-boundary scaffold into an ordered migration and deletion plan. The goal is to move useful legacy functionality into the correct production domain, keep compatibility shims until importer proof exists, and isolate vendor-named ownership so it can eventually be retired.

The canonical production boundaries are now:
- `src/providers/` for product-category provider normalization and contracts
- `src/connectors/` for raw external data access
- `src/ai/` for AI/LLM reasoning and evaluation
- `src/brokerage/` for execution boundaries
- `src/core/` for pure math and risk primitives
- `src/services/` for application orchestration

## Current Domain Boundaries
- `src/providers/` owns prediction markets, zero-dte stocks, and sportsbooks at the product-category layer.
- `src/connectors/` owns raw market data, odds data, prediction-market data, web scraping boundaries, and feeds.
- `src/ai/` owns future AI policy, prompt, model, and evaluation scaffolds.
- `src/brokerage/` owns future paper/live execution scaffolds and risk-control gateways.
- `automation_scheduler/` remains a temporary orchestration and compatibility shell.
- `betting_providers/` and `providers/` remain legacy vendor-oriented compatibility layers.

## Migration Principles
1. Move pure contracts and pure helpers before live adapters.
2. Split raw connector fetches from normalized provider meaning.
3. Preserve old import paths until wrapper tests prove the new owner is equivalent.
4. Keep live network behavior out of tests.
5. Do not delete a legacy module until dependency proof and test redirection are complete.
6. Keep AI, brokerage, and connector work isolated in their own production boundaries instead of mixing them into providers or scheduler code.

## Ordered Migration Batches
### Batch 1: Pure provider foundations
Transport pure, local-only provider scaffolds first:
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_adapter_base.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `betting_providers/base.py`
- `providers/base_provider.py`
- `betting_providers/normalization.py`

Future destination:
- `src/providers/contracts.py`
- `src/providers/base.py`
- `src/providers/registry.py`
- `src/providers/health.py`
- `src/providers/normalization.py`
- `src/providers/errors.py`

### Batch 2: Raw connector split
Transport raw live-fetch or source-fetch logic into `src/connectors/` and keep provider normalization separate:
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `kalshi_client.py`
- `sharp_client.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/calibration_collector.py`

Future destination:
- `src/connectors/prediction_market_data/`
- `src/connectors/odds_data/`
- `src/connectors/market_data/`

### Batch 3: Provider-category normalization and compatibility repointing
Move category-specific normalization and legacy enrichment consumers:
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `providers/odds_provider_router.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/kalshi_scoring.py`
- `automation_scheduler/kalshi_monitor.py`
- `automation_scheduler/kalshi_readonly_readiness.py`

Future destination:
- `src/providers/prediction_markets/`
- `src/providers/sportsbooks/`
- `src/services/`

### Batch 4: AI, brokerage, and connector production boundaries
Move future production-domain scaffolds out of scheduler ownership:
- `automation_scheduler/ai_provider_security.py`
- `automation_scheduler/advanced_red_team_provider_policy.py`
- `automation_scheduler/advanced_shape_diagnostics.py`
- `automation_scheduler/advanced_red_team_report.py`
- `automation_scheduler/institutional_execution_desk.py`
- `automation_scheduler/execution_later_gate.py`
- `automation_scheduler/human_approval_gate.py`
- `automation_scheduler/later_auto_execution_policy.py`
- `automation_scheduler/nfl_open_data_adapters.py`
- `automation_scheduler/nfl_coaching_adapters.py`
- `automation_scheduler/ncaaf_collegefootballdata_adapter.py`
- `automation_scheduler/news_events_adapter_contract.py`
- `automation_scheduler/injury_weather_adapter_contract.py`
- `automation_scheduler/stock_price_adapter_contract.py`
- `automation_scheduler/stock_fundamentals_adapter_contract.py`

Future destination:
- `src/ai/policy`, `src/ai/evaluation`
- `src/brokerage/execution`, `src/brokerage/risk_controls`, `src/brokerage/order_gateway`
- `src/connectors/market_data`, `src/connectors/odds_data`, `src/connectors/prediction_market_data`, `src/connectors/feeds`, `src/connectors/web_scraping`

### Batch 5: automation_scheduler shrink and retirement
After the earlier batches are stable:
- shrink `automation_scheduler` to orchestration-only compatibility glue
- keep only the smallest possible shell for transitional workflows
- delete the shell only after importer proof, wrapper tests, and dependency scans are clean

## Batch 1 Recommended Scope
Batch 1 should stay limited to pure, local-only, import-safe pieces:
- provider contracts
- provider registry scaffolds
- provider health scaffolds
- provider normalization helpers
- provider errors
- vendor-neutral adapter bases

This batch is the safest because it does not require live clients, network access, credentials, or order execution.

## Batch 2 Recommended Scope
Batch 2 should move raw fetch mechanics into `src/connectors/` without changing normalization behavior:
- prediction-market raw reads
- sportsbook raw reads
- market-data/raw odds client wrappers
- connector-level helpers that are currently bundled with vendor modules

## Batch 3 Recommended Scope
Batch 3 should separate product-category meaning from compatibility shells:
- prediction-market normalization
- sportsbook normalization
- wrapper routers and enrichment bridge modules
- route/service consumers that still point at legacy shells

## Deferred Unsafe Areas
- `main.py`
- `streamlit_app.py`
- FastAPI route rewrites
- live trading or broker execution
- scraper implementation
- any module that would change behavior instead of just ownership

## Deletion Policy
- Delete only after dependency proof, test redirection, and safe replacement are complete.
- Vendor-named modules should not remain permanent architecture owners.
- Legacy modules may remain as shims while tests and importer scans still point at them.

## Shim Policy
- Keep thin wrappers for old import paths during transition.
- Preserve public function names while the canonical owner is being established.
- Use shims for compatibility, not for new behavior.

## Test Rewrite Policy
- Rewrite vendor-specific tests only after canonical category tests exist.
- Preserve current coverage until the new boundary is proven.
- Add fake-client, no-network tests before removing compatibility paths.

## Rollback Strategy
- If a migration batch changes output shape or import behavior, stop and restore the wrapper rather than deleting the old path.
- Keep the legacy module until the canonical module passes equivalence tests.
- Roll back by repointing importers, not by removing functionality.

## Next Recommended Phase
Proceed to the first safe transport implementation batch for the pure provider foundations and connector scaffolds, with fake-client coverage and no runtime behavior changes.
