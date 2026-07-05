# Next Phase Split Plan

## Goal

Start the next migration phase from this checkpoint commit, not from an uncommitted tree.

## Recommended Split Strategy

1. Separate repository-shape changes from behavior changes.
2. Process one dependency cluster at a time.
3. Keep runtime, tests, and proof-scanner updates in the same slice when they are tightly coupled.
4. Re-run the validation ladder after each slice:
   - targeted tests
   - smoke
   - `ops_check`
   - full gate before finalizing the slice

## Suggested Next Slice Order

1. repository-wide scanner and stale-proof cleanup
2. remaining compatibility-facade tightening
3. clustered legacy-retirement follow-up work by canonical owner
4. final architecture freeze and duplicate-ownership audit

## Working Rule

Do not continue from another large dirty tree if the next phase can be split into smaller validated commits.
