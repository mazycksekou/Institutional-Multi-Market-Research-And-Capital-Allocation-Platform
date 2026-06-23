# Prediction-Market Compatibility Test Retirement Map After 10K8ZGV

| Test file | Previous ownership assumption | Canonical surface used now | Status |
| --- | --- | --- | --- |
| `tests/test_kalshi_readonly_adapter.py` | legacy Kalshi shell adapter | `src.services.prediction_market_runtime_bridge`, `src.connectors.prediction_market_data`, `src.providers.prediction_markets` | redirected |
| `tests/test_kalshi_readonly_readiness_contract.py` | legacy Kalshi shell adapter | `src.services.prediction_market_runtime_bridge` | redirected |
| `tests/test_calibration_collector.py` | legacy Kalshi shell adapter | `src.services.prediction_market_runtime_bridge` | redirected |
| `tests/test_scheduler_runner.py` | legacy scheduler patch target | `src.services.prediction_market_runtime_bridge`, `src.services.odds_runtime_bridge` | redirected |
| `tests/test_kalshi_market_provider.py` | legacy Kalshi market-provider shell | `src.services.prediction_market_runtime_bridge`, `src.providers.prediction_markets` | redirected |
| `tests/test_screenshot_analysis.py` | legacy `providers.kalshi_provider` provider shell | `src.providers.prediction_markets`, `screenshot_intake` service boundary | redirected |

## Historical Evidence Retained
Earlier proof files from `10K8ZGR` through `10K8ZGU` remain as historical evidence. They are no longer the primary runtime owner in the six blocker tests above.

