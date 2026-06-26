# Automation Scheduler Active Test Scan After 10K8ZMH

Active test import statements:
- Count: `524`
- Unique files: `198`

Top test blocker files:
- `tests/test_streamlit_dashboard_data.py` -> `42`
- `tests/test_baseball_impact_intelligence.py` -> `17`
- `tests/test_golf_impact_intelligence.py` -> `16`
- `tests/test_hockey_impact_intelligence.py` -> `16`
- `tests/test_soccer_impact_intelligence.py` -> `16`
- `tests/test_combat_impact_intelligence.py` -> `15`
- `tests/test_tennis_impact_intelligence.py` -> `15`
- `tests/test_football_impact_intelligence.py` -> `11`
- `tests/test_advanced_red_team.py` -> `10`
- `tests/test_phase10k5_core_arbitrage_engine.py` -> `10`
- `tests/test_basketball_player_impact.py` -> `8`
- `tests/test_extreme_randomness_diagnostics.py` -> `8`
- `tests/test_historical_line_movement.py` -> `8`
- `tests/test_market_state_manifold.py` -> `8`
- `tests/test_security_framework.py` -> `8`

Historical proof-only string references remain in two tests and are not counted as imports:
- `tests/test_phase10k8zgz_post_provider_connector_cleanup_freeze.py`
- `tests/test_phase10k8zgy_prediction_market_shell_deletion.py`

Result:
- The package is still blocked by active test imports, not runtime code.
