# FULL_VENDOR_REFERENCE_INVENTORY_AFTER_10K8ZFQ

## Executive Summary
The repository contains vendor references across runtime modules, compatibility wrappers, tests, docs, config files, and string literals. The tracked-file search surfaced high concentrations for Kalshi, Sharp, sportsbook brands, market-data vendors, AI vendors, and a smaller set of crypto or brokerage references. Canonical future ownership should remain product-category based, not vendor based.

## Search Method
- Scanned tracked files with vendor-name and provider-pattern searches.
- Reviewed direct imports, module names, class names, function names, config/env variables, test references, docs, and string literals.
- Grouped references by product category, criticality, and likely future action.

## Inventory Summary
| Vendor or family | Representative file paths | Reference types | Product category mapping | Runtime/test/doc status | Recommended action |
| --- | --- | --- | --- | --- | --- |
| Kalshi | `betting_providers/kalshi_api.py`, `providers/kalshi_provider.py`, `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/kalshi_market_provider.py`, `automation_scheduler/kalshi_scoring.py`, `automation_scheduler/kalshi_monitor.py`, `automation_scheduler/kalshi_readonly_readiness.py`, `automation_scheduler/kalshi_adapter_contract.py`, `kalshi_client.py`, `src/api/market_metadata_routes.py`, `src/api/provider_status_routes.py` | module name, class, function, import, config/env var, test, doc, string literal, compatibility wrapper | `prediction_markets` | runtime-critical, heavily tested, compatibility-heavy | transport useful functionality into `src/providers/prediction_markets/`; keep temporary shims until wrappers prove safe; delete vendor modules later |
| Sharp | `betting_providers/sharp_api.py`, `providers/sharp_provider.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/sportsbook_odds_provider.py`, `automation_scheduler/sportsbook_adapter_contract.py`, `sharp_client.py`, `src/api/provider_status_routes.py`, `src/api/market_metadata_routes.py` | module name, class, function, import, config/env var, test, doc, string literal, compatibility wrapper | `sportsbooks` | runtime-critical, heavily tested, compatibility-heavy | transport useful functionality into `src/providers/sportsbooks/`; keep temporary shims until wrappers prove safe; delete vendor modules later |
| Sportsbook brands | `betting_providers/the_odds_api.py`, `betting_providers/sportsgameodds.py`, `betting_providers/sharp_api.py`, `src/core/entity_resolver.py`, `main.py`, `tests/test_sportsbook_*` | module name, function, import, test, string literal | `sportsbooks` | runtime, test, doc | classify as sportsbook support; keep functionality in category-owned provider modules; rewrite legacy brand-specific tests later |
| Prediction-market brands | `betting_providers/kalshi_api.py`, `providers/kalshi_provider.py`, `automation_scheduler/kalshi_*`, `automation_scheduler/prediction_market_outcome_candidates.py`, `tests/test_kalshi_*`, `tests/test_outcome_*` | module name, function, import, test, string literal | `prediction_markets` | runtime, test, doc | transport useful prediction-market behavior to `src/providers/prediction_markets/`; retain compatibility only until migration is proven |
| Polymarket | `automation_scheduler/backtest_strategy_profiles.py`, `automation_scheduler/data_availability_tiers.py`, `automation_scheduler/data_source_registry.py`, `streamlit_app.py`, `tests/test_derived_feature_backfill_report.py`, `tests/test_open_sports_history_*` | module name, test, string literal | `prediction_markets` | test/doc/runtime-adjacent | keep as product-category reference; no vendor canonical package |
| Brokerage / stock vendors | `automation_scheduler/data_source_registry.py`, `automation_scheduler/provider_allowlist.py`, `automation_scheduler/provider_registry.py`, `main.py`, `src/core/entity_resolver.py`, `tests/test_security_framework.py`, `tests/test_stock_monitor.py`, `tests/test_institutional_stock_pro_analyst_registry.py` | module name, config/env var, import, test, string literal | `zero_dte_stocks` | runtime/test/doc | transport useful stock/market-data functionality into `src/providers/zero_dte_stocks/`; leave broker execution separate and disabled |
| Market-data vendors | `automation_scheduler/data_source_registry.py`, `main.py`, `requirements.txt`, `tests/test_market_research_store.py`, `tests/test_phase10k4_0dte_options_schema_foundation.py` | module name, config/env var, import, test, string literal | `zero_dte_stocks` | runtime/test/doc | keep only if it supports the stock/0DTE product goal; otherwise classify as non-goal/delete candidate |
| Crypto / exchange vendors | `automation_scheduler/data_source_registry.py`, `automation_scheduler/provider_allowlist.py`, `tests/test_crypto_edge_lab_registry.py`, `tests/test_data_source_registry.py`, `tests/test_security_framework.py` | module name, config/env var, import, test, string literal | non-goal / delete candidate | runtime/test/doc | mark for separate decision; not part of the current product categories |
| AI vendors | `automation_scheduler/ai_provider_security.py`, `automation_scheduler/advanced_red_team_provider_policy.py`, `automation_scheduler/security_readiness_report.py`, `tests/test_advanced_red_team.py`, `tests/test_security_framework.py`, `config.py`, `.env.example` | module name, config/env var, import, test, doc, string literal | non-goal / delete candidate | runtime/test/doc | keep as separate policy evidence only; do not turn into canonical provider ownership |

