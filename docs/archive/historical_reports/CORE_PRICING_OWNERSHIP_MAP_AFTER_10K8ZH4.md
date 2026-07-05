# Core Pricing Ownership Map After 10K8ZH4

## Ownership
- `src/core/pricing.py` owns odds conversion, no-vig math, EV, edge, payout, profit, and price normalization.
- `market_pricing.py` is a compatibility wrapper.
- `quant_engine.py` is a compatibility wrapper for shared pricing helpers.
- canonical target: `src/core/pricing.py`

## Migration Notes
- Pure pricing helpers moved to `src/core/pricing.py`.
- No connectors, providers, or live dependencies were introduced.
- Root compatibility imports remain available for downstream code.
