# Dedicated 0DTE Paper Fixture Template

## Executive Summary
This Dedicated 0DTE Paper Fixture Template review covers `automation_scheduler/zero_dte_fixture_template.py`, `automation_scheduler/model_data_field_catalog.py`, `streamlit_app.py`, and the math boundary in `quant_engine.py`.

The template defines a paper-only, readiness-only local fixture row shape for the dedicated One 0DTE Options Trade lane. This lane is the primary active trading lane, but this phase remains local fixture-backed testing only.
0DTE is the primary active trading lane.

## Existing Owner Used
The existing owner rule was preserved. No duplicate owner created.

## Dedicated 0DTE Paper Fixture Template
The dedicated template is owned by `automation_scheduler/zero_dte_fixture_template.py` and is built around:

- `ZERO_DTE_MODE_KEY`
- `ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS`
- `ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS`
- `ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS`
- `ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS`
- `zero_dte_fixture_field_groups`
- `zero_dte_fixture_fields`
- `build_zero_dte_fixture_template_row`
- `describe_zero_dte_fixture_template`

## Required Input Fields
The required constant is `ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS`.
The required template row fields include:

- underlying_symbol
- underlying_price
- expiration_date
- minutes_to_expiration
- strike
- option_type
- call_put
- bid
- ask
- mid
- implied_volatility
- delta
- gamma
- theta
- vega
- spread_percent
- premium

## Optional Input Fields
The optional constant is `ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS`.
The optional template fields keep the row ready for local fixture-backed testing and include the broader 0DTE context, while remaining paper-only and readiness only.

## Technical Signal Fields
`technical_signal_fields` remain technical inputs only. Arbitrage, EV, edge, Kelly, fair odds, implied probability, bankroll, confidence, and no-bet style fields stay out of `TECHNICAL_SIGNAL_FIELDS`.
technical signals are not universal math outputs.

## Review Output Fields
The review output surface includes the review-only calculations and checks needed for a local template row, including:

- paper_arbitrage_percentage
- paper_arbitrage_window
- paper_arbitrage_timeframe
- paper_arbitrage_best_percentage
- paper_arbitrage_liquidity_adjusted_percentage
- paper_arbitrage_after_spread_percentage
- paper_arbitrage_after_fees_percentage

## Paper Arbitrage Output Fields
The paper arbitrage output fields are review-only outputs, not technical signals.
paper arbitrage outputs are review-only.

## Universal Math Boundary
EV stays in quant_engine.py.
edge stays in quant_engine.py.
Kelly stays in quant_engine.py.
arbitrage stays out of TECHNICAL_SIGNAL_FIELDS.

## Streamlit Visibility
`streamlit_app.py` now shows the dedicated 0DTE paper fixture template, local fixture-backed testing, paper-only, readiness only, no broker execution, no real trade execution, no live connectors, no API calls, no database writes, `paper_arbitrage_percentage`, and `paper arbitrage percentage within tested timeframe`.

## Paper-Only Boundary
The template is paper-only prediction testing and does not add real model execution or real trade execution.

## Readiness-Only Boundary
The template is readiness only and intended for local fixture-backed inspection before any later change.

## Trade Execution Boundary
No real trade execution is added.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Guardrails Preserved
The template preserves:

- paper-only
- readiness only
- local fixture-backed testing
- no live connectors
- no API calls
- no database writes
- no broker execution
- no real trade execution
- no duplicate owner created
- no temporary git shim
- user threshold review-only
- validity check only
- do not label quality automatically
- do not hide valid results because sample size is low

## Test Plan
The 10K8O test verifies the new template module, the Streamlit visibility copy, the required field groups, the review-only boundary, and the absence of forbidden connector and execution strings.

## Next Phase Recommendation
Use the local fixture template to continue paper-only readiness work for One 0DTE Options Trade. Do not add live execution, connectors, API actions, or database writes.

implementation reviewed in 10K8O
