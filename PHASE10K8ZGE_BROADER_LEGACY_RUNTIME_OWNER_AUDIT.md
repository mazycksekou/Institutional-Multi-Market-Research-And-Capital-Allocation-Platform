# PHASE 10K8ZGE Broader Legacy Runtime Owner Audit + Cleanup Plan

## Executive Summary
Phase 10K8ZGE is an audit-only phase. No deletion occurred and no migration occurred. The provider foundation cleanup is complete after 10K8ZGD, so this phase maps the remaining legacy runtime owners that still need ownership clarification before any future cleanup.

## Current HEAD
`e9629da9cf05d54ac13db1037604b61ce545dd1d`

## Relationship To 10K8ZGD
- 10K8ZGD removed the final provider foundation compatibility shims.
- This phase does not reopen that cleanup; it only audits what remains outside the canonical provider foundation.

Current local inventory snapshot:
- `automation_scheduler/`: 347 files, still the main decommission target
- `providers/`: 3 files, legacy compatibility/live enrichment surface
- `betting_providers/`: 6 files, legacy vendor client surface
- `src/`: 104 files
- `tests/`: 379 files
- tracked JSON/JSONL/CSV under `data/`: 0

`.r2.env` is ignored by `.gitignore` and is not tracked.

## Big-Picture Architecture
The target architecture remains:
- `src/providers`: product-category normalization and provider contracts
- `src/connectors`: raw external data access boundaries
- `src/services`: application orchestration and workflow
- `src/core`: reusable math, probability, EV, CLV, and risk calculations
- `src/ai`: future reasoning and evaluation boundaries
- `src/brokerage`: future execution boundaries

Legacy baskets still contain useful runtime behavior, but they are no longer the intended long-term home.

## What Has Already Been Migrated Or Deleted
- Provider foundation wrappers were deleted in 10K8ZGD.
- Canonical provider ownership already lives under `src/providers`.
- `src/connectors` exists as an inert raw-data boundary.
- `src/api/model_card_service.py` already imports canonical `ProviderRouter`.

## Classification Tags Used In This Audit
- `MIGRATE_TO_SRC_PROVIDERS`
- `MIGRATE_TO_SRC_CONNECTORS`
- `MIGRATE_TO_SRC_SERVICES`
- `MIGRATE_TO_SRC_CORE`
- `MIGRATE_TO_SRC_AI_LATER`
- `MIGRATE_TO_SRC_BROKERAGE_LATER`
- `KEEP_ENTRYPOINT_OR_DASHBOARD`
- `COMPATIBILITY_SHIM_CANDIDATE`
- `DELETE_CANDIDATE_AFTER_PROOF`
- `UNSAFE_TO_TOUCH`

## Remaining Legacy Owners

