# Next Data / Backtesting Layer Plan After 10K8ZHH

## Plan

The next recommended phase should focus on the data/backtesting layer:

- keep `src.core` as the canonical math and evaluation layer
- keep `src.services.model_backtest_service` as the local orchestration shell
- review the remaining `automation_scheduler` backtesting and history helpers for safe service migration
- do not start AI/LLM integration yet
- do not start brokerage/live execution yet

## Goal

Turn the remaining historical data and backtest helpers into a smaller, cleaner service/data boundary before any higher-level production work begins.

## Required Reminder

AI/LLM is deferred. Brokerage/live execution is deferred. Live production is deferred.
