# PROVIDER_DUPLICATION_AND_OVERLAP_REPORT_AFTER_10K8ZFN

## Executive Summary
The provider surface contains duplicate-risk logic across routing, normalization, live adapters, and odds/math helpers. The largest overlap is between legacy provider shells, scheduler-owned provider plumbing, and math helpers that already have canonical equivalents in `src/core/`. None of this is safe to delete in this phase.

## Overlap Group 1: Odds, No-Vig, EV, and CLV Math
- Files:
  - `src/core/math_utils.py`
  - `src/core/clv.py`
  - `automation_scheduler/odds_math.py`
  - `automation_scheduler/no_vig_pricing.py`
  - `betting_providers/normalization.py`
  - `market_pricing.py`
  - `quant_engine.py`
  - `automation_scheduler/sharp_sportsbook_adapter.py`
- Similar responsibility:
  - american/decimal conversion
  - implied probability conversion
  - no-vig normalization
  - EV / CLV helpers
  - payout / Kelly / edge math
- Evidence:
  - `automation_scheduler/odds_math.py` delegates many helpers to `src.core.math_utils`.
  - `automation_scheduler/no_vig_pricing.py` delegates no-vig helpers to `src.core.math_utils`.
  - `market_pricing.py` imports `src.core.clv` and `src.core.math_utils`.
  - `quant_engine.py` imports `src.core.math_utils` while also keeping risk-facing wrappers.
  - `automation_scheduler/sharp_sportsbook_adapter.py` reuses canonical math helpers but still owns adapter logic.
- Risk level: high
- Recommended future canonical destination:
  - `src/core/` for pure math
  - provider package only for adapter-specific use of canonical math
- Safe now or later:
  - Safe to document now.
  - Not safe to delete or collapse in this phase.

## Overlap Group 2: Provider Router and Enrichment
- Files:
  - `betting_providers/provider_router.py`
  - `providers/odds_provider_router.py`
  - `src/services/enrichment_service.py`
  - `main.py`
  - `screenshot_intake.py`
  - `src/api/model_card_service.py`
- Similar responsibility:
  - select provider implementation
  - normalize provider responses
  - enrich screenshot/ticket payloads
  - route live odds requests
- Evidence:
  - `providers/odds_provider_router.py` is explicitly a legacy compatibility wrapper around `src/services/enrichment_service.py`.
  - `src/services/enrichment_service.py` still calls `providers.kalshi_provider` and `providers.sharp_provider`.
  - `main.py` and `src/api/model_card_service.py` still depend on `betting_providers.ProviderRouter`.
  - `screenshot_intake.py` still imports the legacy odds provider router.
- Risk level: high
- Recommended future canonical destination:
  - `src/providers/` for provider selection and normalization
  - `src/services/` for enrichment orchestration only
- Safe now or later:
  - Safe to keep as compatibility now.
  - Migration should wait for `src/providers/` creation and wrapper tests.

## Overlap Group 3: Kalshi Provider Surfaces
- Files:
  - `betting_providers/kalshi_api.py`
  - `providers/kalshi_provider.py`
  - `automation_scheduler/kalshi_readonly_adapter.py`
  - `automation_scheduler/kalshi_market_provider.py`
  - `automation_scheduler/kalshi_scoring.py`
  - `automation_scheduler/kalshi_monitor.py`
  - `kalshi_client.py`
- Similar responsibility:
  - read-only Kalshi fetches
  - market normalization
  - snapshot creation
  - health/status and scoring
- Evidence:
  - `betting_providers/kalshi_api.py` performs live network calls with requests.
  - `providers/kalshi_provider.py` normalizes and enriches the same market payload family.
  - `automation_scheduler/kalshi_readonly_adapter.py` and `kalshi_market_provider.py` provide read-only/snapshot functionality for the same source.
  - `kalshi_client.py` is another root-level Kalshi client with no clear current runtime importer in the AST scan.
- Risk level: high
- Recommended future canonical destination:
  - `src/providers/prediction_markets/`
- Safe now or later:
  - Safe to map and wrap now.
  - Not safe to delete or merge until fake-client coverage exists.

## Overlap Group 4: Sharp / Sportsbook Provider Surfaces
- Files:
  - `betting_providers/sharp_api.py`
  - `providers/sharp_provider.py`
  - `automation_scheduler/sharp_sportsbook_adapter.py`
  - `automation_scheduler/sportsbook_odds_provider.py`
  - `sharp_client.py`
  - `betting_providers/the_odds_api.py`
  - `betting_providers/sportsgameodds.py`
