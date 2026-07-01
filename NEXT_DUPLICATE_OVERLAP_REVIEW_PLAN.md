# Next Duplicate Overlap Review Plan

## Objective

Review remaining overlap now that the active legacy bridge imports are closed.

## Focus Areas

- Duplicate exports between façade modules and canonical owners
- Overlap between `src.services.streamlit_dashboard_facade` and the smaller `src.services.*` runtime modules
- Any remaining compatibility strings that are no longer executable dependencies
- Stale phase tests that only assert old file text instead of behavior

## Recommended Next Checks

1. Run a repository-wide overlap report for `src.providers`, `src.services`, and `src.market_intelligence`.
2. Identify symbols still exposed through multiple owners.
3. Keep only the canonical owner for each behavior surface.
4. Remove any obsolete proof docs once the overlap review is complete.
