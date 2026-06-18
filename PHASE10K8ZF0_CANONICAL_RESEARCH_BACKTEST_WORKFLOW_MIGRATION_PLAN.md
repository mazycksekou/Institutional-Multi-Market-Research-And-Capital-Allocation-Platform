# Canonical Research/Backtest Workflow Migration Plan

## Executive Summary
10K8ZF0 defines the migration path from legacy paper/test/review wording to one canonical workflow for the product: Data, Validation, Strategy Research, Backtest, Results / Metrics, and Later: Live Model Testing. The goal is to keep compatibility aliases only as transition scaffolding while the public UI and future backtest path converge on a single research/backtest architecture.

## Product Decision
The product contract now treats research/backtest as the canonical implementation path. A separate paper workflow is rejected because it creates a second architecture, a second naming scheme, and a second mental model for the same future implementation.

## Canonical Workflow
The canonical workflow is:

Data
-> Validation
-> Strategy Research
-> Backtest
-> Results / Metrics
-> Later: Live Model Testing

This is the one canonical workflow for product language and future implementation planning.

## Why Separate Paper Paths Are Rejected
Separate paper paths imply a different product architecture. Paper is an execution-mode flag, not a product architecture. That means paper may remain as an internal safety flag during transition, but the backtest path must be the actual future implementation path.

## Current Paper/Review/Test Naming Inventory
Current source and tests still contain legacy names in compatibility blocks, hidden source-text blocks, or frozen assertions. The inventory includes paper-only, paper fixture, paper validation, paper evaluation, paper pipeline, paper_result, paper_edge, paper_ev, paper_stake_units, paper_arbitrage_percentage, fake demo, synthetic demo wording, Testing Room, readiness only, and review-only.

## Public UI Naming Boundary
Public UI should not lead with paper, fake, synthetic demo, or testing room language. The visible workflow should use Data, Validation, Strategy Research, Backtest, Results / Metrics, Research Mode, and Local Data.

## Internal Safety Flag Boundary
Internal safety flags may remain temporarily. Hidden compatibility/source-text blocks are transitional only and exist only to preserve frozen tests while the UI contract migrates.

## Compatibility Alias Boundary
Compatibility aliases may remain temporarily. They should map legacy paper names to canonical research/backtest names until the suite proves stable enough to remove them.

## Canonical Name Mapping
Old / legacy concept -> Canonical target

- paper_only -> local_research_backtest_mode
- paper fixture -> research_backtest_fixture
- paper validation -> research_backtest_validation
- paper evaluation -> research_backtest_evaluation
- paper pipeline -> research_backtest_pipeline
- paper_result -> research_backtest_result
- paper_edge -> research_backtest_edge
- paper_ev -> research_backtest_ev
- paper_stake_units -> research_backtest_stake_units
- paper_arbitrage_percentage -> research_backtest_arbitrage_percentage
- fake demo -> remove from product UI
- synthetic rows are fake demo -> remove from product UI
- Testing Room -> Research Mode / Backtest
- readiness only -> Validation / Research Mode where public-facing
- review-only -> Research Mode where public-facing
- hidden legacy source-text blocks -> compatibility aliases only

## Migration Order Before Backtesting
1. Product contract reset.
2. Canonical naming migration plan.
3. Add compatibility aliases for old paper names.
4. Migrate public UI copy.
5. Migrate production helper names to research_backtest names.
6. Keep old paper names as aliases for one phase.
7. Update tests to canonical names.
8. Remove old aliases only after full suite proves stable.
9. Add controlled local data loader.
10. Add canonical backtest runner UI.
11. Add footprint + opening range metric implementation.
12. Begin 10K9 cleanup only after migration is complete.

## Migration Order Before Cleanup
10K9 cleanup must wait until the canonical workflow, compatibility aliases, and public UI copy have all converged on the research/backtest contract.

## Files Requiring Future Symbol Migration
Likely future symbol migration targets include `streamlit_app.py`, `automation_scheduler/zero_dte_fixture_template.py`, and any future helpers that still use paper-prefixed result names in public-facing paths.

## Files Requiring Future UI Copy Migration
Likely UI copy migration targets include `streamlit_app.py` and legacy test files that still mention paper or testing-room wording in product-facing assertions.

## Files That Should Not Be Renamed Yet
Do not rename production helpers yet unless a tiny alias is required for tests. Compatibility aliases should carry the transition until the suite is stable.

## Backtest Path Requirement
The backtest path must be the actual future implementation path. That path should be the same one used for controlled research, validation, and later live model testing.

## Live Model Testing Boundary
Later: Live Model Testing remains future work and does not belong in this phase.

## Broker Boundary
No broker execution.

## Connector Boundary
No live connectors.

## API Boundary
No API calls.

## Database Write Boundary
No database writes.

## Test Plan
The migration test should verify the canonical workflow strings, the compatibility alias boundary, the canonical name mapping table, and the fact that streamlit_app.py does not present obsolete public-facing profit or live-execution claims.

## Next Phase Recommendation
Proceed to compatibility alias migration only after this canonical research/backtest plan is accepted and the current frozen assertions remain stable.

## Required Terms
- Canonical Research/Backtest Workflow Migration Plan
- 10K8ZF0
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
- compatibility aliases may remain temporarily
- public UI should not lead with paper, fake, synthetic demo, or testing room language
- internal safety flags may remain temporarily
- hidden compatibility/source-text blocks are transitional only
- local_research_backtest_mode
- research_backtest_validation
- research_backtest_evaluation
- research_backtest_pipeline
- research_backtest_fixture
- legacy paper names must migrate before controlled backtest runner UI
- migration must happen before footprint metric implementation
- migration must happen before 10K9 cleanup
- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no guaranteed profit language
- no assured profit language
- implementation reviewed in 10K8ZF0
