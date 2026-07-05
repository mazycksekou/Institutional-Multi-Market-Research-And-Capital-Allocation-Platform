# Next Orphan / Dead Code Review Plan

Next phase should review the remaining orphan and dead-code candidates from the repository discovery sweep.

Suggested order:
1. Rebuild the orphan candidate list from the live tree.
2. Separate test-only helpers from dead production modules.
3. Review docs/proofs that still reference removed paths.
4. Delete only files with zero runtime, test, and internal references.
5. Re-run smoke, ops checks, and the full gate after each deletion cluster.

The duplicate/overlap cleanup is complete enough to hand off to orphan/dead-code review.

