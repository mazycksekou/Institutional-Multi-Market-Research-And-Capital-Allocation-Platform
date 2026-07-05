# Analytics/Research Compatibility Test Retirement Map After 10K8ZI1

| Retired test | Canonical replacement | Status |
| --- | --- | --- |
| `tests/test_governance_health.py` | `src.analytics.governance.build_governance_health` | redirected |
| `tests/test_governance_report.py` | `src.analytics.reports.generate_governance_report` | redirected |
| `tests/test_model_validation_report.py` | `src.analytics.reports.build_model_validation_report` | redirected |
| `tests/test_market_research_store.py` | `src.research.storage` | redirected |
| `tests/test_data_intelligence_stack.py` | `src.research` | redirected |

Wrapper ownership assumptions are no longer primary.
Canonical imports now carry the regression coverage.
