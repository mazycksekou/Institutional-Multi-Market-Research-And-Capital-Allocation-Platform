# Data/Backtesting Foundation Audit After 10K8ZHI

## Executive Summary
The repo already has a strong canonical math/risk foundation in `src/core`, but the data and backtesting layers are still distributed across legacy `automation_scheduler`, `model_governance`, and root-level compatibility modules.

We do not implement backtesting in this phase.
We only map ownership and define the migration order.

## Canonical Architecture
- `src.data`: historical ingestion, stores, schemas, data lineage, source registries, replay artifacts
- `src.backtesting`: backtest orchestration, simulation, replay, leakage checks, strategy evaluation
- `src.analytics`: pricing, probability, CLV, risk, performance, calibration, governance, attribution
- `src.research`: experimental and exploratory research lanes, deep-dive analysis, model research stores

## Current Canonical Anchors
- `src.core.math_utils`
- `src.core.risk`
- `src.core.backtester`
- `src.services.model_backtest_service`
- `src.api.model_backtest_routes`
- `src.api.performance_routes`

## Current Legacy Owners
- `automation_scheduler.backtesting_engine`
- `automation_scheduler.backtest_dataset_builder`
- `automation_scheduler.backtest_schema`
- `automation_scheduler.backtest_leakage`
- `automation_scheduler.backtest_strategy_bankroll`
- `automation_scheduler.backtest_strategy_profiles`
- `automation_scheduler.calibration*`
- `automation_scheduler.performance_metrics`
- `automation_scheduler.clv_tracker`
- `automation_scheduler.risk_of_ruin`
- `automation_scheduler.drawdown_controls`
- `automation_scheduler.liquidity_risk`
- `automation_scheduler.review_queue`
- `automation_scheduler.data_*`
- `automation_scheduler.historical_*`
- `automation_scheduler.model_*`
- `model_governance.*`
- `research.*`
- root compatibility modules: `market_pricing.py`, `quant_engine.py`, `risk_engine.py`, `bet_log.py`, `bet_decision_engine.py`, `screenshot_intake.py`

## Duplicated Logic
- Backtest schema and leakage handling appear in both `automation_scheduler` and core/service layers.
- Performance and calibration logic are split across `automation_scheduler`, `model_governance`, and `src/core`.
- Market pricing / risk / portfolio helpers live in root compatibility modules and `src.core`.

## Orphaned Utilities
- Root compatibility wrappers that now mostly forward to canonical modules:
  - `quant_engine.py`
  - `risk_engine.py`
  - `bet_decision_engine.py`
  - `screenshot_intake.py`
- Historical store helpers that should eventually move under `src.data`:
  - `research/market_research_store.py`
  - `automation_scheduler/outcome_store.py`
  - `automation_scheduler/paper_trade_ledger.py`

## Migration Order
1. Extract `src.data` for historical stores, lineage, and registry-style utilities.
2. Extract `src.backtesting` for schema, leakage, replay, and simulation orchestration.
3. Consolidate `src.analytics` for pricing, calibration, risk, performance, and governance.
4. Move research-only code into `src.research`.
5. Reduce root compatibility modules to thin shells or delete them after proof.

## Safety Boundaries
- No live API calls.
- No credential reads at import time.
- No AI implementation.
- No brokerage execution implementation.
- No behavior-changing production migrations.

