# PREDICTION_MARKET_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGU

| Historical test/reference | New classification | Canonical surface used |
| --- | --- | --- |
| `tests/test_phase10k8zgs_prediction_market_compatibility_shell_delete_readiness.py` | reclassified historical evidence | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgt_prediction_market_runtime_scheduler_redirection.py` | redirected runtime proof | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgr_prediction_market_legacy_live_method_retirement.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` / `src.connectors.prediction_market_data` / `src.providers.prediction_markets` |
| `tests/test_phase10k8zgq_prediction_market_runtime_consumer_redirection.py` | historical evidence only | `src.services.prediction_market_runtime_bridge` |
| `tests/test_phase10k8zgg_prediction_market_live_client_connector_migration.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_phase10k8zfy_prediction_market_connector_batch_1.py` | historical evidence only | `src.connectors.prediction_market_data` |
| `tests/test_kalshi_readonly_adapter.py` | compatibility evidence | legacy adapter shell, retained until separate rewrite |
| `tests/test_kalshi_readonly_readiness_contract.py` | compatibility evidence | legacy readiness shell, retained until separate rewrite |
| `tests/test_calibration_collector.py` | runtime-adjacent evidence | bridge-backed adapter import path |
| `tests/test_scheduler_runner.py` | runtime proof | bridge-backed adapter import path |
| `tests/test_kalshi_market_provider.py` | compatibility evidence | bridge-backed snapshot helper path |
| `tests/test_screenshot_analysis.py` | compatibility evidence | legacy provider shell import path |

## Result
The historical evidence set has been reclassified so it no longer treats the legacy prediction-market shells as active runtime owners.
