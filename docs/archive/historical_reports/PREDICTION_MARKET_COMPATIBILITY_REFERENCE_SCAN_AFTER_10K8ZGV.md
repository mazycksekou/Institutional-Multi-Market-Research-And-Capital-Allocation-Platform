# Prediction-Market Compatibility Reference Scan After 10K8ZGV

## Scan Summary
The remaining legacy prediction-market shell references are now mostly historical or evidence-only.

## Canonical Runtime / Test References
- `src.services.prediction_market_runtime_bridge`
- `src.connectors.prediction_market_data`
- `src.providers.prediction_markets`
- `screenshot_intake`
- `automation_scheduler.scheduler_runner`
- `automation_scheduler.kalshi_readonly_readiness`

## Updated Target Tests
- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_screenshot_analysis.py`

## Historical Evidence Still Present
- `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py`
- `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py`
- `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py`
- `tests/test_phase10k8zgu_prediction_market_historical_compatibility_test_redirection.py`

## Legacy Shell Files Still on Disk
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## Interpretation
The compatibility-reference surface is shrinking. The six tests listed above now point at canonical surfaces, while the legacy shells remain only as evidence and compatibility artifacts.

