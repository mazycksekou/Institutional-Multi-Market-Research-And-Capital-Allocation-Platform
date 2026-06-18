# Paper-Only Fixture Validation Helper

## Executive Summary

Phase 10K8C is review-only. It adds a tiny paper-only fixture validation helper to the existing backtest dataset owner without starting prediction testing, adding connectors, changing UI, or writing database rows.

The current implementation reviewed in 10K8C stays bounded as a `Controlled Navigation Shell` with a local `readiness display preview`. It keeps `no prediction testing`, `no live connectors`, `no API calls`, and `no database writes` in place.

This helper builds on the `Paper-Only Fixture Testing Contract` and preserves `source-text guardrails` plus the `no temporary git shim` boundary.

## Existing Owner Used

The existing owner rule is to reuse the established fixture/backtest dataset owner rather than create a new module.

The helper is added to `automation_scheduler/backtest_dataset_builder.py`, which already owns normalized backtest dataset assembly and paper fixture discovery.

## Helper Added

The helper added in 10K8C is:

- `PAPER_ONLY_FIXTURE_REQUIRED_FIELDS`
- `PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS`
- `validate_paper_only_fixture_rows`

This helper validates local fixture rows only. It does not execute models, score predictions, run backtests, call APIs, or write database rows.

## Fixture Field Contract

The shared fixture field contract includes:

- `fixture_id`
- `sport_or_market`
- `event_id`
- `prediction_target`
- `selection`
- `model_probability`
- `market_odds_american`
- `implied_probability`
- `expected_value`
- `stake_units`
- `bankroll_snapshot`
- `result_label`
- `outcome_known`
- `source_type`
- `execution_mode`

The helper also recognizes the review fields:

- `rows_tested`
- `rows_valid`
- `rows_invalid`
- `missing_field_reasons`
- `warning_reasons`

## Validation Behavior

The helper returns a plain dict only.

It counts:

- `rows_tested`
- `rows_valid`
- `rows_invalid`

It reports:

- `missing_field_reasons`
- `warning_reasons`
- `execution_mode`
- `source_type`
- `prediction_testing_started`
- `live_connectors_enabled`
- `api_calls_enabled`
- `database_writes_enabled`

Validation rules:

- `execution_mode` must be `paper_only` or `fixture_only`
- `source_type` must contain `fixture` or equal `local_fixture`
- `prediction_testing_started` is always false
- `live_connectors_enabled` is always false
- `api_calls_enabled` is always false
- `database_writes_enabled` is always false
- missing required fields make a row invalid
- invalid probability values outside `[0, 1]` add warning reasons
- invalid numeric odds, stake, or EV values add warning reasons
- do not label quality automatically
- do not hide valid results because sample size is low
- user threshold review-only
- validity check only
- no prediction testing started in 10K8C

## Paper-Only Boundary

paper-only prediction testing

The helper supports later paper-only review only. It does not start prediction testing.

## Fixture-Backed Boundary

local fixture-backed testing

The helper validates local fixture rows only. It does not introduce live money or production execution.

## Prediction Testing Boundary

no prediction testing

This phase does not start prediction testing.

## Connector Boundary

no live connectors

This phase does not add vendor connectors, scraper actions, or live data wiring.

## API Boundary

no API calls

This phase does not add API actions or remote calls.

## Database Write Boundary

no database writes

This phase does not write warehouse rows, runtime rows, or dashboard rows.

## Guardrails Preserved

- `no duplicate owner created`
- `no temporary git shim`
- `do not label quality automatically`
- `do not hide valid results because sample size is low`
- `user threshold review-only`
- `validity check only`

## Test Plan

- Run the targeted helper regression.
- Run the 10K6K shell review regression.
- Run the repo `test`, `smoke`, and `stat` workflow.
- Confirm the helper stays dependency-free and review-only.

## Next Phase Recommendation

Proceed only if the helper remains paper-only, fixture-backed, and aligned with the existing owner rule.

implementation reviewed in 10K8C.

