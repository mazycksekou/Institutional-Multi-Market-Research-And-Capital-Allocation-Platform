# Core Engine Ownership Map (After 10K8ZH0)

```
src/core/math_utils.py    : math functions (stateless)
src/core/clv.py           : CLV helpers
src/core/calibrator.py    : probability calibrators
src/core/backtester.py    : walk‑forward backtest
src/core/risk.py          : risk helpers (new in 10K8ZH2)
src/core/pricing.py       : pricing helpers (future)
src/core/probability.py   : probability blending (future)
src/core/execution.py     : execution math (future)
src/core/game_theory.py   : game‑theory (future)
src/services/decision_engine.py : decision flow (future)
src/services/screenshot_workflow.py : screenshot orchestration (future)
```

Source files that currently host these functions will become compatibility shims after migration.
