# Analytics/Research Wrapper Test Scan After 10K8ZHZ

## Active test dependencies
- `tests/test_governance_health.py`
- `tests/test_governance_report.py`
- `tests/test_model_validation_report.py`
- `tests/test_market_research_store.py`
- `tests/test_data_intelligence_stack.py`

## Historical proof tests
- `tests/test_phase10k8zhr_analytics_migration_batch_1.py`
- `tests/test_phase10k8zhs_research_migration_batch_1.py`
- `tests/test_phase10k8zht_analytics_research_batch_1_legacy_scan.py`
- `tests/test_phase10k8zhv_analytics_downstream_redirection.py`
- `tests/test_phase10k8zhw_research_downstream_redirection.py`
- `tests/test_phase10k8zhx_analytics_research_batch_2_legacy_scan.py`
- `tests/test_phase10k8zhy_analytics_research_batch_2_checkpoint.py`

## Compatibility-only assertions
- Historical tests still assert wrapper imports exist.
- Historical tests still use wrapper filenames as evidence.
- That evidence is not a delete blocker by itself unless paired with an active runtime or test dependency.

## Summary
- Active test imports remain the main reason the wrappers are not delete-ready.
- Doc-only mentions are tracked separately and do not imply runtime dependency.
