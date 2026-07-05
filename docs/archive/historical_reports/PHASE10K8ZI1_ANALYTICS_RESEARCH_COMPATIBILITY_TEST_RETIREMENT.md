# PHASE10K8ZI1 Analytics/Research Compatibility Test Retirement

Canonical ownership now lives in `src.analytics` and `src.research`.
This phase retires the old compatibility-oriented tests that used to preserve
legacy wrapper ownership assumptions.

Retired test dependencies:
- `tests/test_governance_health.py`
- `tests/test_governance_report.py`
- `tests/test_model_validation_report.py`
- `tests/test_market_research_store.py`
- `tests/test_data_intelligence_stack.py`

Compatibility references are now historical evidence only.
The canonical runtime checks validate:
- `src.analytics.governance`
- `src.analytics.reports`
- `src.research.storage`
- `src.research.maturity`

No live behavior, AI/LLM, brokerage, or connector activation is introduced.