- Similar responsibility:
  - sportsbook odds lookup
  - odds normalization
  - snapshot creation
  - provider health and live-read gating
- Evidence:
  - `betting_providers/sharp_api.py` and `providers/sharp_provider.py` both call Sharp-like HTTP endpoints.
  - `automation_scheduler/sharp_sportsbook_adapter.py` now owns the read-only contract and canonical math reuse.
  - `automation_scheduler/sportsbook_odds_provider.py` writes and validates sportsbook snapshot files.
  - `sharp_client.py` is a separate root-level live client with no direct importer found in the scan.
- Risk level: high
- Recommended future canonical destination:
  - `src/providers/sportsbooks/`
- Safe now or later:
  - Safe to document now.
  - Later migration only after wrapper and fake-client tests pass.

## Overlap Group 5: Provider Contracts, Registry, Health, and Policy
- Files:
  - `automation_scheduler/provider_contracts.py`
  - `automation_scheduler/provider_registry.py`
  - `automation_scheduler/provider_health.py`
  - `automation_scheduler/provider_adapter_base.py`
  - `automation_scheduler/provider_normalization_contract.py`
  - `automation_scheduler/provider_payload_validator.py`
  - `automation_scheduler/provider_secret_policy.py`
  - `automation_scheduler/provider_allowlist.py`
  - `automation_scheduler/provider_write_firewall.py`
  - `automation_scheduler/provider_contracts.py`
- Similar responsibility:
  - contract schema definition
  - registry assembly
  - health summarization
  - payload validation
  - secret redaction and safety policy
  - write firewall and allowlist checks
- Evidence:
  - `provider_contracts.py` and `provider_registry.py` both define provider capability/state surfaces.
  - `provider_health.py` summarizes contract readiness.
  - `provider_adapter_base.py` and `provider_normalization_contract.py` overlap on validation and normalized payload shape.
  - `provider_secret_policy.py`, `provider_allowlist.py`, and `provider_write_firewall.py` are all part of the safety boundary.
- Risk level: medium-high
- Recommended future canonical destination:
  - `src/providers/` for contract/registry/health/policy
- Safe now or later:
  - Safe to retain now.
  - Migration should wait for the future package boundary.

## Overlap Group 6: Data-Source Adapter Family
- Files:
  - `automation_scheduler/ncaaf_collegefootballdata_adapter.py`
  - `automation_scheduler/nfl_coaching_adapters.py`
  - `automation_scheduler/nfl_open_data_adapters.py`
- Similar responsibility:
  - provider-adjacent data-source adapters
  - normalization and source-specific payload shaping
- Evidence:
  - All three are adapter-style modules under `automation_scheduler`.
  - They are consumed by tests and some orchestration paths.
- Risk level: medium
- Recommended future canonical destination:
  - likely `src/providers/data_sources/` or a sibling data-source boundary, but not decided here
- Safe now or later:
  - Later, after provider core migration and ownership split.

## Overlap Group 7: Legacy Compatibility Shells
- Files:
  - `betting_providers/__init__.py`
  - `providers/__init__.py`
  - `automation_scheduler/__init__.py`
  - `providers/base_provider.py`
- Similar responsibility:
  - keep old import paths alive
  - provide compatibility wrappers
  - mask the absence of a canonical provider package
- Evidence:
  - `providers/odds_provider_router.py` explicitly says it is a legacy compatibility wrapper.
  - `automation_scheduler/__init__.py` exports provider, risk, backtest, and dashboard surfaces, making it a broad facade.
- Risk level: medium
- Recommended future canonical destination:
  - compatibility-only wrapper layers around `src/providers/`
- Safe now or later:
  - Safe to keep now.
  - Later replacement only after direct importers are repointed.

## Summary of Safe Future Destinations
- `src/core/` for pure math and no-vig helpers.
- `src/providers/` for provider contracts, registry, health, adapters, and normalization.
- `src/services/` for enrichment orchestration only.
- `src/api/` for route ownership.
- `automation_scheduler/` should shrink after provider and math dependencies are split.

## Action Guidance
- Do not delete any of the overlapping modules in this phase.
- Prefer wrappers and canonical imports over refactors.
- Treat all live provider adapters as unsafe for test-time network access.
