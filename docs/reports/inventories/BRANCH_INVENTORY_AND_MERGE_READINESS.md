# Branch Inventory And Merge Readiness

## Purpose

This report audits the current local and remote branch set before any branch deletion work.
It records which branches are active, which ones are modernization-related, and which ones are stale but still unique and therefore not safe to delete yet.

## Current Real Flow

- `main` is the stable upstream target and the default remote branch.
- `phase-6-api-slimming` is the active modernization branch and the near-term merge candidate back into `main`.
- The remaining remote branches are older feature, audit, or cleanup branches with unique commits that should be reviewed before any deletion.

## Branch Classification Summary

| branch | latest commit | last commit date | merged into main? | merged into phase-6-api-slimming? | unique commits vs main | unique commits vs phase-6-api-slimming | likely purpose | risk level | classification | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `origin/main` | `199c1ae` | 2026-06-09 21:28:44 -0400 | yes | yes | 0 | 0 | canonical mainline | low | KEEP ACTIVE | Keep as the stable upstream target. |
| `origin/phase-6-api-slimming` | `8e00fe3` | 2026-07-05 19:09:49 -0400 | no | yes | 381 | 0 | repository modernization closeout | low | MERGE CANDIDATE | Keep active until PR checks pass, then merge into `main`. |
| `origin/final-product-verification-gap-fill-formula-audit` | `f12cd90` | 2026-06-06 13:55:25 -0400 | no | no | 28 | 28 | final product verification / audit work | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/free-open-normalized-loaders` | `efd7b65` | 2026-06-06 17:17:32 -0400 | no | no | 37 | 37 | free/open loader finalization work | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/live-arbitrage-edge-standard` | `eefde5b` | 2026-06-05 22:52:53 -0400 | no | no | 22 | 22 | live/read-only arbitrage edge standard | high | STALE BUT UNIQUE — REVIEW | Review carefully because the subject suggests live-adjacent behavior. |
| `origin/ncaaf-final-oxylabs-source-policy-free-open-exhaustion` | `ed204a8` | 2026-06-05 19:24:18 -0400 | no | no | 21 | 21 | NCAAF / combat source policy artifacts | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/oxylabs-retrieval-repair-source-classification-validation` | `49b999a` | 2026-06-06 15:50:22 -0400 | no | no | 31 | 31 | Oxylabs retrieval and source-classification repair | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/oxylabs-unresolved-data-field-source-discovery-audit` | `ed3b434` | 2026-06-06 15:08:46 -0400 | no | no | 30 | 30 | unresolved data-field discovery audit | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/practical-horse-racing-quant-lineage` | `a284b8c` | 2026-06-06 14:43:58 -0400 | no | no | 29 | 29 | horse-racing quant lineage work | high | STALE BUT UNIQUE — REVIEW | Review carefully; the branch appears to carry substantial domain work. |
| `origin/product-architecture-multi-asset-sweep` | `55f49aa` | 2026-06-06 10:16:11 -0400 | no | no | 25 | 25 | multi-asset architecture sweep | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/provider-selection-replay-quality-validation` | `2516ad1` | 2026-06-06 01:18:47 -0400 | no | no | 24 | 24 | provider selection / replay quality validation | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/regression-quantitative-modeling-layer` | `da43f38` | 2026-06-06 16:11:50 -0400 | no | no | 32 | 32 | quantitative modeling layer | high | STALE BUT UNIQUE — REVIEW | Review carefully; the branch name suggests substantive model-layer work. |
| `origin/repo-cleanliness-commit-discipline-enforcement-fix` | `0fbe016` | 2026-06-06 16:26:43 -0400 | no | no | 33 | 33 | repository hygiene / commit-discipline enforcement | low | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/source-access-execution-plan-master-ledger` | `4eef0f7` | 2026-06-06 16:46:47 -0400 | no | no | 35 | 35 | source-access execution plan and ledger | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |
| `origin/system-canonical-ownership-audit` | `707702a` | 2026-06-06 12:01:38 -0400 | no | no | 26 | 26 | canonical ownership audit | medium | STALE BUT UNIQUE — REVIEW | Review for merge or archival evidence before deletion. |

## Answers

1. The current real flow is `main` as the stable upstream target, `phase-6-api-slimming` as the active modernization branch, and the older remote branches as side work that still needs review.
2. The modernization branch is `phase-6-api-slimming`.
3. The branch that should merge into `main` next is `phase-6-api-slimming`, after PR checks pass.
4. Every other remote branch listed here contains unique work not yet proven merged into `main` or `phase-6-api-slimming`.
5. No remote branch is safe to delete today based on current evidence. After `phase-6-api-slimming` merges to `main`, that branch becomes a delete candidate. The others need proof of merge or supersession first.
6. All non-main, non-phase branches need manual review before any delete decision.
7. The clean branch strategy after modernization should be short-lived task branches off `main`, merged by PR, then deleted after validation. Long-lived cleanup branches should be avoided unless there is a formal program with explicit review ownership.

## Branch Strategy Recommendation

- Keep `main` as the durable integration target.
- Use `feature/*`, `bugfix/*`, `docs/*`, `refactor/*`, and `architecture/*` branches for task-focused work.
- Keep modernization branches short-lived and explicitly bounded.
- Delete a branch only after proving it has been merged or superseded.
- Run repository preflight before commit and before push on every task branch.

