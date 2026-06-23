# Phase 10K8ZHB - Service Layer Ownership Audit

## Executive Summary
The canonical service layer is already thin in the right places:

- `src/services/decision_engine.py` owns decision orchestration and only calls `src.core`.
- `src/services/enrichment_service.py` owns ticket enrichment orchestration and only calls canonical bridge services.
- `src/services/action_betting_service.py` owns request shaping and provider-router orchestration for action endpoints.
- `src/services/bet_csv_service.py` owns the local CSV betting ledger shell.
- `src/services/model_backtest_service.py` owns local backtest orchestration.
- `src/services/odds_runtime_bridge.py` and `src/services/prediction_market_runtime_bridge.py` own the canonical bridge surfaces for odds and prediction markets.

No direct math, pricing, probability, risk, or portfolio implementation remains in the canonical service layer. Those responsibilities are already in `src/core`.

Legacy compatibility shells remain in place where callers still depend on them:

- `screenshot_intake.py`
- `bet_log.py`
- `bet_decision_engine.py`

This phase does not rewrite the dashboard, bootstrap, or live execution path. AI/LLM and brokerage remain deferred.

## Service Inventory

- `src/services/decision_engine.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/enrichment_service.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/action_betting_service.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/bet_csv_service.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/model_backtest_service.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/odds_runtime_bridge.py`: `SERVICE_ORCHESTRATION_OWNER`
- `src/services/prediction_market_runtime_bridge.py`: `SERVICE_ORCHESTRATION_OWNER`
- `screenshot_intake.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `bet_log.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `bet_decision_engine.py`: `COMPATIBILITY_SHIM_CANDIDATE`

## Misplaced Logic Findings

- No misplaced math, pricing, probability, risk, or portfolio logic was found in the canonical service modules.
- Connector-like behavior is isolated to the bridge layer and stays disabled/read-only.
- API-like behavior still lives in `src/api/*`, not in `src/services/*`.
- Dashboard-like behavior is not in `src/services/*`.

## Service Thinning Sequence

1. Keep `src/services/decision_engine.py` as the canonical orchestration shell over `src/core`.
2. Keep `src/services/enrichment_service.py` as the canonical enrichment shell over bridge helpers.
3. Move screenshot workflow ownership from `screenshot_intake.py` into `src/services/screenshot_workflow.py`.
4. Keep `bet_log.py` as a local storage compatibility shell until a dedicated storage/service plan exists.
5. Keep `bet_decision_engine.py` as a compatibility shell until the remaining root wrapper callers are redirected.
6. Continue migrating any remaining `automation_scheduler` orchestration into `src/services` only when it is local-only and test-protected.

## Required Statement
Useful service orchestration belongs in `src/services`, while math and risk live in `src/core`. `screenshot_intake.py`, `bet_log.py`, and `bet_decision_engine.py` remain compatibility shells for now, and AI/LLM plus brokerage are still deferred.
