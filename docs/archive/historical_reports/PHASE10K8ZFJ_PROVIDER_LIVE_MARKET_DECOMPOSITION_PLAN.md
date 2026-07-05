# PHASE10K8ZFJ Provider / live_market_intelligence Decomposition Plan

## Executive Summary
10K8ZFJ is a decomposition plan only. No files deleted, no files moved, no source-function migration, no public functions removed, and behavior unchanged.

The provider canonical owner remains `src/providers/` as the long-term target from the canonical ownership map. In this checkout, `betting_providers/` is the active compatibility/adapter home, `providers/` is a thin legacy enrichment shell, and `live_market_intelligence/` exists as an empty scaffold tree with no files yet.

This phase does not authorize deletion.

## Current HEAD
Current HEAD: `1e0402495012914d8c16a4d65b1755c453e95978` (`1e04024 docs: plan automation scheduler decomposition`).

Repo status at planning time is clean. The fresh inventory shows:
- `providers/`: 5 files
- `betting_providers/`: 9 files
- provider-related files under `automation_scheduler/`: 62 files
- `src/providers/`: absent
- `src/api` provider/status route files: 1
- `live_market_intelligence/`: absent
- tests: 352 Python files
- raw/generated `data/` JSON/JSONL/CSV: 320 / 0 / 0

## Purpose
Create a safe future migration sequence for provider-related code and live-market-intelligence-adjacent code before any implementation migration.

## Scope
This report classifies provider-adjacent files into ownership lanes, identifies the long-term canonical owner, and defines migration waves without changing runtime behavior.

## Non-Goals
- no files deleted
- no files moved
- no source-function migration
- no public functions removed
- no external API calls
- no live connectors
- no credentials committed
- no secrets printed
- no AI integration
- no ML training
- no backtest runner
- no controlled data loader
- no broker execution
- no real trade execution
- no scraper actions

## Relationship to 10K8ZFF
10K8ZFF established the canonical ownership map. This report applies that map to provider and live-market-intelligence responsibilities and keeps the migration direction pointed at `src/providers/`.

## Relationship to 10K8ZFI
10K8ZFI classified `automation_scheduler/` as an orchestration-only future. This provider plan follows that boundary: `automation_scheduler/` may keep wrappers temporarily, but provider business logic should move out later.

## Provider Decomposition Method
The method is evidence-first:
- inventory current provider-related files
- separate adapters, contracts, health, routing, and enrichment
- distinguish raw provider calls from derived signals/intelligence
- keep compatibility wrappers until tests prove stable migration safety
- avoid live requests during planning and unit tests

## Provider Inventory
| Area | Present? | Count | Current shape | Canonical future owner |
| --- | --- | ---: | --- | --- |
| `providers/` | yes | 5 | legacy enrichment shell plus compatibility wrappers | `src/providers/` |
| `betting_providers/` | yes | 9 | active adapter home and compatibility layer | `src/providers/` |
| provider-related `automation_scheduler/` files | yes | 62 | contracts, registry, health, adapters, policies, monitors | `src/providers/`, `src/api/`, `src/signals/`, `src/storage/` |
| `src/providers/` | no | 0 | not created yet | future canonical provider owner |
| `src/api/provider_status_routes.py` | yes | 1 | route boundary | `src/api/` |
| `live_market_intelligence/` | yes | 0 | empty scaffold tree with no files yet | future split when populated |

## Provider Interface / Adapter Base Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `providers/base_provider.py`, `betting_providers/base.py`, `automation_scheduler/provider_adapter_base.py`, `automation_scheduler/provider_contracts.py` | Provider Interface / Adapter Base | Enrichment / Services | `src/providers/` | yes | P1 | medium | none | These files define the adapter surface, base responses, and contract shape. | `src/providers/` does not exist yet; compatibility consumers still import current paths. | Introduce the canonical provider interface later and forward wrappers into it. |

## Provider Registry / Router Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/provider_router.py`, `automation_scheduler/provider_registry.py` | Provider Registry / Router | Orchestration / Scheduler | `src/providers/registry.py` or `src/providers/router.py` | yes | P1 | medium | none | These files decide provider selection, aliases, and routing behavior. | Consumers still depend on old package names; canonical package absent. | Move routing logic to `src/providers/` later and keep compatibility imports. |

