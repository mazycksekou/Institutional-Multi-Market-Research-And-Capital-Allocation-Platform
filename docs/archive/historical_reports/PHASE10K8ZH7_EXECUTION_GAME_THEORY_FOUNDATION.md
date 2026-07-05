# Phase 10K8ZH7 - Execution / Game-Theory Foundation

## Executive Summary
Execution and game-theory ownership is canonical in `src/core/execution.py`, `src/core/market_impact.py`, and `src/core/game_theory.py`.
These modules are deterministic and do not place orders or start live trading.

## Scope
- estimate_slippage
- split_order
- liquidity_adjusted_size
- estimate_market_impact
- signaling_risk_score
- adverse_selection_score
- position_accumulation_plan
- thesis_break_triggered

## Ownership Map
- Canonical targets: `src/core/execution.py`, `src/core/market_impact.py`, `src/core/game_theory.py`
- Out of scope: brokerage execution, live connectors, AI/LLM, dashboard rewrite

