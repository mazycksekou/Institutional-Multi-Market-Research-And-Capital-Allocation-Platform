# PHASE 10K8ZHK Backtesting Foundation

## Executive Summary

This phase creates the first canonical `src.backtesting` foundation while
preserving all current behavior. The package owns backtest dataset contracts,
leakage checks, replay planning, and simulation planning. It is intentionally
local-only and does not activate execution.

## Current HEAD

Starting HEAD for this phase:

`a3c48605cf28a84eeeb2d80fcbd19e2ce0abe17a`

## Why `src.backtesting` Exists

`src.backtesting` is the canonical home for:

- backtest dataset contracts
- dataset ordering checks
- leakage detection
- replay planning
- simulation planning

The existing `src.core.backtester` remains the canonical kernel for the legacy
walk-forward implementation; `src.backtesting` adds a foundation layer around it
without changing runtime behavior.

## What This Phase Does Not Do

- no live data fetches
- no broker execution
- no strategy activation
- no AI/LLM
- no dashboard rewrite
- no network access

## Files Created

- `src/backtesting/__init__.py`
- `src/backtesting/contracts.py`
- `src/backtesting/datasets.py`
- `src/backtesting/leakage.py`
- `src/backtesting/replay.py`
- `src/backtesting/simulation.py`

## Import-Safety Guarantees

- `src.backtesting` imports safely.
- dataset validation is pure and chronological.
- leakage checks are deterministic and local-only.
- replay and simulation are planning contracts, not trade execution.

## Validation Summary

The foundation proves that the package can:

- validate row order
- detect future timestamps
- build replay plans without execution
- build simulation plans without trades

## Test Summary

The phase proof test validates import safety, ordering checks, leakage checks,
local replay planning, and non-executing simulation planning.

## Next Recommended Phase

Use the ownership maps to plan the next `src.analytics` and `src.research`
extractions.
