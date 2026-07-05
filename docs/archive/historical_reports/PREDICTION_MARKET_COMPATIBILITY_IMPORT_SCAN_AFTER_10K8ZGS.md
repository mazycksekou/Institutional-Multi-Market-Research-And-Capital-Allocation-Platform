# PREDICTION_MARKET_COMPATIBILITY_IMPORT_SCAN_AFTER_10K8ZGS

## Import Scan Summary
The scan shows the legacy prediction-market shells still appear in runtime scheduler code, historical tests, and one documentation string.

## Runtime Imports Still Present
- `automation_scheduler/__init__.py`
  - `KalshiReadonlyAdapter`
  - `get_kalshi_snapshot`
  - `summarize_kalshi_snapshot`
  - `validate_kalshi_snapshot`
  - `write_kalshi_snapshot`
- `automation_scheduler/scheduler_runner.py`
  - `KalshiReadonlyAdapter`
  - `get_kalshi_snapshot`
  - `summarize_kalshi_snapshot`
- `automation_scheduler/settlement_discovery.py`
  - `KalshiReadonlyAdapter`
- `automation_scheduler/calibration_collector.py`
  - `KalshiReadonlyAdapter`
- `automation_scheduler/prediction_market_outcome_candidates.py`
  - `KalshiReadonlyAdapter`

## Historical Test Imports Still Present
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`
- `tests/test_phase10k8zfv_runtime_provider_migration_batch_1.py`
- `tests/test_phase10k8zg2_legacy_deletion_readiness_audit.py`
- `tests/test_screenshot_analysis.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`

## Doc-Only Reference
- `src/api/market_utility_routes.py`
  - contains the text `kalshi_client.py`

## After-Redirection Status
No runtime import redirection was needed for this proof step beyond documenting the remaining blockers.

The scan confirms the shells are still retained because runtime and test references still exist.
