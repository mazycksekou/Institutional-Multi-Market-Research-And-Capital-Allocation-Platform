# Dashboard Product Lane Cleanup

## Executive Summary
The public-facing dashboard now presents `Sports`, `Stocks / 0DTE`, and `Predictions` as the main product lanes, while legacy labels remain only as internal compatibility aliases where required by frozen 10K8 tests. This keeps the product surface cleaner without breaking the existing review contracts.

## Existing Owner Used
The existing owner rule is preserved in `streamlit_app.py` and the lane cleanup stays inside the current dashboard owner instead of creating a detached UI surface.

## Public Product Lanes
The public selector is driven by `PRODUCT_MARKET_LANES` and maps to `sports`, `stocks_0dte`, and `predictions`.

## Compatibility Aliases
`LEGACY_INTERNAL_MODE_ALIASES` preserves the old internal labels:
`One Sport`, `One Stock Market`, `One Crypto Market`, `One Prediction Market`, and `One 0DTE Options Trade`.

## Internal Mode Mapping
`internal_model_mode_for_product_lane` keeps the product lanes wired to `one_sport`, `one_0dte_options_trade`, and `one_prediction_market`.

## Sports Lane
`Sports` remains the lane for NFL, NBA, MLB, NHL, soccer, tennis, UFC, boxing, and golf.

## Stocks / 0DTE Lane
`Stocks / 0DTE` is the only stock lane and keeps the 0DTE readiness, validation, evaluation, and pipeline previews.

## Predictions Lane
`Predictions` covers controlled Kalshi and Polymarket style market copy without live connectors.

## ORB Strategy Research Placement
`ORB Strategy Research` is positioned under `Stocks / 0DTE` as a controlled research caption only.

## Internal Testing Surface
`Testing / Readiness Lab` and `Internal Research Lab` keep the paper/test/readiness flows in an internal surface instead of the main product framing.

## Paper-Only Boundary
The lane cleanup remains `paper-only` and `local fixture-backed testing`.

## Readiness-Only Boundary
The lane cleanup remains `readiness only` and `review-only`.

## Trade Execution Boundary
No real trade execution was added.

## Broker Boundary
No broker execution was added.

## Connector Boundary
No live connectors were added.

## API Boundary
No API calls were added.

## Database Write Boundary
No database writes were added.

## Guardrails Preserved
`local fixture-backed testing`, `paper-only`, `readiness only`, `no broker execution`, `no real trade execution`, `no live connectors`, `no API calls`, and `no database writes` remain visible in `streamlit_app.py`.

## Test Plan
Validate the new public lane constants, verify the compatibility aliases remain internal, confirm the ORB research caption is under `Stocks / 0DTE`, and confirm no forbidden connector or profit language was introduced.

## Next Phase Recommendation
Proceed to `10K8ZD` ORB Strategy Research Integration Audit follow-up work if a real ORB owner is later identified; otherwise keep ORB in controlled research wording only.

## Implementation Reviewed in 10K8ZC
`streamlit_app.py` was reviewed in 10K8ZC.

implementation reviewed in 10K8ZC