| Area | Current files | Classification | Future home | Notes |
|---|---|---|---|---|
| Entrypoint shell | `main.py` | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays as thin orchestration shell | Not an automatic deletion candidate. |
| Dashboard shell | `streamlit_app.py` | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays as thin UI shell | Not an automatic deletion candidate. |
| Quant math | `quant_engine.py`, `market_pricing.py`, `model_probability.py` | `MIGRATE_TO_SRC_CORE` | `src/core` | Reusable EV, Kelly, probability, and pricing math. |
| Risk math | `risk_engine.py` | `MIGRATE_TO_SRC_CORE` | `src/core` | Bankroll, ruin, exposure, and stake sizing math. |
| Decision/logging utilities | `bet_decision_engine.py`, `bet_log.py`, `screenshot_intake.py` | `MIGRATE_TO_SRC_SERVICES` | `src/services` | Application workflow and persistence glue. |
| Live clients | `kalshi_client.py`, `sharp_client.py` | `MIGRATE_TO_SRC_CONNECTORS` / `UNSAFE_TO_TOUCH` | `src/connectors` | Live HTTP clients with env/credential access. |
| Legacy provider enrichers | `providers/kalshi_provider.py`, `providers/sharp_provider.py` | `COMPATIBILITY_SHIM_CANDIDATE` | split across `src.providers` + `src.connectors` | Mixed normalization + live fetch logic. |
| Legacy vendor clients | `betting_providers/kalshi_api.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, `betting_providers/sportsgameodds.py` | `UNSAFE_TO_TOUCH` | `src/connectors` later | Live adapter/client behavior remains. |
| Automation provider adapters | `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/kalshi_market_provider.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/sportsbook_odds_provider.py` | `UNSAFE_TO_TOUCH` | split to `src.providers` + `src.connectors` | Still mixed provider/connector behavior. |
| Legacy provider policy | `automation_scheduler/provider_allowlist.py` | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers.policy.allowlist` | Canonical policy already exists. |
| AI policy / evaluation family | `automation_scheduler/advanced_red_team_provider_policy.py`, `automation_scheduler/ai_provider_security.py`, `automation_scheduler/deepseek_*`, `automation_scheduler/model_recheck_runner.py` | `MIGRATE_TO_SRC_AI_LATER` | `src/ai` | AI/LLM work is future-only and blocked until canonical foundations are stable. |
| Execution / gatekeeper family | `automation_scheduler/institutional_execution_desk.py`, `automation_scheduler/execution_gatekeeper.py`, `automation_scheduler/hard_gate_policy.py` | `MIGRATE_TO_SRC_BROKERAGE_LATER` | `src/brokerage` | Execution and order-routing logic belong in the future brokerage boundary. |
| API bridge | `src/api/provider_status_routes.py` | `MIGRATE_TO_SRC_SERVICES` | thin route shell | Still bridges to runtime state. |
| Service bridge | `src/services/enrichment_service.py` | `MIGRATE_TO_SRC_SERVICES` | thin service shell | Still calls legacy provider enrichers. |

## What Should Not Be Deleted
- `main.py`
- `streamlit_app.py`
- `quant_engine.py`
- `risk_engine.py`
- live clients
- connector scaffolds
- AI scaffolds
- brokerage scaffolds

## What Is Unsafe To Touch
- Files that read credentials or env vars at import time.
- Files that make live HTTP calls.
- Files that submit or simulate execution behavior.
- Files that still serve as runtime bridges for the app and API.

## Remaining Legacy Ownership By Basket
- `automation_scheduler/` still owns large orchestration, dashboard-data, backtest, data-source registry, and live adapter behavior.
- `providers/` still carries legacy compatibility/live enrichment behavior for sharp and prediction-market data.
- `betting_providers/` still carries vendor client behavior and should be treated as compatibility-only until connector migration proves safe.
- Root-level live clients remain runtime-critical and should move to `src/connectors` before any deletion.
- Root-level engines/utilities (`quant_engine.py`, `risk_engine.py`, `market_pricing.py`, `model_probability.py`, `bet_log.py`, `bet_decision_engine.py`, `screenshot_intake.py`) still contain useful functionality and should be classified by ownership, not treated as automatic deletion candidates.

## Recommended Next Actions
1. Split live connector behavior into `src/connectors` and keep provider modules read-only.
2. Move reusable math/risk logic into `src/core` after migration/deletion cleanup.
3. Thin `main.py`, `streamlit_app.py`, and API bridges once runtime dependencies are redirected.
4. Continue compatibility-shim proof and delete only after import and test proof.
5. Defer AI/LLM work until canonical math, risk, data, and evaluation foundations are stable.

## Explicit Planning Notes
- Math/risk foundation integration comes after migration/deletion cleanup.
- AI/LLM integration comes after canonical math/risk/data/evaluation foundations.
- `automation_scheduler` remains a decommission target.
- automation_scheduler remains a decommission target.

## Required Statement
Useful functionality should be transported into the correct src domain before legacy modules are deleted. Entrypoints, dashboards, quant logic, and risk logic are not automatic deletion candidates; they must be classified by ownership and dependency role.

## Safety Notes
No deletion occurred in this phase. No migration occurred in this phase. No live imports were introduced by this audit.
