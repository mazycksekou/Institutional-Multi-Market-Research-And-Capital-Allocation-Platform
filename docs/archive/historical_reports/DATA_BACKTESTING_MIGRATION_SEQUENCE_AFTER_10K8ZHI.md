# Data/Backtesting Migration Sequence After 10K8ZHI

## Recommended Order
1. `src.data`
   - historical storage
   - source registries
   - lineage
   - dataset catalogues

2. `src.backtesting`
   - schema
   - leakage checks
   - replay
   - simulation
   - strategy profiling

3. `src.analytics`
   - pricing
   - CLV
   - calibration
   - risk
   - performance attribution
   - governance

4. `src.research`
   - research stores
   - exploratory diagnostics
   - experimental lanes

## Why This Order
- Data ownership must be stable before backtesting can be simplified.
- Backtesting must be stable before analytics can be thinned safely.
- Research should be isolated last so it can consume the canonical data and analytics foundations without owning them.

## What Stays Put For Now
- `src.core` remains the math/risk kernel.
- `src.services.model_backtest_service` remains a thin orchestration wrapper.
- `src.api.model_backtest_routes` remains a thin route wrapper.

