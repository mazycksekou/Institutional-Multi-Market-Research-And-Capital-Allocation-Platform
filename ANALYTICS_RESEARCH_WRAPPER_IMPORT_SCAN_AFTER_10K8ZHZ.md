# Analytics/Research Wrapper Import Scan After 10K8ZHZ

## Runtime import references
- `model_governance/__init__.py` exports `generate_governance_report` and `get_governance_health`.
- `automation_scheduler/__init__.py` exports research lane helpers through canonical `src.research`.
- `automation_scheduler/model_maturity_registry.py` imports canonical research maturity helpers.

## Test import references
- `tests/test_governance_health.py`
- `tests/test_governance_report.py`
- `tests/test_model_validation_report.py`
- `tests/test_market_research_store.py`
- `tests/test_data_intelligence_stack.py`
- `tests/test_phase10k8zhr_analytics_migration_batch_1.py`
- `tests/test_phase10k8zhs_research_migration_batch_1.py`
- `tests/test_phase10k8zht_analytics_research_batch_1_legacy_scan.py`
- `tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- `tests/test_phase10k8zhw_research_downstream_redirection.py`
- `tests/test_phase10k8zhx_analytics_research_batch_2_legacy_scan.py`

## Monkeypatch or mock targets
- `model_governance/governance_health.py` is still patched by downstream tests that compare wrapper and canonical health output.
- `automation_scheduler/__init__.py` is still patched in the research redirection proof to avoid local-data/env coupling.

## Historical proof evidence
- Phase docs from 10K8ZHR through 10K8ZHY intentionally mention the wrappers as part of the migration trail.

## Doc-only evidence
- Numerous `.md` audit documents reference the wrapper filenames as migration history.

## Compatibility export
- `model_governance/__init__.py`
- `automation_scheduler/__init__.py`
- `src/analytics/__init__.py`
- `src/research/__init__.py`

## String-only metadata
- File names and wrapper names appear in audit docs as historical evidence, not as runtime dependencies.
