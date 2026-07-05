# Phase 10K8ZHA - Core Engine Migration Checkpoint

## Executive Summary
The core engine migration block is complete for pricing, probability, portfolio, execution, market impact, and game theory.
Service orchestration remains thin and AI/brokerage are deferred.

## Ownership
- Pricing ownership: `src/core/pricing.py`
- Probability ownership: `src/core/probability.py`
- Risk ownership: `src/core/risk.py`
- Portfolio ownership: `src/core/portfolio.py`
- Execution/game-theory ownership: `src/core/execution.py`, `src/core/market_impact.py`, `src/core/game_theory.py`
- Service orchestration ownership: `src/services/decision_engine.py`

## Deferred
- AI/LLM deferred
- Brokerage/live execution deferred
- Dashboard/API cleanup remains

