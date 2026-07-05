# Frozen Test Contract Reset

## Executive Summary
10K8ZF0A resets the frozen public-copy contract so the dashboard can use canonical research/backtest language instead of obsolete synthetic and testing-room phrasing. The new product contract supersedes obsolete synthetic/fake-demo public-copy assertions while preserving the safety meaning through professional wording.

## Blocker Resolved
The obsolete sentence that previously blocked the product contract is removed from `streamlit_app.py` and replaced with canonical research/backtest safety wording.

## Contract Decision
The app now presents one canonical workflow:
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing

## Obsolete Public Copy Removed
The following public-facing wording is removed from `streamlit_app.py`:
- Synthetic rows are fake demo data and must not be used as model evidence.

## Replacement Safety Wording
`Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.`

## Frozen Tests Updated
`tests/test_streamlit_dashboard_data.py` now asserts the replacement safety wording and no longer requires the obsolete sentence.

## Product Workflow Boundary
Public UI language now centers on Data, Validation, Strategy Research, Backtest, Results / Metrics, and Research Mode.

## Internal Compatibility Boundary
Internal compatibility aliases may remain temporarily where needed for transition safety.

## Paper Naming Boundary
Paper may remain only as a temporary internal execution-mode flag, not as public product language.

## Backtest Path Requirement
The backtest path must be the actual future implementation path.

## Live Model Testing Boundary
Later live model testing remains a future phase.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Test Plan
Validate the updated test contract and confirm the obsolete public sentence is absent from `streamlit_app.py`.

## Next Phase Recommendation
Proceed to `10K8ZF0 Canonical Research/Backtest Workflow Migration Plan`.

## Required Review Text
- 10K8ZF0A
- Frozen Test Contract Reset
- new product contract supersedes obsolete synthetic/fake-demo public-copy assertions
- Synthetic rows are fake demo data and must not be used as model evidence removed from streamlit_app.py
- Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.
- Data
- Validation
- Strategy Research
- Backtest
- Results / Metrics
- Later: Live Model Testing
- one canonical workflow
- no separate paper workflow
- paper is an execution-mode flag, not a product architecture
- backtest path must be the actual future implementation path
- internal compatibility aliases may remain temporarily
- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF0A
