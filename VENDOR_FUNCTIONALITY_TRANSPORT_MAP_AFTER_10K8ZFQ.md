# VENDOR_FUNCTIONALITY_TRANSPORT_MAP_AFTER_10K8ZFQ

## Executive Summary
The repository still contains vendor-specific functionality that is useful to the product goal. The useful parts should be transported into category-owned canonical packages. Vendor-specific modules should eventually shrink to temporary adapters, compatibility shims, or deletion candidates after safe verification.

## Transport Map
| Current module or function | Useful functionality | Canonical owner category | Proposed future destination | Migration prerequisites | Test prerequisites | Risk level | Temporary shim needed | Delete after migration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/kalshi_api.py` | Fetch and normalize prediction-market events/markets | `prediction_markets` | `src/providers/prediction_markets/` | canonical package exists; adapter contract defined; import-safe registry/health available | fake-client contract tests; no-network import tests; wrapper-path tests | high | yes | yes |
| `betting_providers/sharp_api.py` | Fetch and normalize sportsbook odds/events | `sportsbooks` | `src/providers/sportsbooks/` | canonical package exists; shared contracts exist; sportsbook normalization contract exists | fake-client contract tests; no-network import tests; wrapper-path tests | high | yes | yes |
| `betting_providers/the_odds_api.py` | Odds provider selection and sportsbook event/odds fetches | `sportsbooks` | `src/providers/sportsbooks/` | sportsbook product boundary fixed; adapter contract in canonical package | fake-client contract tests; no-network import tests | high | yes | yes |
| `betting_providers/sportsgameodds.py` | Sportsbook odds lookup and normalization | `sportsbooks` | `src/providers/sportsbooks/` | sportsbook package exists; transport contract decided | fake-client contract tests; no-network import tests | medium-high | yes | yes |
| `betting_providers/provider_router.py` | Provider selection/routing across sportsbook and prediction-market adapters | shared provider contracts + category adapters | `src/providers/registry.py` and category subpackages | canonical provider package exists; registry contract stabilized | router wrapper tests; fake-client path tests | high | yes | yes |
| `betting_providers/normalization.py` | Normalization for sportsbook and prediction-market payloads | `prediction_markets` and `sportsbooks` | `src/providers/normalization.py` plus category submodules | canonical normalization contract exists | pure-function tests with fixtures | medium | yes | yes |
| `providers/kalshi_provider.py` | Prediction-market enrichment and probability normalization | `prediction_markets` | canonical prediction-market package plus `src/services/` consumer rewrite | enrichment service repointed; canonical provider package exists | wrapper tests; no-network tests | high | yes | yes |
| `providers/sharp_provider.py` | Sportsbook enrichment and odds normalization | `sportsbooks` | canonical sportsbook package plus `src/services/` consumer rewrite | enrichment service repointed; canonical provider package exists | wrapper tests; no-network tests | high | yes | yes |
| `providers/odds_provider_router.py` | Legacy enrichment router wrapper | compatibility-only | temporary `src/services/` bridge or direct canonical service call | screenshot intake repointed | wrapper tests | medium | yes | yes |
| `automation_scheduler/kalshi_readonly_adapter.py` | Read-only prediction-market fetch, signing, diagnostics, and health | `prediction_markets` | `src/providers/prediction_markets/` | canonical package exists; safety contract preserved | fake-client import test; signature/health unit tests; no live calls | high | yes | yes |
| `automation_scheduler/kalshi_market_provider.py` | Prediction-market snapshot normalization and validation | `prediction_markets` | `src/providers/prediction_markets/` | canonical normalization contract exists | pure-function tests | medium | yes | yes |
| `automation_scheduler/kalshi_monitor.py` | Prediction-market monitoring and candidate generation | `prediction_markets` | `src/providers/prediction_markets/` or `src/signals/` for derived signals | domain split on raw provider vs derived signal | pure-function tests | medium | yes | yes |
| `automation_scheduler/kalshi_scoring.py` | Kalshi-specific liquidity/quality scoring | `prediction_markets` | `src/providers/prediction_markets/` or `src/metrics/` if separated later | scoring boundary decided | pure-function tests | medium | yes | yes |
| `automation_scheduler/kalshi_readonly_readiness.py` | Read-only readiness and env policy | `prediction_markets` | `src/providers/prediction_markets/` | canonical policy contract exists | pure-function tests; env-safety tests | medium | yes | yes |
| `automation_scheduler/kalshi_adapter_contract.py` | Prediction-market payload contract | `prediction_markets` | `src/providers/contracts.py` + category contract | canonical contract shape fixed | contract tests | medium | yes | yes |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Sportsbook read-only adapter and odds conversions | `sportsbooks` | `src/providers/sportsbooks/` | canonical package exists; pure math boundary fixed | fake-client tests; math parity tests; no live calls | high | yes | yes |
| `automation_scheduler/sportsbook_odds_provider.py` | Sportsbook snapshot normalization and serialization | `sportsbooks` | `src/providers/sportsbooks/` | sportsbook package exists | pure-function tests | medium | yes | yes |
| `automation_scheduler/sportsbook_adapter_contract.py` | Sportsbook payload contract | `sportsbooks` | `src/providers/contracts.py` + category contract | canonical contract shape fixed | contract tests | medium | yes | yes |
| `automation_scheduler/provider_contracts.py` | Provider contract schema and placeholder registry | shared provider layer | `src/providers/contracts.py` and `src/providers/registry.py` | canonical package exists | contract tests; no-network import tests | medium-high | yes | yes |
| `automation_scheduler/provider_registry.py` | Provider registry and capability selection | shared provider layer | `src/providers/registry.py` | canonical package exists; importer count reduced | registry tests; no-network tests | medium-high | yes | yes |
| `automation_scheduler/provider_health.py` | Health/status summarization | shared provider layer | `src/providers/health.py` | canonical package exists | health tests; redaction tests | medium | yes | yes |
| `automation_scheduler/provider_normalization_contract.py` | Shared normalization contract | shared provider layer | `src/providers/normalization.py` | canonical package exists | pure-function tests | medium | yes | yes |
| `automation_scheduler/provider_payload_validator.py` | Payload validation and shape gating | shared provider layer | `src/providers/contracts.py` or `src/providers/normalization.py` | canonical package exists | pure-function tests | medium | yes | yes |
| `automation_scheduler/provider_secret_policy.py` | Secret redaction and credential-status policy | shared provider layer | `src/providers/errors.py` and `src/providers/health.py` or `policy.py` later | canonical package exists | secret-safety tests; import-safety tests | medium | yes | yes |
| `automation_scheduler/provider_allowlist.py` | Provider classification and policy gating | shared provider policy | future provider policy module or non-provider safety boundary | canonical policy decision fixed | safety tests | medium | yes | yes |
| `automation_scheduler/provider_write_firewall.py` | Write-blocking safety guard | shared provider safety | future provider policy/safety module | canonical policy decision fixed | safety tests | medium | yes | yes |
| `kalshi_client.py` | Kalshi live client and snapshot helper | `prediction_markets` | `src/providers/prediction_markets/` or delete if unused after transport | importer count proven safe; fake-client coverage exists | live-client wrapper tests; no-network tests | high | yes | yes |
| `sharp_client.py` | Sharp sportsbook live client | `sportsbooks` | `src/providers/sportsbooks/` or delete if unused after transport | importer count proven safe; fake-client coverage exists | live-client wrapper tests; no-network tests | high | yes | yes |
| `market_pricing.py` | Cross-book pricing, CLV, and sportsbook math helpers | shared math / core | `src/core/` and `src/metrics/` where appropriate | pure math owner decision fixed | parity tests against canonical math | medium | maybe | yes |
| `quant_engine.py` | Quant helper math and risk-facing evaluation helpers | shared math / risk / core | `src/core/` and `src/risk/` where appropriate | pure math owner decision fixed | parity tests; no behavior changes | medium | maybe | yes |

## Migration Prerequisites
- The canonical `src/providers/` package must remain import-safe.
- Shared contracts, registry, health, and normalization must be stable before adapter transport.
- Wrapper tests must prove that old import paths still behave the same.
- No live API calls may occur during transport verification.

## Test Prerequisites
- No-network import tests for the new canonical package.
- Fake-client tests for vendor adapters.
- Pure-function parity tests for normalization and math.
- Compatibility tests proving old modules still resolve during the transition window.

## Risk Notes
- High risk: live adapters, signing code, and router code that still mediate runtime traffic.
- Medium risk: pure normalization and contract helpers.
- Low risk: empty namespace packages and scaffold-only modules.

## Deleteability Notes
- Vendor-named modules can be deleted only after the canonical product-category package owns the useful functionality and all importers are repointed.
- Temporary shims should remain until wrapper tests and usage scans are clean.

## Supplemental Vendor-Dependent Support Surfaces
| Current module or function | Useful functionality | Canonical owner category | Proposed future destination | Migration prerequisites | Test prerequisites | Risk level | Temporary shim needed | Delete after migration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `automation_scheduler/data_source_registry.py` | Vendor/source classification and source routing used for market-data selection | `zero_dte_stocks` or `non-goal / delete candidate` depending source family | split into category-owned data-source registry helpers or remove non-goal vendor families | product-category split decided; non-goal vendor families isolated | pure-data fixture tests; no-network classification tests | medium-high | yes | maybe |
| `automation_scheduler/provider_allowlist.py` | Provider policy gates and family allowlist | shared provider policy | future provider policy module under `src/providers/` or `src/providers/policy.py` later | policy contract fixed | pure policy tests | medium | yes | yes |
| `automation_scheduler/provider_write_firewall.py` | Write-blocking guardrail for provider operations | shared provider safety | future provider policy/safety module under `src/providers/` | safety contract fixed | safety tests; no-network tests | medium | yes | yes |
| `src/api/debug_routes.py` | Environment/status redaction for vendor-backed secrets | API/security surface | remain in API layer; route logic can later call canonical provider/status surfaces | API ownership boundary fixed | route tests; redaction tests | medium | maybe | maybe |
| `src/api/market_utility_routes.py` | Route bridge to vendor client helpers | API route layer | remain in API layer until canonical provider clients exist | canonical provider clients and route contracts fixed | API route tests; no-network client tests | medium-high | yes | maybe |
| `src/api/provider_status_routes.py` | Provider status and health routes | API route layer | remain in API layer and call canonical provider health later | canonical provider health contract fixed | route tests; redaction tests | medium | maybe | maybe |
| `src/services/enrichment_service.py` | Compatibility enrichment service built on legacy provider shells | service layer bridge | future service or adapter consumer of canonical provider categories | canonical provider package exists; consumers repointed | wrapper tests; no-network tests | high | yes | yes |
| `screenshot_intake.py` | Screenshot-intake routing into odds/provider lookups | route/service bridge | future canonical service or API route adapter | consumer refactor completed | wrapper tests; no-network tests | medium | yes | maybe |
