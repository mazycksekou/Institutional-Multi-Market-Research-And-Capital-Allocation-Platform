# AUTOMATION_SCHEDULER_EXIT_SEQUENCE_AFTER_10K8ZFS

## Executive Summary
`automation_scheduler` should eventually become orchestration-only. To get there safely, the repository must first move provider ownership, then connector logic, then AI and brokerage boundaries, and only then shrink the scheduler into a minimal compatibility shell.

## What Must Leave automation_scheduler First
1. Pure provider contracts, registry, health, normalization, and adapter base logic.
2. Provider-category normalization and compatibility wrappers.
3. Any module that is only preserving an old provider import path.

## What Must Leave automation_scheduler Later
1. Raw connector fetches and source adapters.
2. Connector-level helpers for odds, prediction markets, market data, and feeds.
3. AI/brokerage scaffolds that are currently parked in scheduler-owned modules.

## What AI / Brokerage / Scraper References Must Be Isolated Outside automation_scheduler
- AI: `ai_provider_security.py`, `advanced_red_team_provider_policy.py`, `advanced_shape_diagnostics.py`, `advanced_red_team_report.py`, `security_readiness_report.py`
- Brokerage: `institutional_execution_desk.py`, `execution_later_gate.py`, `human_approval_gate.py`, `later_auto_execution_policy.py`, and related risk-control helpers
- Scraper / connector references: raw source adapters, odds clients, market-data adapters, feed adapters, and prediction-market fetchers that should live under `src/connectors`

## What Can Become a Compatibility Shim
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `betting_providers/*`
- `providers/*`

## What Must Be Proven Before automation_scheduler Can Shrink
- The canonical package imports safely.
- Wrapper tests prove old paths still behave the same.
- No live API calls are required by the new owner.
- No credentials are read at import time.
- The consumer graph has been repointed away from scheduler-owned provider logic.
- The provider-facing API routes and services no longer depend on scheduler-owned implementations.

## Proposed Exit Sequence
1. Move pure contracts, health, registry, and normalization.
2. Redirect tests.
3. Move provider-category logic.
4. Move connector/live-fetch logic into `src/connectors` as inert boundaries first.
5. Move broker/live-trading boundaries into `src/brokerage` as inert boundaries first.
6. Move AI/LLM boundaries into `src/ai` as inert boundaries first.
7. Shrink `automation_scheduler` into a compatibility shell.
8. Delete the compatibility shell after dependency proof.

## Safe Shrink Target
The end state should be a tiny orchestration or compatibility shell at most, and then eventual removal once direct dependencies are gone.

## Next Action
Use the transport roadmap to implement the first pure-provider batch, then repoint consumers in small, test-protected steps before touching any live connector, AI, or brokerage functionality.
