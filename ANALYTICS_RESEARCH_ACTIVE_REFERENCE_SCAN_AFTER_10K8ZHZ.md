# Analytics/Research Active Reference Scan After 10K8ZHZ

## Active reference categories
- runtime import
- test import
- monkeypatch or mock target
- monkeypatch or mock targets
- doc-only evidence
- historical proof evidence
- compatibility export
- string-only metadata

## Current scan summary
- `model_governance/governance_health.py` is an active test dependency and a compatibility export.
- `model_governance/governance_report.py` is an active test dependency and a compatibility export.
- `model_governance/model_validation_report.py` is an active test dependency and a compatibility export.
- `research/market_research_schema.py` is an active test dependency and historical proof evidence.
- `research/market_research_store.py` is an active test dependency and historical proof evidence.
- `automation_scheduler/deep_learning_research_lanes.py` is an active test dependency and a compatibility export.
- `automation_scheduler/tabular_ml_research.py` is an active test dependency and a compatibility export.
- `automation_scheduler/model_maturity_registry.py` is a runtime import and scheduler-coupled blocker.

## Note
- Doc-only evidence is tracked separately and does not count as a runtime dependency.
