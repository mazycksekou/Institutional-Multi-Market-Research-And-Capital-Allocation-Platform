# VENDOR_MODULE_DELETION_CANDIDATES_AFTER_10K8ZFQ

## Executive Summary
This document groups vendor-named modules, tests, docs, configs, and env keys by deletion readiness after safe transport to canonical product-category ownership. No deletion is authorized in this phase. The goal is to separate immediate future delete candidates from code that still requires migration, wrapper preservation, or test rewrites.

## Candidate Groups
| Candidate | Reason | Required blocker removal | Product-category replacement path | Deletion risk | Recommended deletion phase |
| --- | --- | --- | --- | --- | --- |
| `betting_providers/kalshi_api.py` | Vendor-specific live adapter with transportable prediction-market logic | canonical prediction-market package + wrapper/importer repointing | `src/providers/prediction_markets/` | high | later migration cleanup |
| `betting_providers/sharp_api.py` | Vendor-specific live sportsbook adapter with transportable odds logic | canonical sportsbook package + wrapper/importer repointing | `src/providers/sportsbooks/` | high | later migration cleanup |
| `betting_providers/the_odds_api.py` | Sportsbook odds provider implementation | canonical sportsbook package + wrapper/importer repointing | `src/providers/sportsbooks/` | high | later migration cleanup |
| `betting_providers/sportsgameodds.py` | Sportsbook odds provider implementation | canonical sportsbook package + wrapper/importer repointing | `src/providers/sportsbooks/` | medium-high | later migration cleanup |
| `providers/kalshi_provider.py` | Legacy compatibility shell around prediction-market enrichment | canonical consumers repointed to product-category package | `src/providers/prediction_markets/` | medium-high | later compatibility cleanup |
| `providers/sharp_provider.py` | Legacy compatibility shell around sportsbook enrichment | canonical consumers repointed to product-category package | `src/providers/sportsbooks/` | medium-high | later compatibility cleanup |
| `providers/odds_provider_router.py` | Compatibility router wrapper | screenshot intake and related consumers repointed | canonical service or category-owned provider bridge | medium | compatibility cleanup after consumer migration |
| `kalshi_client.py` | Root-level live client wrapper | importer count reduced to zero or canonical package wrapper retained | `src/providers/prediction_markets/` | high | post-migration cleanup |
| `sharp_client.py` | Root-level live sportsbook client wrapper | importer count reduced to zero or canonical package wrapper retained | `src/providers/sportsbooks/` | high | post-migration cleanup |
| `automation_scheduler/kalshi_readonly_adapter.py` | Read-only adapter overlaps with future canonical prediction-market ownership | transport/prune importer graph first | `src/providers/prediction_markets/` | high | after wrapper parity is proven |
| `automation_scheduler/kalshi_market_provider.py` | Prediction-market snapshot helper | canonical package parity and importer migration | `src/providers/prediction_markets/` | medium | after wrapper parity is proven |
| `automation_scheduler/kalshi_monitor.py` | Monitoring / candidate generation logic | raw-provider vs derived-signal split decided | `src/providers/prediction_markets/` or `src/signals/` | medium | later migration cleanup |
| `automation_scheduler/kalshi_scoring.py` | Kalshi scoring helper | scoring ownership split decided | `src/providers/prediction_markets/` or `src/metrics/` | medium | later migration cleanup |
| `automation_scheduler/kalshi_readonly_readiness.py` | Policy/readiness helper | canonical provider policy contract exists | `src/providers/prediction_markets/` | medium | later migration cleanup |
| `automation_scheduler/kalshi_adapter_contract.py` | Prediction-market adapter contract overlaps shared provider contracts | canonical contract module stabilized | `src/providers/contracts.py` | medium | later migration cleanup |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Read-only sportsbook adapter overlaps canonical sportsbook ownership | canonical sportsbook package stabilized | `src/providers/sportsbooks/` | high | after wrapper parity is proven |
| `automation_scheduler/sportsbook_odds_provider.py` | Sportsbook odds normalization overlaps canonical ownership | canonical sportsbook package stabilized | `src/providers/sportsbooks/` | medium | later migration cleanup |
| `automation_scheduler/sportsbook_adapter_contract.py` | Sportsbook adapter contract overlaps shared provider contracts | canonical contract module stabilized | `src/providers/contracts.py` | medium | later migration cleanup |
| `automation_scheduler/provider_contracts.py` | Shared provider contract layer duplicated by canonical `src/providers` scaffold | canonical package fully adopted | `src/providers/contracts.py` | medium | after canonical adoption |
| `automation_scheduler/provider_registry.py` | Shared registry logic duplicated by canonical scaffold | importer graph reduced | `src/providers/registry.py` | medium | after canonical adoption |
| `automation_scheduler/provider_health.py` | Shared health/status logic duplicated by canonical scaffold | importer graph reduced | `src/providers/health.py` | medium | after canonical adoption |
| `automation_scheduler/provider_normalization_contract.py` | Shared normalization contract duplicated by canonical scaffold | canonical normalization contract stabilized | `src/providers/normalization.py` | medium | after canonical adoption |
| `automation_scheduler/provider_payload_validator.py` | Shared payload validation duplicated by canonical scaffold | canonical normalization/contract layer stabilized | `src/providers/contracts.py` or `src/providers/normalization.py` | medium | later migration cleanup |
| `automation_scheduler/provider_secret_policy.py` | Secret redaction / credential policy duplicated by canonical safety surfaces | canonical provider policy module exists | `src/providers/health.py` or future policy module | medium | later migration cleanup |
| `automation_scheduler/provider_allowlist.py` | Vendor allowlist and safety gating | policy ownership split decided | future provider policy module | medium | later migration cleanup |
| `automation_scheduler/provider_write_firewall.py` | Write-block safety guard | policy ownership split decided | future provider safety module | medium | later migration cleanup |
| `automation_scheduler/data_source_registry.py` | Vendor/source registry mixes useful stock/data support with non-goal vendor families | product-category split and non-goal isolation | `src/providers/zero_dte_stocks/` plus policy cleanup | medium-high | after taxonomy split |
| `tests/test_kalshi_*` | Vendor-specific contract and adapter tests | canonical package tests exist and wrappers are proven | category-owned provider tests | medium | rewrite after migration |
| `tests/test_sharp_*` | Vendor-specific contract and adapter tests | canonical package tests exist and wrappers are proven | category-owned provider tests | medium | rewrite after migration |
| `tests/test_sportsbook_*` | Vendor- and brand-specific sportsbook tests | canonical sportsbook tests exist | category-owned provider tests | medium | rewrite after migration |
| `tests/test_screenshot_analysis.py` | Compatibility-only path coverage | canonical route/service path exists | API/service tests | low-medium | later cleanup |
| `.env.example` entries such as `KALSHI_*`, `SHARP_*`, `OPENAI_*`, `ALPACA_*`, `POLYGON_*`, `IEX_*`, `TRADIER_*`, `SCHWAB_*`, `COINBASE_*`, `BINANCE_*`, `KRAKEN_*` | Vendor-specific config/env keys that prevent product-neutral ownership | generalized config names and canonical package ownership | canonical provider config, API config, or policy config | medium | later config cleanup |

