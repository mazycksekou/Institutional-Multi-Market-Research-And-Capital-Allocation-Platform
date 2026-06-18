# 0DTE Field + Formula Gap Patch

## Executive Summary
This `0DTE Field + Formula Gap Patch` for `10K8ZB` applies the audited missing coverage identified in `PHASE10K8ZA_0DTE_DATA_FIELD_FORMULA_COVERAGE_AUDIT.md`.

`0DTE is the primary active trading lane`, but the stack remains `controlled paper-only prediction testing`, `local fixture-backed testing`, `readiness only`, and `review-only formulas`. The patch adds the missing 0DTE field coverage, safe local formula helpers, and a formula snapshot summary to the frozen paper pipeline without adding live execution.

## Existing Owner Used
The existing owner rule was preserved. No duplicate owner created.

## Audit Basis
This patch is based on `PHASE10K8ZA_0DTE_DATA_FIELD_FORMULA_COVERAGE_AUDIT.md`.

## 0DTE Field Gap Patch
`automation_scheduler/model_data_field_catalog.py` now exposes dedicated 0DTE field groups for liquidity/execution, GEX, volume profile, strategy, and macro-event coverage.

## Liquidity and Slippage Fields
`ZERO_DTE_LIQUIDITY_EXECUTION_FIELDS` covers:

- `bid_size`
- `ask_size`
- `quoted_depth`
- `liquidity_score`
- `slippage_estimate`
- `estimated_slippage`
- `max_contracts_at_top_of_book`
- `execution_capacity_warning`
- `volume_open_interest_ratio`

## Volume and Open Interest Fields
`volume_open_interest_ratio` is now covered as a first-class 0DTE field and formula output boundary.

## Gamma Exposure / GEX Fields
`ZERO_DTE_GEX_FIELDS` covers:

- `net_gex`
- `strike_gex`
- `call_gex`
- `put_gex`
- `gamma_flip_level`
- `gex_regime`

## Volume Profile Fields
`ZERO_DTE_VOLUME_PROFILE_FIELDS` covers:

- `strike_volume_profile`
- `volume_profile_peak_strike`
- `call_volume_by_strike`
- `put_volume_by_strike`
- `total_volume_by_strike`
- `volume_profile_skew`

## Strategy-Specific Fields
`ZERO_DTE_STRATEGY_FIELDS` covers:

- `strategy_type`
- `iron_condor`
- `iron_butterfly`
- `vertical_credit_spread`
- `long_straddle`
- `long_strangle`
- `single_call_put_scalp`
- `max_profit`
- `max_loss`
- `breakeven_low`
- `breakeven_high`
- `risk_reward_ratio`

## Macro Event Context Fields
`ZERO_DTE_MACRO_EVENT_FIELDS` covers:

- `cpi_day`
- `fomc_day`
- `jobs_day`
- `fed_speaker_day`

## Formula Gap Patch
`automation_scheduler/zero_dte_fixture_template.py` now includes safe local formula helpers:

- `build_zero_dte_formula_snapshot`
- `calculate_zero_dte_mid_price`
- `calculate_zero_dte_spread`
- `calculate_zero_dte_spread_percent`
- `calculate_zero_dte_volume_open_interest_ratio`
- `calculate_zero_dte_moneyness`
- `calculate_zero_dte_moneyness_percent`
- `calculate_zero_dte_estimated_slippage`

The formulas are local fixture-backed and review-only.

Formula strings preserved exactly:

- spread = ask - bid
- mid = (bid + ask) / 2
- spread_percent = spread / mid
- volume_open_interest_ratio = volume / open_interest
- moneyness_percent
- estimated_slippage

## Formula Snapshot
`build_zero_dte_formula_snapshot` returns:

- `mid`
- `spread`
- `spread_percent`
- `volume_open_interest_ratio`
- `moneyness`
- `moneyness_percent`
- `estimated_slippage_midpoint`
- `estimated_slippage_marketable`
- `formula_owner`
- `formula_mode`
- `guardrails`

## Pipeline Result Extension
`build_zero_dte_paper_pipeline_result` now includes:

- `formula_snapshots`
- `formula_snapshot_count`
- `average_spread_percent`
- `average_volume_open_interest_ratio`
- `average_estimated_slippage_midpoint`
- `formula_guardrails`

## Streamlit Visibility
`streamlit_app.py` now shows the controlled formula gap patch in the One 0DTE Options Trade pipeline preview.

## Technical Signal Boundary
`automation_scheduler/technical_signal_fields.py` was expanded for the 0DTE context fields that are consistent with the current market-field grouping.

## Universal Math Boundary
EV stays in quant_engine.py.
edge stays in quant_engine.py.
Kelly stays in quant_engine.py.
arbitrage stays out of TECHNICAL_SIGNAL_FIELDS.
paper_arbitrage_percentage remains review-only.

## Paper-Only Boundary
The patch stays paper-only prediction testing.

## Readiness-Only Boundary
The patch stays readiness only and review-only formulas.

## Review-Only Boundary
The formulas are review-only and local fixture-backed.

## Broker Boundary
No broker execution is added.

## Connector Boundary
No live connectors are added.

## API Boundary
No API calls are added.

## Database Write Boundary
No database writes are added.

## Unsupported Claim Boundary
No guaranteed profit language is added.
No assured profit language is added.

Boundary strings preserved exactly:

- no broker execution
- no real trade execution
- no live connectors
- no API calls
- no database writes
- no file upload
- no CSV parsing
- no frontend page files
- no guaranteed profit language
- no assured profit language

## Test Plan
The 10K8ZB test verifies the new field constants, the 0DTE catalog integration, the formula helpers, the formula snapshot output, the pipeline summary, and the Streamlit preview strings.

## Next Phase Recommendation
The audited gap patch is complete. Proceed to `10K9A Asset-Grade Cleanup Inventory`.

implementation reviewed in 10K8ZB
