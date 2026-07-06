# Branch Inventory and Merge Readiness

## Current State

- Current integration branch: `main`
- Current merged main commit: `831f3405c45ae7d5d5ca0b91c93d6231703c13a0`
- Modernization source branch: `phase-6-api-slimming` (merged into `main` and deleted locally/remotely)
- Remote branches discovered in the current fetch: `14`
- Older stale-but-unique remote branches audited in this pass: `13`

## Real Flow

1. `main` is now the integration branch for the repository.
2. `phase-6-api-slimming` has been merged into local `main` and should only be deleted after `main` is pushed and validated upstream.
3. The 13 older remote branches are stale snapshots with unique commits, but none were proven safe for wholesale merge in this pass.
4. Current policy is selective extraction only: preserve useful work, reject duplicate legacy runtime surfaces, and do not merge old branch snapshots blindly.

## Branch Status Summary

| Branch | Latest Commit | Date | Unique Commits vs `main` | File Changes | Docs | Tests | Src | Scripts | Risk | Recommended Action |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `origin/main` | `ab6f41c` | `2026-06-18 14:11:30 -0400` | n/a | n/a | n/a | n/a | n/a | n/a | low | KEEP ACTIVE |
| `origin/final-product-verification-gap-fill-formula-audit` | `f12cd90` | `2026-06-06 13:55:25 -0400` | `28` | `1148` | `68` | `362` | `0` | `55` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/free-open-normalized-loaders` | `efd7b65` | `2026-06-06 17:17:32 -0400` | `37` | `1414` | `86` | `433` | `0` | `61` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/live-arbitrage-edge-standard` | `eefde5b` | `2026-06-05 22:52:53 -0400` | `22` | `700` | `23` | `266` | `0` | `19` | `high` | `HOLD FOR MANUAL REVIEW` |
| `origin/ncaaf-final-oxylabs-source-policy-free-open-exhaustion` | `ed204a8` | `2026-06-05 19:24:18 -0400` | `21` | `557` | `17` | `234` | `0` | `19` | `high` | `HOLD FOR MANUAL REVIEW` |
| `origin/oxylabs-retrieval-repair-source-classification-validation` | `49b999a` | `2026-06-06 15:50:22 -0400` | `31` | `1274` | `74` | `394` | `0` | `57` | `high` | `HOLD FOR MANUAL REVIEW` |
| `origin/oxylabs-unresolved-data-field-source-discovery-audit` | `ed3b434` | `2026-06-06 15:08:46 -0400` | `30` | `1235` | `74` | `382` | `0` | `56` | `high` | `HOLD FOR MANUAL REVIEW` |
| `origin/practical-horse-racing-quant-lineage` | `a284b8c` | `2026-06-06 14:43:58 -0400` | `29` | `1201` | `74` | `373` | `0` | `55` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/product-architecture-multi-asset-sweep` | `55f49aa` | `2026-06-06 10:16:11 -0400` | `25` | `834` | `48` | `299` | `0` | `21` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/provider-selection-replay-quality-validation` | `2516ad1` | `2026-06-06 01:18:47 -0400` | `24` | `775` | `28` | `284` | `0` | `20` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/regression-quantitative-modeling-layer` | `da43f38` | `2026-06-06 16:11:50 -0400` | `32` | `1315` | `74` | `407` | `0` | `57` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/repo-cleanliness-commit-discipline-enforcement-fix` | `0fbe016` | `2026-06-06 16:26:43 -0400` | `33` | `1333` | `76` | `412` | `0` | `60` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/source-access-execution-plan-master-ledger` | `4eef0f7` | `2026-06-06 16:46:47 -0400` | `35` | `1380` | `84` | `424` | `0` | `61` | `medium` | `HOLD FOR MANUAL REVIEW` |
| `origin/system-canonical-ownership-audit` | `707702a` | `2026-06-06 12:01:38 -0400` | `26` | `966` | `54` | `332` | `0` | `51` | `medium` | `HOLD FOR MANUAL REVIEW` |

## Recommendation

- Merge `phase-6-api-slimming` into `main` before deleting the source branch.
- Keep the 13 older branches available until a branch-by-branch manual review or selective extraction plan is approved.
- Do not delete any of the older branches in this pass; they still require decision capture and/or selective extraction proof.
- The next clean branch strategy should be: task-focused branches off `main`, short-lived review branches, and deletion only after safe extraction or explicit rejection.

## Detailed Dossier

See [OLD_BRANCH_CONTENT_DOSSIER.md](./OLD_BRANCH_CONTENT_DOSSIER.md) for per-branch analysis.
