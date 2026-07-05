# PHASE 10K8ZHZ Analytics/Research Wrapper Delete Proof

## Canonical ownership
- `src.analytics` owns deterministic performance, attribution, calibration, governance, report, and model-evaluation summaries.
- `src.research` owns deterministic research lane descriptors, experiment metadata, hypothesis records, ablation plans, and storage/schema descriptors.
- `src/analytics/model_governance/governance_health.py` is the relocated canonical file for governance-health logic.

## Wrapper classification
| File | Classification | Blocker summary | Canonical replacement target |
| --- | --- | --- | --- |
| `model_governance/governance_health.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_governance_health.py`; also exported by `model_governance/__init__.py`. | `src.analytics.governance.build_governance_health` |
| `model_governance/governance_report.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_governance_report.py`; also exported by `model_governance/__init__.py`. | `src.analytics.reports.generate_governance_report` |
| `model_governance/model_validation_report.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_model_validation_report.py`; also exported by `model_governance/__init__.py`. | `src.analytics.reports.build_model_validation_report` |
| `research/market_research_schema.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_market_research_store.py` and multiple historical tests. | `src.research.storage` |
| `research/market_research_store.py` | `FILE_IO_OR_STORAGE_BLOCKED` | Owns the legacy local DB path and SQLite file-IO compatibility surface; imported by active tests. | `src.research.storage` |
| `automation_scheduler/deep_learning_research_lanes.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_data_intelligence_stack.py`; compatibility wrapper only. | `src.research.build_deep_learning_research_lanes` |
| `automation_scheduler/tabular_ml_research.py` | `ACTIVE_TEST_DEPENDENCY` | Imported by `tests/test_data_intelligence_stack.py`; compatibility wrapper only. | `src.research.build_tabular_ml_research_lanes` |
| `automation_scheduler/model_maturity_registry.py` | `SCHEDULER_COUPLED_BLOCKED` | Used by scheduler/runtime paths and `tests/test_data_intelligence_stack.py`; not a thin wrapper. | `src.research.build_tabular_maturity_records` and `src.research.build_deep_learning_maturity_records` |

## Delete-readiness summary
- No wrapper in this phase is delete-ready.
- The thin wrappers are compatibility-only, but they remain active test dependencies.
- `automation_scheduler/model_maturity_registry.py` remains scheduler-coupled and is not a delete candidate yet.
- `COMPATIBILITY_WRAPPER_ONLY` is still the right description for the thin wrapper modules.
- `DELETE_READY_AFTER_PROOF` does not apply to any wrapper in this phase.
- `automation_scheduler remains a decommission target`.

## Evidence boundaries
- No AI or LLM behavior is introduced.
- No connectors are imported from canonical analytics/research modules.
- No legacy odds or prediction-market shells are reintroduced.