## Provider Normalization / Contracts Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/normalization.py`, `automation_scheduler/provider_normalization_contract.py`, `automation_scheduler/provider_payload_validator.py`, `automation_scheduler/sportsbook_adapter_contract.py`, `providers/kalshi_provider.py` | Provider Normalization / Contracts | Provider Interface / Adapter Base | `src/providers/normalization.py` | yes | P1 | high | none | These modules normalize odds, events, payloads, and validation rules across multiple adapter families. | A single canonical contract module is not yet in place under `src/providers/`. | Extract a single normalization contract later and keep compatibility wrappers until parity is proven. |

## Provider Health / Status Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `automation_scheduler/provider_health.py`, `automation_scheduler/kalshi_monitor.py`, `automation_scheduler/kalshi_readonly_readiness.py`, `src/api/provider_status_routes.py` | Provider Health / Status | API Route | `src/providers/health.py` for logic and `src/api/provider_status_routes.py` for routes | yes | P2 | medium | none | Health/status summaries and route wiring are split across scheduler and API layers. | Route consumers still call automation_scheduler health helpers. | Keep routes thin and move provider health logic into the canonical provider package later. |

## Sportsbook Adapters Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/the_odds_api.py`, `betting_providers/sharp_api.py`, `betting_providers/sportsgameodds.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/sportsbook_odds_provider.py`, `providers/sharp_provider.py` | Sportsbook Adapters | Provider Normalization / Contracts | `src/providers/sportsbook/` | yes | P1 | high | high | These adapters can make live HTTP requests and normalize sportsbook data. | Live clients and compatibility wrappers are still in active use. | Later migrate raw sportsbook adapter behavior to `src/providers/sportsbook/` and keep fake-client tests only. |

## Kalshi Adapters Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/kalshi_api.py`, `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/kalshi_market_provider.py`, `automation_scheduler/kalshi_adapter_contract.py`, `automation_scheduler/kalshi_readonly_readiness.py`, `providers/kalshi_provider.py` | Kalshi Adapters | Provider Health / Status | `src/providers/kalshi/` | yes | P1 | high | high | These modules contain Kalshi-specific adapter logic, snapshot shaping, and read-only/live toggles. | There is no canonical `src/providers/` package yet. | Move adapter logic later and keep the current wrappers until parity and route safety are proven. |

## Sharp / Market Intelligence Adapters Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `providers/sharp_provider.py`, `automation_scheduler/cross_asset_intelligence_router.py`, `automation_scheduler/cross_asset_manifold_router.py`, `automation_scheduler/cross_asset_embedding_router.py`, `automation_scheduler/institutional_cross_asset_adapters.py`, `automation_scheduler/institutional_cross_asset_reports.py`, `automation_scheduler/institutional_cross_asset_scores.py`, `automation_scheduler/odds_line_monitor.py` | Sharp / Market Intelligence Adapters | Signals / Features | raw adapters to `src/providers/sharp/`; derived intelligence to `src/signals/` | yes | P2 | medium | possible | These files mix raw adapter access, cross-asset intelligence, and derived scoring/reporting. | `live_market_intelligence/` is absent, so the split has not been localized into a dedicated folder. | Separate raw provider calls from derived signals later; keep orchestration and report generation stable for now. |

## Enrichment / Services Lane
| file | primary lane | secondary lane | likely future owner | keep temporarily | migration priority | risk | external-call risk | reason | blockers | recommended future action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `providers/odds_provider_router.py`, `providers/base_provider.py`, `src/services/enrichment_service.py`, `src/services/action_betting_service.py` | Enrichment / Services | Provider Interface / Adapter Base | `src/services/` plus `src/providers/` for provider calls | yes | P2 | medium | possible | These services bridge provider enrichment, ticket shaping, and action orchestration. | Existing callers still rely on `providers/` and `betting_providers/` names. | Keep service orchestration in place and redirect provider calls through the canonical provider package later. |

## live_market_intelligence Lane
`live_market_intelligence/` exists as an empty scaffold tree with the subdirectories `alerts`, `contracts`, `engines`, `fixtures`, `gates`, `metrics`, `normalization`, `providers`, and `replay`. There are no files yet, so this lane is scaffold-only for now. The adjacent evidence lives in `automation_scheduler/cross_asset_*`, `automation_scheduler/institutional_cross_asset_*`, and `automation_scheduler/odds_line_monitor.py`.

Future split if this lane is introduced:
- raw provider calls -> `src/providers/`
- derived signals/intelligence -> `src/signals/`
- orchestration/reporting -> `automation_scheduler/`

