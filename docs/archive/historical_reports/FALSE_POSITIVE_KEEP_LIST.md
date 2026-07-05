# False Positive Keep List

The following stem collisions are not duplicate ownership:
- `src/analytics/performance.py` vs `src/api/schemas/performance.py`
- `src/core/execution.py` vs `src/brokerage/execution.py`
- `src/core/risk.py` vs `src/market_intelligence/risk.py`
- `src/providers/normalization.py` vs `src/providers/zero_dte_stocks/normalization.py`
- `src/connectors/*/adapter.py` and `src/providers/*/adapters.py` families, which are domain-specific per package

These names overlap lexically but not semantically.

