# PREDICTION_MARKET_COMPATIBILITY_TEST_REDIRECTION_AFTER_10K8ZGS

## Test Redirection Summary
The historical compatibility tests still intentionally touch legacy prediction-market shells. Those references are preserved as evidence, not as deletion blockers by themselves.

## Tests Still Touching Legacy Shells
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

## Redirection Decision
No test redirection was applied in this proof phase because the runtime scheduler still depends on the legacy shell layer.

The correct next step is to continue redirecting the runtime scheduler and historical compatibility tests toward:
- `src.services.prediction_market_runtime_bridge`
- `src.providers.prediction_markets`
- `src.connectors.prediction_market_data`

## Result
The test surface still proves compatibility, but it does not yet prove delete readiness.
