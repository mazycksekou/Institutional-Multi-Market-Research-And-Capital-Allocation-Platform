# Automation Scheduler Active Test Scan After 10K8ZMH

Active test import statements targeting the relocated legacy scheduler namespace:
- Count: `105`
- Unique files: `76`

Top test blocker files:
- `tests/test_nfl_coaching_adapters.py` -> `5`
- `tests/test_nfl_open_data_backfill.py` -> `4`
- `tests/test_basketball_player_impact.py` -> `3`
- `tests/test_data_intelligence_stack.py` -> `3`
- `tests/test_market_state_manifold.py` -> `3`
- `tests/test_strategy_framework.py` -> `3`
- `tests/test_football_impact_intelligence.py` -> `2`
- `tests/test_kelly_staking.py` -> `2`
- `tests/test_nfl_coaching_feature_builders.py` -> `2`
- `tests/test_phase10k5_core_arbitrage_engine.py` -> `2`
- `tests/test_phase10k8q_dedicated_0dte_validation_readiness_payload.py` -> `2`
- `tests/test_phase10k8r_dedicated_0dte_validation_readiness_ui.py` -> `2`
- `tests/test_phase10k8t_dedicated_0dte_evaluation_readiness_payload.py` -> `2`
- `tests/test_phase10k8u_dedicated_0dte_evaluation_ui.py` -> `2`
- `tests/test_phase10k8x_controlled_0dte_paper_run_smoke_review.py` -> `2`

Historical proof-only string references remain in two tests and are not counted as imports:
- `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py`
- `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`

Result:
- Top-level `automation_scheduler` imports are at zero in tests.
- The remaining test blockers target `src.automation_scheduler_legacy`.
