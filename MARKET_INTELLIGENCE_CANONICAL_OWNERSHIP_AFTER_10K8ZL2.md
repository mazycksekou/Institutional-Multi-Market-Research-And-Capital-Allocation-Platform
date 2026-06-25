# Market Intelligence Canonical Ownership After 10K8ZL2

- `src.market_intelligence.contracts` owns the standard report contract.
- `src.market_intelligence.report` owns report construction and validation.
- `src.market_intelligence.sports` owns sports-betting intelligence helpers.
- `src.market_intelligence.prediction_markets` owns prediction-market intelligence helpers.
- `src.market_intelligence.options` owns options / 0DTE / GEX / Vanna modeling helpers.
- `src.market_intelligence.manifold` owns canonical manifold / cross-asset intelligence helpers.
- `src.market_intelligence.impact` owns generic impact-summary helpers.
- `src.market_intelligence.crypto` and `src.market_intelligence.futures` own market-specific wrappers.

No market-intelligence helper in this phase activates live data, broker logic, AI, or connectors.

