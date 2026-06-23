# Phase 10K8ZH3 — Game‑Theory / Execution Edge Plan

## Status

Planning only. No implementation.

## Concepts Documented

- Market impact
- Slippage modelling
- Signalling risk
- Adverse selection
- Position accumulation
- Order splitting
- Liquidity‑adjusted Kelly
- Stop‑loss / thesis break
- Exposure‑aware sizing
- Bayesian update loop
- War of attrition in live markets
- Limit‑order / liquidity‑provider game

## Future Implementation Locations

- `src/core/execution.py` – execution math, order splitting, slippage.
- `src/core/market_impact.py` – market‑impact models.
- `src/core/game_theory.py` – game‑theoretic decision logic.
- `src/core/portfolio.py` – portfolio‑level exposure management.
- `src/services/decision_engine.py` – orchestration of the decision loop.
- `src/brokerage/` – deferred; for paper/live execution only.

## What Is Deferred

- AI / LLM reasoning
- Broker execution
- Live trading
- Scraping
- Credential reads