## Safe Later Deletion Candidates
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `providers/odds_provider_router.py`
- `kalshi_client.py`
- `sharp_client.py`

## Requires Dependency Migration First
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/kalshi_monitor.py`
- `automation_scheduler/kalshi_scoring.py`
- `automation_scheduler/kalshi_readonly_readiness.py`
- `automation_scheduler/kalshi_adapter_contract.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/sportsbook_adapter_contract.py`
- `automation_scheduler/provider_contracts.py`
- `automation_scheduler/provider_registry.py`
- `automation_scheduler/provider_health.py`
- `automation_scheduler/provider_normalization_contract.py`
- `automation_scheduler/provider_payload_validator.py`
- `automation_scheduler/provider_secret_policy.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`
- `automation_scheduler/data_source_registry.py`

## Requires Test Rewrite First
- `tests/test_kalshi_*`
- `tests/test_sharp_*`
- `tests/test_sportsbook_*`
- `tests/test_screenshot_analysis.py`

## Vendor-Specific Docs to Rewrite
- `README.md` sections that still present vendor names as architecture owners
- `.env.example` entries that still expose vendor-named configuration as the primary interface
- any markdown report or guide that still describes vendor modules as canonical ownership boundaries
- historical audit notes that need to be superseded by the vendor-neutral provider taxonomy

## Requires Ownership Decision First
- `automation_scheduler/kalshi_monitor.py`
- `automation_scheduler/kalshi_scoring.py`
- `automation_scheduler/data_source_registry.py`
- `automation_scheduler/provider_allowlist.py`
- `automation_scheduler/provider_write_firewall.py`

## Compatibility Shell Candidates
- `providers/odds_provider_router.py`
- `betting_providers/provider_router.py`
- `src/services/enrichment_service.py`
- `screenshot_intake.py`

## Do-Not-Touch-Yet Candidates
- `main.py`
- `src/api/provider_status_routes.py`
- `src/api/debug_routes.py`
- `src/api/market_utility_routes.py`
- `src/services/enrichment_service.py`
- `automation_scheduler/__init__.py`
- `automation_scheduler/provider_*` files that still support active runtime behavior

## Recommended Deletion Phase
These candidates should only be deleted after canonical provider transport, wrapper tests, importer scans, and explicit approval:
1. Vendor adapter shells and root-level live clients.
2. Compatibility routers after all callers are repointed.
3. Legacy tests after category-owned tests replace them.
4. Vendor-specific env keys after generalized configuration lands.
