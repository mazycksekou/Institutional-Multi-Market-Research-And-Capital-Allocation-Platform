# Core Engine Compatibility Wrapper Report After 10K8ZH9

## Executive Summary
The canonical `src/core/*` modules now own the shared math and orchestration surface.
Legacy root engine files remain importable as compatibility wrappers.

## Compatibility Wrappers
- `quant_engine.py`
- `market_pricing.py`
- `model_probability.py`
- `risk_engine.py`
- `bet_decision_engine.py`

## Notes
- Root imports remain available for downstream code.
- The canonical modules are the primary owners.