## Deprecated / Manual Review Candidates
| file or group | reason for manual review | external-call risk | keep yet? | recommended future action |
| --- | --- | --- | --- | --- |
| `automation_scheduler/ai_provider_security.py`, `automation_scheduler/advanced_red_team_provider_policy.py` | policy-heavy files that mix provider classification, AI policy, and safety rules | none | yes | keep as policy guards until the provider and AI boundaries are fully separated |
| `automation_scheduler/provider_write_firewall.py`, `automation_scheduler/provider_allowlist.py`, `automation_scheduler/provider_secret_policy.py` | safety policy and provider classification overlap | none | yes | keep as guardrails; do not delete before wrapper and usage scans |
| `automation_scheduler/kalshi_monitor.py`, `automation_scheduler/odds_line_monitor.py` | monitoring and intelligence overlap can hide responsibility creep | none | yes | review after provider and signals ownership are separated |
| `automation_scheduler/cross_asset_*`, `automation_scheduler/institutional_cross_asset_*` | broad intelligence routers, scorers, and reports | possible | yes | classify later into raw provider, derived signals, or orchestration lanes |

## Future Provider Owner Decision
1. Long-term provider home: `src/providers/`.
2. `betting_providers/`: keep as a compatibility wrapper and temporary adapter home until `src/providers/` is real.
3. `providers/`: keep as a thin legacy compatibility shell and enrichment bridge, not the canonical owner.
4. `automation_scheduler/provider_*`: keep as wrappers, policy glue, and temporary orchestration helpers.
5. `live_market_intelligence/`: absent here; if introduced later, split raw provider calls, derived signals, and orchestration before adding any live connector behavior.

## Provider Migration Waves
### Provider Wave 0
Current guardrails only. 10K8ZFF, 10K8ZFI, and this report exist; no source migration yet.

### Provider Wave 1
Provider ownership contract. Define `src/providers/` without live calls and keep tests only.

### Provider Wave 2
Normalization contract extraction. Create one odds/event normalization contract and wrap old modules later.

### Provider Wave 3
Health/status extraction. Separate health logic from API routes and keep `src/api/` route ownership thin.

### Provider Wave 4
Sportsbook adapters. Move or wrap sportsbook adapters into `src/providers/sportsbook/` with fake-client tests only.

### Provider Wave 5
Kalshi adapters. Move or wrap Kalshi adapters into `src/providers/kalshi/` with fake-client tests only.

### Provider Wave 6
Sharp / market intelligence adapters. Split raw adapter calls from derived signals and keep the orchestration surface stable.

### Provider Wave 7
`live_market_intelligence` split, if the folder is introduced later.

### Provider Wave 8
Provider deprecation review after wrappers, tests, and usage scans prove that cleanup is safe.

## Must-Not-Delete-Yet Compliance
The following remain protected by the canonical owner map and the evidence scan:
- provider interfaces
- provider routers and registries
- provider normalization and validation contracts
- provider health/status logic
- sportsbook and Kalshi adapters
- sharp and market-intelligence adjacent routing
- enrichment services
- API provider/status routes
- compatibility wrappers under `providers/` and `betting_providers/`
- automation_scheduler provider helpers and policy guards

This is the `must_not_delete_yet` set.

This phase does not authorize deletion.

## External Call Safety Policy
- no external API calls in tests
- no live connectors in this phase
- no credentials committed
- no secrets printed
- R2 credentials come from environment variables only
- provider migration must stay compatible with fake-client tests before any live request path is approved

## Unsafe Actions
- deleting compatibility wrappers before usage and parity checks
- moving provider code without tests
- introducing live connectors during a planning pass
- treating `live_market_intelligence/` as present when it is absent here
- conflating raw provider adapters with derived signal generation
- mixing provider ownership changes with unrelated scheduler cleanup
- breaking old import paths

## Acceptance Results
- provider canonical owner: selected
- provider migration direction: `providers/` and `betting_providers/` -> `src/providers/`
- live_market_intelligence present: yes
- live_market_intelligence classified: scaffold-only
- no external API calls: yes
- no live connectors: yes
- daily data hygiene scheduler remains operational: yes
- dry-run by default: yes
- agent is advisory only: yes
- agent does not directly delete files: yes
- risk preset controls sizing: yes
- scenario mode controls missing-data handling: yes
- source code was preserved
- tests/fixtures were preserved
- manifests were preserved
- archives were preserved
- tracked files were preserved
- no credentials committed
- no secrets printed

## Next Phase Recommendation
Proceed to 10K8ZFK Test Suite Cleanup Plan
