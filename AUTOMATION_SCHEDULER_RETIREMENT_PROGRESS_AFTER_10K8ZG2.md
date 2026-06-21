# AUTOMATION_SCHEDULER_RETIREMENT_PROGRESS_AFTER_10K8ZG2

## Executive Summary
`automation_scheduler` is still a decommission target, but it remains heavily involved in runtime orchestration and dashboard data.

The good news:
- provider foundation wrappers are already canonical elsewhere
- provider-related scheduler files are a small slice of the tree

The bad news:
- the package still owns a lot of runtime behavior and import surface

No deletion occurs in this phase. This phase establishes deletion readiness evidence only.

## Current Scope
File counts:
- total `automation_scheduler` files: `709`
- provider-related `automation_scheduler` files by filename scan: `36`

Provider-related share of the scheduler tree:
- about `5%` by filename scan

## What Has Already Left
- provider foundations live under `src/providers`
- inert connector boundaries live under `src/connectors`
- category-owned read-only adapters exist for prediction markets, odds, and zero-DTE/stocks

## What Still Lives In `automation_scheduler`
- scheduler runners and orchestration
- dashboard data helpers
- backtest / report helpers
- provider snapshots / health / registry wrappers
- sharp and kalshi live adapter logic
- many research and diagnostic workflows

## Progress Against Retirement
- canonical wrappers exist: yes
- direct legacy provider ownership reduced: yes
- runtime scheduler ownership removed entirely: no
- dashboard dependency removed: no
- API dependency removed: no

## Retirement Blockers
1. `main.py` still imports `automation_scheduler`
2. `streamlit_app.py` still imports scheduler dashboard helpers
3. `src/api/provider_status_routes.py` still exposes scheduler-owned provider snapshots
4. `src/services/enrichment_service.py` still uses legacy provider owners
5. `screenshot_intake.py` still depends on legacy odds enrichment
6. live scheduler adapters still own provider behavior
7. tests still depend on scheduler-owned workflows

## Exit State
`automation_scheduler` should eventually become either:
- a minimal compatibility/orchestration shell, or
- fully removable after all dependent entrypoints are redirected

## Acceptance Results
- Retirement progress evidence collected: yes
- No deletion occurred: yes
- No migration occurred: yes
- No behavior changed: yes

## Next Phase Recommendation
Rewire the remaining API/service/UI importers before touching the scheduler wrappers.
