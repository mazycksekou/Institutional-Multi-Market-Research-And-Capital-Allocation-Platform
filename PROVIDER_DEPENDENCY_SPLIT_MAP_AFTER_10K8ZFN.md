# PROVIDER_DEPENDENCY_SPLIT_MAP_AFTER_10K8ZFN

## Executive Summary
Provider ownership is still split across active adapters, legacy compatibility shells, scheduler plumbing, and a few root-level helpers. `src/providers/` is the selected future canonical provider owner, but it does not currently exist in the repository. This document maps the current split so that later migration phases can retire `automation_scheduler` safely and in the right order.

## Current Ownership State
- `betting_providers/*` is the active provider adapter home.
- `providers/*` is a legacy compatibility and enrichment shell.
- `automation_scheduler/provider_*` and `automation_scheduler/kalshi_*` still own provider contracts, health, registry, policy, and live adapter code.
- `src/api/provider_status_routes.py` still depends on `automation_scheduler` for provider status data.
- `src/services/enrichment_service.py` still depends on `providers/*`.
- `src/providers/` does not exist yet.

## Dependency Split Map
| Module or family | Current owner / location | Known importers | Runtime dependency status | Test dependency status | Compatibility dependency status | Future action | Blocks automation_scheduler retirement? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `betting_providers/*` | Active provider adapter home | `main.py`, `src/api/model_card_service.py`, provider tests | Runtime-critical | Heavily tested | Compatibility layer for old call sites | Migrate later to `src/providers/` and keep wrappers during transition | Yes |
| `providers/*` | Legacy enrichment shell | `src/services/enrichment_service.py`, `screenshot_intake.py`, targeted tests | Runtime-critical for screenshot enrichment | Tested directly | Compatibility-only | Wrap then retire after canonical provider home exists | Yes |
| `automation_scheduler/provider_*` | Scheduler-owned provider plumbing | `main.py` indirectly, `src/api/provider_status_routes.py`, provider tests | Runtime-critical | Heavily tested | Compatibility and policy layer | Split into future `src/providers/` or retire as shims | Yes |
| `automation_scheduler/kalshi_*` | Scheduler-owned Kalshi read-only/live wrappers | `tests/test_kalshi_*`, `tests/test_provider_*`, some scheduler flows | Runtime-critical for Kalshi surfaces | Heavily tested | Compatibility and adapter layer | Move or wrap later, preserving read-only safety | Yes |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Scheduler-owned sportsbook live adapter | `tests/test_sharp_sportsbook_adapter.py`, `tests/test_sportsbook_odds_provider.py` | Runtime-critical if live reads enabled | Heavily tested | Compatibility and adapter layer | Move to future provider package after wrapper tests | Yes |
| `automation_scheduler/sportsbook_odds_provider.py` | Scheduler-owned sportsbook snapshot helper | `tests/test_sportsbook_odds_provider.py`, `tests/test_sharp_sportsbook_adapter.py` | Runtime-critical for snapshot flow | Heavily tested | Compatibility wrapper candidate | Wrap first, then migrate once canonical provider owner exists | Yes |
| `automation_scheduler/sportsbook_adapter_contract.py` | Scheduler-owned sportsbook contract | Provider contract tests | Runtime-critical for normalization contract | Heavily tested | Compatibility contract layer | Candidate for future `src/providers/contracts.py` | Yes |
| `automation_scheduler/provider_contracts.py` | Scheduler-owned provider contract registry | Provider tests, scheduler config | Runtime-critical | Heavily tested | Compatibility contract layer | Candidate for future `src/providers/contracts.py` | Yes |
| `automation_scheduler/provider_registry.py` | Scheduler-owned provider registry | `tests/test_provider_registry.py`, `tests/test_kalshi_market_provider.py`, `tests/test_sportsbook_odds_provider.py` | Runtime-critical | Heavily tested | Compatibility registry layer | Candidate for future `src/providers/registry.py` | Yes |
| `automation_scheduler/provider_health.py` | Scheduler-owned provider health reporting | `tests/test_provider_health.py` | Runtime-critical | Heavily tested | Compatibility health layer | Candidate for future `src/providers/health.py` | Yes |
| `automation_scheduler/provider_normalization_contract.py` | Scheduler-owned normalization contract | Normalization tests, adapter tests | Runtime-critical | Heavily tested | Compatibility contract layer | Candidate for future `src/providers/normalization.py` | Yes |
| `automation_scheduler/provider_payload_validator.py` | Scheduler-owned payload validation | Provider tests | Runtime-critical | Heavily tested | Compatibility validation layer | Candidate for future provider contract package | Yes |
| `automation_scheduler/provider_secret_policy.py` | Scheduler-owned secret policy | Provider security tests | Runtime-critical safety layer | Heavily tested | Compatibility safety layer | Candidate for future `src/providers/policy.py` / `errors.py` | Yes |
| `automation_scheduler/provider_allowlist.py` | Scheduler-owned provider classification | Security tests | Runtime-critical safety layer | Tested | Compatibility safety layer | Candidate for future policy module | Yes |
| `automation_scheduler/provider_write_firewall.py` | Scheduler-owned execution barrier | Security tests | Runtime-critical safety layer | Tested | Compatibility safety layer | Keep until provider/write split is stable | Yes |
| `automation_scheduler/provider_adapter_base.py` | Scheduler-owned adapter base | Adapter tests | Runtime-critical | Heavily tested | Compatibility base class | Candidate for future `src/providers/base.py` | Yes |
| `automation_scheduler/kalshi_readonly_adapter.py` | Scheduler-owned read-only Kalshi adapter | Kalshi adapter tests, calibration collector tests | Runtime-critical if live reads enabled | Heavily tested | Compatibility live-read wrapper | Wrap or move later, never expose live calls in tests | Yes |
| `automation_scheduler/kalshi_market_provider.py` | Scheduler-owned Kalshi snapshot helper | Kalshi provider tests | Runtime-critical | Heavily tested | Compatibility snapshot wrapper | Candidate for future provider package | Yes |
| `automation_scheduler/kalshi_scoring.py` | Scheduler-owned Kalshi scoring helper | Kalshi scoring tests | Runtime-critical for review queues | Tested | Compatibility scoring helper | Later move to provider or metrics boundary depending usage | Yes |
| `automation_scheduler/kalshi_monitor.py` | Scheduler-owned Kalshi monitor | Kalshi monitor tests | Runtime-critical for review queue | Tested | Compatibility monitor helper | Later move to provider or scheduler orchestration | Yes |
| `automation_scheduler/odds_math.py` / `no_vig_pricing.py` | Scheduler-owned math compatibility wrappers | Odds math tests | Runtime-critical but duplicated | Heavily tested | Compatibility and duplication risk | Wrap to `src/core/math_utils.py` later | Yes |
| `market_pricing.py` | Root-level pricing helper | `main.py`, tests, runtime utilities | Runtime-critical | Tested | Compatibility helper | Keep until moved to canonical math/core owner | Yes |
| `quant_engine.py` | Root-level quant helper | `main.py`, `streamlit_app.py`, tests | Runtime-critical | Heavily tested | Compatibility helper | Keep until canonical math/core boundaries are stable | Yes |
| `kalshi_client.py` | Root-level live client | No direct runtime importers found in scan | Potentially live-call capable | Limited direct test coverage | Compatibility / legacy | Retain until import usage is fully proven absent | Maybe |
| `sharp_client.py` | Root-level live client | No direct runtime importers found in scan | Potentially live-call capable | Limited direct test coverage | Compatibility / legacy | Retain until import usage is fully proven absent | Maybe |
| `src/services/enrichment_service.py` | Service layer | `providers/odds_provider_router.py` | Runtime-critical | Tested indirectly | Compatibility bridge | Repoint to future provider owner later | Yes |
| `src/api/provider_status_routes.py` | API route layer | `main.py` | Runtime-critical | Tested indirectly | Compatibility API bridge | Move status logic to `src/providers/` and keep route thin | Yes |
| `src/api/model_card_service.py` | API service layer | `main.py` | Runtime-critical | Tested indirectly | Compatibility API bridge | Keep route thin while provider router migration happens later | Yes |
| `main.py` | App assembly | Runtime entrypoint | Runtime-critical | Tested heavily | Compatibility composition root | Repoint to future provider owner later | Yes |
| `screenshot_intake.py` | Input pipeline | `main.py`, screenshot tests | Runtime-critical | Tested | Compatibility enrichment consumer | Repoint to canonical provider enrichment owner later | Yes |
| `automation_scheduler/ncaaf_collegefootballdata_adapter.py` | Data-source adapter | Data-source tests | Runtime-critical for data ingestion | Tested | Compatibility adapter | Keep until a provider/data-source boundary is decided | Maybe |
| `automation_scheduler/nfl_coaching_adapters.py` | Data-source adapter | Feature-builder tests | Runtime-critical for data ingestion | Tested | Compatibility adapter | Keep until ownership is split from scheduler | Maybe |
| `automation_scheduler/nfl_open_data_adapters.py` | Data-source adapter | Backfill and adapter tests | Runtime-critical for data ingestion | Tested | Compatibility adapter | Keep until ownership is split from scheduler | Maybe |
| `live_market_intelligence/` | Scaffold only | None found | No runtime dependencies yet | No test surface yet | Scaffold only | Leave untouched until it gains files | No |

## Retire-or-Wrap Guidance
- Migrate first: contracts, registry, health, normalization, and adapter base logic.
- Wrap first: live adapters, root-level compatibility shells, and scheduler provider plumbing.
- Retire later: `automation_scheduler` provider surfaces only after direct importers are repointed and wrapper tests pass.
- Leave untouched for now: the root `main.py` composition root and the current `betting_providers/*` adapter package until `src/providers/` exists.

## Suggested Next Step
Create the future provider package in a later approved phase, then migrate contracts and wrappers in small batches with fake-client tests only.
