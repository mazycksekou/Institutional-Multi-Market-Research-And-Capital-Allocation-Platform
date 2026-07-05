# Data / Backtesting Migration Sequence After 10K8ZHL

## Recommended Sequence

1. Stabilize `src.data` contracts, registry, validation, and local loader.
2. Stabilize `src.backtesting` contracts, leakage, replay, and simulation.
3. Move storage-oriented data helpers out of `automation_scheduler`.
4. Move backtest dataset builders and leakage checks into `src.backtesting`.
5. Consolidate analytics and governance reporting into `src.analytics`.
6. Move research-only code into `src.research`.
7. Retire compatibility wrappers only after import proof and test redirection.

## Current Priority

`src.data` and `src.backtesting` first, then analytics/research extraction.

