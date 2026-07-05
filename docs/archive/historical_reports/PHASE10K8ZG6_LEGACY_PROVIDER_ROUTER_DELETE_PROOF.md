# PHASE10K8ZG6 LEGACY PROVIDER ROUTER DELETE PROOF

## Executive Summary
10K8ZG6 removes the remaining direct dependency reasons for keeping the legacy provider router compatibility hooks. The canonical router remains `src.providers.provider_router`, and no runtime path now requires `betting_providers.provider_router` or `providers.odds_provider_router`.

Both legacy files remain on disk as compatibility hooks only. No deletion occurs in this phase.

## Current HEAD
`3681e5374a6e7ffee56d37a4413bd96349450136`

## Purpose
Prove that the legacy provider router hooks are no longer required by runtime consumers or by patch-targeted tests.

## Scope
- Canonical provider router ownership
- Runtime import redirection proof
- Test patch-target redirection proof
- Delete-readiness evidence only

## Non-Goals
- No deletion
- No live API calls
- No credential reads
- No scraping
- No broker execution
- No AI/LLM calls
- No dashboard rewrite
- No main.py logic rewrite

## Relationship to 10K8ZG5
10K8ZG5 made `src.providers.provider_router` independent. 10K8ZG6 removes the remaining direct reasons to keep the legacy router hooks as required dependencies.

## Remaining Imports Before Changes
- Runtime code no longer imported the legacy router hooks.
- The remaining references were historical phase-test assertions and compatibility documentation.

## Imports Redirected
- `main.py` continues to use `src.providers.provider_router.ProviderRouter`
- `src/api/model_card_service.py` continues to use `src.providers.provider_router.ProviderRouter`
- phase tests now avoid direct imports of `betting_providers.provider_router` and `providers.odds_provider_router`

## Patch Targets Redirected
- No current tests patch `providers.odds_provider_router`
- screenshot enrichment continues through the canonical enrichment service path

## Compatibility Hooks Still Needed
- None for runtime ownership
- The legacy files remain only as on-disk compatibility hooks until the next approved deletion batch

## Delete-Ready Status
- `betting_providers.provider_router`: delete-ready after import proof
- `providers.odds_provider_router`: delete-ready after import proof

## Why Deletion Did or Did Not Occur
No deletion occurred because this phase is proof-first. The compatibility hooks are preserved on disk while the repository records the delete-ready evidence.

## Next Recommended Phase
Delete the legacy provider router compatibility hooks after the final approved deletion batch is opened.

## Required Statement
Legacy provider router deletion is allowed only after import proof, compatibility proof, and full test proof. This phase prioritizes proof over deletion.

No deletion occurs in this phase.