## High-Signal Vendor References
| Reference | File paths | Type | Category | Action |
| --- | --- | --- | --- | --- |
| `KALSHI_*` env vars | `.env.example`, `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/calibration_collector.py`, `automation_scheduler/provider_registry.py`, `automation_scheduler/provider_secret_policy.py`, `src/api/debug_routes.py`, `tests/test_kalshi_readonly_adapter.py`, `tests/test_provider_registry.py` | config/env var | `prediction_markets` | replace or generalize in future canonical package; keep legacy compatibility until migration |
| `SHARP_*` env vars | `.env.example`, `betting_providers/sharp_api.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/provider_registry.py`, `src/api/debug_routes.py`, `tests/test_sharp_sportsbook_adapter.py`, `tests/test_provider_registry.py` | config/env var | `sportsbooks` | replace or generalize in future canonical package; keep legacy compatibility until migration |
| `OPENAI_*` env vars | `.env.example`, `automation_scheduler/ai_provider_security.py`, `automation_scheduler/advanced_red_team_provider_policy.py`, `src/api/debug_routes.py` | config/env var | non-goal / delete candidate | replace or isolate outside provider taxonomy |
| `ALPACA_*`, `POLYGON_*`, `IEX_*`, `TRADIER_*`, `SCHWAB_*`, `YFINANCE`, `NASDAQ`, `CME` | `automation_scheduler/data_source_registry.py`, `automation_scheduler/provider_allowlist.py`, `tests/test_security_framework.py`, `tests/test_stock_monitor.py`, `tests/test_institutional_stock_pro_analyst_registry.py`, `main.py` | config/env var, import, test, string literal | `zero_dte_stocks` | transport useful stock/market-data functionality into category-owned package; keep broker execution separate |

## Vendor-Named Modules and Compatibility Surfaces
| File path | Reference type | Current status | Future action |
| --- | --- | --- | --- |
| `betting_providers/provider_router.py` | module, class, import, compatibility wrapper | runtime-critical compatibility layer | wrap temporarily, then migrate to canonical provider package |
| `betting_providers/kalshi_api.py` | module, class, import | runtime vendor adapter | transport functionality to `prediction_markets`; delete later |
| `betting_providers/sharp_api.py` | module, class, import | runtime vendor adapter | transport functionality to `sportsbooks`; delete later |
| `betting_providers/the_odds_api.py` | module, class, import | runtime vendor adapter | transport sportsbook functionality to category-owned package; delete later |
| `betting_providers/sportsgameodds.py` | module, class, import | runtime vendor adapter | transport sportsbook functionality to category-owned package; delete later |
| `providers/odds_provider_router.py` | compatibility wrapper | compatibility-only | retire after screenshot intake migrates to canonical service path |
| `providers/kalshi_provider.py` | module, function, import | legacy compatibility shell | transport useful prediction-market enrichment behavior; delete later |
| `providers/sharp_provider.py` | module, function, import | legacy compatibility shell | transport useful sportsbook enrichment behavior; delete later |
| `kalshi_client.py` | module, function | root-level live client | likely delete candidate after transport or if import usage remains absent |
| `sharp_client.py` | module, function | root-level live client | likely delete candidate after transport or if import usage remains absent |

## Product-Category Mapping
- `prediction_markets`: Kalshi, Polymarket references, prediction-market outcome and calibration surfaces.
- `zero_dte_stocks`: Robinhood, Alpaca, Polygon, IEX, Tradier, Schwab, Yahoo/yfinance, Nasdaq, CME references.
- `sportsbooks`: Sharp, The Odds API, SportsGameOdds, DraftKings, FanDuel, BetMGM, Caesars, ESPN BET, Pinnacle, Bet365, Bovada references.
- `non-goal / delete candidate`: crypto, AI, and any vendor reference that does not support the current product goal.
- `unknown`: references that need manual review before transport or deletion.

## Criticality Snapshot
- Runtime-critical: active adapters, router entrypoints, API route hooks, and provider registry/health surfaces.
- Test-only: vendor-specified fixtures, phase tests, and live-client contract tests that use mocks.
- Doc-only: phase reports, repo audits, and historical ownership maps.
- Scaffold-only: `src/providers/*` package placeholders created in the vendor-neutral scaffold phases.
- Compatibility-only: legacy `providers/*`, `betting_providers/*`, and scheduler compatibility surfaces.

## Recommended Actions
- Transport useful prediction-market code to `src/providers/prediction_markets/`.
- Transport useful stock/market-data code to `src/providers/zero_dte_stocks/`.
- Transport useful sportsbook code to `src/providers/sportsbooks/`.
- Replace vendor-specific canonical ownership with product-category ownership.
- Mark crypto, AI, and other non-goal vendor references for separate delete or isolate decisions.

## Boundary Clarification
AI/LLM, brokerage/live-trading, and scraper/live-connector functionality are future production domains, not automatic deletion categories. References in this inventory are evidence of legacy or vendor-specific ownership, not a reason to erase the future production domains. Preserve the scaffold boundaries under `src/ai`, `src/brokerage`, and `src/connectors` so later phases can transport useful functionality without reintroducing vendor ownership.
