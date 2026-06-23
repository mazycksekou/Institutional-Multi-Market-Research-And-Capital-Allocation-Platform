# Next Core Engine Extraction Plan (After 10K8ZGZ)

1. **Audit** – Stage 2A: classify every function in the target files (`quant_engine.py`, `risk_engine.py`, `market_pricing.py`, `model_probability.py`, `bet_decision_engine.py`, `bet_log.py`, `screenshot_intake.py`, `src/core/math_utils.py`, `src/core/clv.py`, `src/core/calibrator.py`, `src/core/backtester.py`).  
   *Output*: `PHASE10K8ZH0_*` docs + test file.

2. **Safe Core Math Foundation** – Stage 2B: add pure‑math helpers (`mean`, `median`, `variance`, `std_dev`, `dot_product`, `weighted_sum`, `covariance`, `correlation`, `correlation_matrix`, `portfolio_return`, `portfolio_variance`) to `src/core/math_utils.py`.  
   *Output*: `PHASE10K8ZH1_*` docs + test file.

3. **Risk Foundation** – Stage 2C: add canonical risk functions (`sharpe_ratio`, `max_drawdown`, `portfolio_risk`, `exposure_summary`) under `src/core/risk.py`.  
   *Output*: `PHASE10K8ZH2_*` docs + test file.

4. **Game‑Theory / Execution Edge Plan** – Stage 2D: plan only, no implementation.  
   *Output*: `PHASE10K8ZH3_*` docs + test file.

Stages are sequential; only after all pass can the next phase begin.
