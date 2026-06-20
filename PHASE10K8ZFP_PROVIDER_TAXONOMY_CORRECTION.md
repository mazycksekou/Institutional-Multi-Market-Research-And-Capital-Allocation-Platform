# PHASE10K8ZFP Provider Taxonomy Correction

## Executive Summary
This phase corrects the provider skeleton so the canonical future package structure is product-category based rather than vendor based. The canonical provider landing zone remains `src/providers/`, but the categories under it must be vendor-neutral.

## Reason for Correction
The initial skeleton introduced a vendor-specific canonical placeholder package. That is too narrow for the long-term ownership model. The taxonomy must reflect product categories so future provider migration can remain stable even if vendors change.

## Correct Canonical Provider Taxonomy
- `prediction_markets/`
- `zero_dte_stocks/`
- `sportsbooks/`

## Removed Vendor-Specific Skeleton Paths
- `src/providers/kalshi/`

## Added Product-Category Paths
- `src/providers/zero_dte_stocks/`
- `src/providers/prediction_markets/` remains
- `src/providers/sportsbooks/` remains

## Vendor-Neutral Naming Policy
Canonical provider ownership is product-category based, not vendor-name based. Prediction markets, 0DTE/stocks, and sportsbooks are the canonical provider categories. Vendor names such as Kalshi or Sharp must not define future package ownership.

## What Was Not Changed
- No runtime provider implementation was migrated.
- No legacy provider modules were deleted.
- No live API behavior changed.
- No automation_scheduler retirement work was performed.
- No provider contracts were made vendor-specific.

## Runtime Safety Statement
The correction is scaffold-only. It changes package naming and tests, not runtime provider behavior. Existing provider code paths continue to function as before.

## Test Summary
- The provider skeleton test now imports `src.providers.prediction_markets`, `src.providers.zero_dte_stocks`, and `src.providers.sportsbooks`.
- The test asserts that `src.providers.kalshi` does not exist.
- The test asserts that no canonical `src/providers` path contains `kalshi` or `sharp`.
- The provider contract and adapter test slice remains local-only and unchanged in behavior.

## Next Recommended Phase
Begin later migration batches using the vendor-neutral categories as the landing zones for wrapper-first provider moves.
