# Compatibility Alias Migration

## Executive Summary
10K8ZF1 adds canonical research/backtest aliases for the existing paper-named 0DTE fixture helpers and readiness helpers. The legacy paper names remain temporarily so the suite stays stable while the product contract converges on one canonical workflow.

## Product Decision
The product keeps one canonical workflow:

Data
-> Validation
-> Strategy Research
-> Backtest
-> Results / Metrics
-> Later: Live Model Testing

Paper names remain temporarily as compatibility aliases only.

## Canonical Alias Strategy
The canonical research/backtest aliases are direct references to the existing implementations. This preserves behavior and keeps old paper names working until the later symbol migration phase.

## Legacy Compatibility Boundary
Paper names remain temporarily as compatibility aliases. They do not define a separate paper workflow and they do not change execution behavior.

## Aliases Added In zero_dte_fixture_template.py
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS`
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS`
- `build_zero_dte_research_backtest_fixture_template_row`
- `validate_zero_dte_research_backtest_fixture_rows`
- `build_zero_dte_research_backtest_validation_result`
- `build_zero_dte_research_backtest_evaluation_result`
- `build_zero_dte_research_backtest_pipeline_result`

## Aliases Added In streamlit_dashboard_data.py
- `build_research_backtest_fixture_readiness_payload`
- `build_research_backtest_fixture_readiness_rows`
- `build_research_backtest_evaluation_readiness_payload`
- `build_research_backtest_evaluation_readiness_rows`

## Aliases Not Added Because Source Helper Was Absent
The report records that no separate legacy source helper existed for a dedicated pipeline display payload/rows helper, so no new behavior was invented for that name.

## Behavior Preservation
All aliases reference the existing implementation and do not change output or execution behavior.

## Public UI Boundary
Public UI remains on the canonical research/backtest wording:
Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.

## Backtest Path Requirement
The backtest path must be the actual future implementation path.

## Live Model Testing Boundary
Later: Live Model Testing remains future work.

## Broker Boundary
No broker execution.

## Connector Boundary
No live connectors.

## API Boundary
No API calls.

## Database Write Boundary
No database writes.

## Next Phase Recommendation
Proceed to 10K8ZF2 Production Symbol Migration away from paper_* names.

## Required Terms
- 10K8ZF1
- Compatibility Alias Migration
- canonical research/backtest aliases
- paper names remain temporarily as compatibility aliases
- no separate paper workflow
- one canonical workflow
- backtest path must be the actual future implementation path
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS`
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS`
- `build_zero_dte_research_backtest_fixture_template_row`
- `build_zero_dte_research_backtest_pipeline_result`
- `build_research_backtest_fixture_readiness_payload`
- `build_research_backtest_fixture_readiness_rows`
- `build_research_backtest_evaluation_readiness_payload`
- `build_research_backtest_evaluation_readiness_rows`
- `Research/backtest mode only. No broker orders, live connectors, API calls, or database writes.`
- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF1
