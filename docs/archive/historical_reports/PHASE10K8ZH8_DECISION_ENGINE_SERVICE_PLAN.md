# Phase 10K8ZH8 - Decision Engine Service Plan

## Executive Summary
`src/services/decision_engine.py` is the thin orchestration shell for the new core layer.
It is allowed to combine pricing, probability, risk, portfolio, execution, and game-theory helpers.

## Scope
- service orchestration only
- no connector calls
- no broker/live execution
- no dashboard rendering

## Ownership
- `src/services/decision_engine.py` owns orchestration
- `src/core/pricing.py`, `src/core/probability.py`, `src/core/risk.py`, `src/core/portfolio.py`, `src/core/execution.py`, `src/core/market_impact.py`, `src/core/game_theory.py` own pure math

## Deferred
- AI/LLM deferred
- brokerage/live execution deferred

