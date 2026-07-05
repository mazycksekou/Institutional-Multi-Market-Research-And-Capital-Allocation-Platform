# DECOMMISSION_CANDIDATES_AFTER_10K8ZFM

## Executive Summary
This phase only identifies future removal or consolidation candidates. Nothing is deleted here. The safest candidates are empty scaffolds and compatibility shells; the riskiest candidates are runtime adapters and scheduler helpers that still have live import traffic.

## Current HEAD
`9402a91` (`docs: plan test suite cleanup`)

## Safe Later Deletion Candidates
These are low-risk future candidates because they are empty scaffolds or obvious placeholders, but they still require a later approval phase:
- `live_market_intelligence/` directory tree, which currently has zero files
- `models/` directory, which currently has zero Python files
- `unused/` directory, which currently has zero Python files

## Requires Dependency Migration First
These files should not be removed until canonical owners exist and wrappers/tests prove equivalence:
- `providers/*`
- `betting_providers/*`
- `automation_scheduler/provider_*`
- `automation_scheduler/kalshi_*`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/backtesting_engine.py`
- `automation_scheduler/backtest_dataset_builder.py`
- `automation_scheduler/historical_backtest_bridge.py`
- `automation_scheduler/historical_odds_sqlite.py`
- `automation_scheduler/streamlit_dashboard_data.py`

## Requires Test Rewrite First
These are oversized or brittle test surfaces that should be reworked before any consolidation:
- `tests/test_streamlit_dashboard_data.py`
- `tests/test_automation_scheduler_endpoints.py`
- `tests/test_response_compactor.py`
- the large provider and scheduler integration families that still import `automation_scheduler` broadly

## Requires Ownership Decision First
These files sit at ownership boundaries and should not be removed until the canonical architecture is fully settled:
- `automation_scheduler/__init__.py`
- `providers/__init__.py`
- `betting_providers/__init__.py`
- `api_server.py`
- `main.py`
- `streamlit_app.py`
- `src/services/enrichment_service.py`

## Compatibility Shell Candidates
These are good candidates for eventual reduction to thin wrappers:
- `api_server.py`
- `automation_scheduler/__init__.py`
- `providers/__init__.py`
- `betting_providers/__init__.py`
- `streamlit_app.py` as a shell over dashboard-data helpers

## Do-Not-Touch-Yet Candidates
These are clearly live and should be treated as protected until a later migration wave:
- `src/core/math_utils.py`
- `src/core/clv.py`
- `src/storage/archive_manifest.py`
- `src/storage/r2_archive_adapter.py`
- `scripts/daily_data_hygiene.py`
- `scripts/r2_archive_pipeline.py`
- `src/api/provider_status_routes.py`
- `src/services/enrichment_service.py`
- `automation_scheduler/streamlit_dashboard_data.py`
- `automation_scheduler/ops_workflow.py`
- `automation_scheduler/scheduler_runner.py`

## Consolidation Candidates
These are not deletion targets yet, but they are likely to consolidate around canonical owners later:
- `market_pricing.py`
- `quant_engine.py`
- `risk_engine.py`
- `bet_log.py`
- `bet_decision_engine.py`
- `model_probability.py`
- `multi_sport_model_registry.py`
- `screenshot_intake.py`
- `full_board_engine.py`
- `logbook_engine.py`

## Safety Policy
- No files are deleted in this phase.
- No files are moved in this phase.
- No source migrations happen in this phase.
- No public functions are removed in this phase.
- Compatibility and behavior preservation remain higher priority than cleanup speed.

## Summary
The best future decommission candidates are the empty scaffolds and compatibility shells. Everything else needs canonical ownership, wrapper coverage, and dependency migration first.
