# PHASE 10K8ZL4 Prediction-Market Intelligence Absorption

Prediction-market intelligence is now represented canonically in `src.market_intelligence.prediction_markets` and `src.market_intelligence.manifold`.

Status:
- YES/NO price, probability movement, liquidity, support/resistance, and invalidation helpers are canonicalized.
- Scheduler manifold wrappers now forward to canonical helpers where safe.
- No Kalshi / Polymarket account access, live connector calls, or credentials were introduced.

