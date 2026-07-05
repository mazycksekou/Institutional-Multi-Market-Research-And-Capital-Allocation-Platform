# Production Symbol Migration

## Executive Summary
10K8ZF2 makes the canonical research/backtest names the primary workflow surface where safe while preserving the legacy paper_* aliases for backward compatibility. This keeps the product on one canonical workflow without breaking existing tests or imports.

## Product Decision
The product contract stays on one canonical workflow:

Data
-> Validation
-> Strategy Research
-> Backtest
-> Results / Metrics
-> Later: Live Model Testing

## Production Symbol Migration Strategy
Canonical research/backtest names are now the preferred naming surface for production-facing helper references. Legacy paper names remain temporarily as backward-compatible aliases.

## Canonical Names Made Primary
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS`
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS`
- `build_zero_dte_research_backtest_fixture_template_row`
- `validate_zero_dte_research_backtest_fixture_rows`
- `build_zero_dte_research_backtest_validation_result`
- `build_zero_dte_research_backtest_evaluation_result`
- `build_zero_dte_research_backtest_pipeline_result`
- `build_research_backtest_fixture_readiness_payload`
- `build_research_backtest_fixture_readiness_rows`
- `build_research_backtest_evaluation_readiness_payload`
- `build_research_backtest_evaluation_readiness_rows`

## Legacy Paper Names Preserved
The legacy paper_* names remain available as aliases and are not removed in this phase.

## Files Updated
- `automation_scheduler/zero_dte_fixture_template.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `streamlit_app.py`

## Behavior Preservation
No formula outputs changed. No readiness logic changed. No guardrail flags changed. No execution behavior changed.

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

## Remaining Legacy Alias Cleanup
Legacy paper_* aliases remain for one more compatibility phase before they can be retired safely.

## Next Phase Recommendation
Proceed to 10K8ZF3 Product UI Language Finalization.

## Required Terms
- 10K8ZF2
- Production Symbol Migration
- canonical research_backtest names are the primary workflow surface
- paper names remain temporarily as backward-compatible aliases
- no separate paper workflow
- one canonical workflow
- backtest path must be the actual future implementation path
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_REQUIRED_FIELDS`
- `ZERO_DTE_RESEARCH_BACKTEST_FIXTURE_OPTIONAL_FIELDS`
- `build_zero_dte_research_backtest_fixture_template_row`
- `validate_zero_dte_research_backtest_fixture_rows`
- `build_zero_dte_research_backtest_validation_result`
- `build_zero_dte_research_backtest_evaluation_result`
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
- implementation reviewed in 10K8ZF2
