# PREDICTION_MARKET_COMPATIBILITY_REFERENCE_SCAN_AFTER_10K8ZGU

## Scan Summary
Historical references to the legacy prediction-market shells still exist, but the runtime scheduler path is now canonical and the remaining references are evidence-only or compatibility-only.

## Redirected Runtime References
- `automation_scheduler/__init__.py`
- `automation_scheduler/scheduler_runner.py`
- `automation_scheduler/settlement_discovery.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/prediction_market_outcome_candidates.py`
- `automation_scheduler/kalshi_readonly_readiness.py`

These files now rely on `src.services.prediction_market_runtime_bridge`.

## Historical Evidence / Compatibility References
- `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_screenshot_analysis.py`

## Remaining Legacy Shell References
The legacy shells themselves still exist and are still importable:

- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Interpretation
The reference scan confirms the compatibility surface is shrinking, but the remaining evidence still blocks deletion.
