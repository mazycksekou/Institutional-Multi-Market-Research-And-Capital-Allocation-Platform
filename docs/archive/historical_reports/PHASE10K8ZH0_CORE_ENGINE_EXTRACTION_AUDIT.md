# Phase 10K8ZH0 — Core Engine Extraction Audit

## Status

Audit complete. No source migration or deletion performed.

## Audit Targets

- `quant_engine.py`
- `risk_engine.py`
- `market_pricing.py`
- `model_probability.py`
- `bet_decision_engine.py`
- `bet_log.py`
- `screenshot_intake.py`
- `src/core/math_utils.py`
- `src/core/clv.py`
- `src/core/calibrator.py`
- `src/core/backtester.py`

## Classification Tags Used

| Tag | Definition |
|-----|------------|
| `MIGRATE_TO_SRC_CORE_MATH` | Pure mathematical helper |
| `MIGRATE_TO_SRC_CORE_PROBABILITY` | Probability transformation |
| `MIGRATE_TO_SRC_CORE_PRICING` | Pricing / fair odds |
| `MIGRATE_TO_SRC_CORE_RISK` | Risk / exposure |
| `MIGRATE_TO_SRC_CORE_PORTFOLIO` | Portfolio metrics |
| `MIGRATE_TO_SRC_CORE_EXECUTION` | Execution / slippage |
| `MIGRATE_TO_SRC_CORE_GAME_THEORY` | Game‑theory logic |
| `MIGRATE_TO_SRC_SERVICES` | Orchestration / workflow |
| `KEEP_ENTRYPOINT_OR_DASHBOARD` | Entrypoint or dashboard |
| `COMPATIBILITY_SHIM_CANDIDATE` | Wrapper to preserve import path |
| `DELETE_CANDIDATE_AFTER_PROOF` | Safe to delete after migration |
| `UNSAFE_TO_TOUCH` | Live connector, execution, or AI |

Full inventory is in `CORE_ENGINE_FUNCTION_INVENTORY_AFTER_10K8ZH0.md`.

## Key Findings

- `quant_engine.py` contains wrappers that belong in `src/core/`. It is **not** a deletion candidate.
- `risk_engine.py` duplicates logic that will move to `src/core/risk.py`; shim will remain.
- `market_pricing.py` contains pricing helpers that belong in `src/core/pricing.py`.
- `model_probability.py` contains probability blending logic that belongs in `src/core/probability.py`.
- `bet_decision_engine.py` orchestrates decision flow – `MIGRATE_TO_SRC_SERVICES`.
- `screenshot_intake.py` orchestrates screenshot workflow – `MIGRATE_TO_SRC_SERVICES`.
- `main.py` and `streamlit_app.py` are `KEEP_ENTRYPOINT_OR_DASHBOARD`.

No live imports, no credential reads, no AI/LLM calls were found.

## Next Phase

Stage 2B – Safe Core Math Foundation (Phase 10K8ZH1).
