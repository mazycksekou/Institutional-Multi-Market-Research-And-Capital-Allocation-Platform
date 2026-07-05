# Test Guardrail Stabilization

## Executive Summary

Phase 10K7B is a source-text guardrail stabilization review. It removes a brittle `git`-based assertion from the 10K6K test so the check stays focused on the shell contract instead of global repo state.

The current implementation reviewed in 10K7B keeps `no prediction testing`, `no live connectors`, `no API calls`, and `no database writes` in place.

## Problem Found

The 10K6K test had a brittle git-status assertion tied to `global untracked files`.

That meant a future phase could fail for reasons unrelated to the dashboard shell contract itself. The failure mode was a `brittle git-status assertion` rather than a true source-text regression.

## Stabilization Change

The 10K6K regression test is now a `source-text guardrail`.

It now keeps `no subprocess git checks`, `no git ls-files`, `no git status`, and `no temporary git shim`.

The test still verifies the shell strings, the readiness display helpers, the forbidden connector/action strings, and the local frontend page boundary.

## Guardrails Preserved

- `connector guardrails remain active`
- `no prediction testing`
- `no live connectors`
- `no API calls`
- `no database writes`

## Frontend Page Boundary

The page boundary check is limited to:

- `pages/*.py`
- `app/pages/*.py`
- `frontend/*.py`
- `frontend/pages/*.py`

This keeps the test limited to `no separate frontend page files`.

## Prediction Testing Boundary

no prediction testing

The stabilization work does not enable execution, model runs, or backtest controls.

## Connector Boundary

no live connectors

The stabilization work does not add connector actions or scraper actions.

## Database Write Boundary

no database writes

The stabilization work does not write runtime rows, dashboard rows, or warehouse rows.

## Test Plan

- Run the targeted stabilization regression.
- Run the 10K6K shell review regression.
- Run the repo `test`, `smoke`, and `stat` workflow.
- Confirm `no temporary git shim` is required.

## Next Phase Recommendation

Proceed with later review phases using the stabilized source-text guardrail only.

implementation reviewed in 10K7B.
