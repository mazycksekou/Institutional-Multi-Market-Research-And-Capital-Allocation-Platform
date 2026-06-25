# Automation Scheduler Decommission Inventory

Canonical src.* architecture already exists. Live trading, broker/account/credential/order/deployment activation remain disabled.

live trading remains disabled
credential reads remain disabled
broker SDK imports remain disabled

Inventory summary:
- Remaining automation_scheduler files: 329
- Runtime-referenced files: 70
- Test-referenced files: 303
- Delete-ready after proof: 23

## Classification Counts

- MIGRATE_TO_SRC_MARKET_INTELLIGENCE_LATER: 128
- COMPATIBILITY_WRAPPER_ONLY: 73
- MIGRATE_TO_SRC_SERVICES: 45
- MIGRATE_TO_SRC_DATA: 23
- DELETE_READY_AFTER_PROOF: 23
- MIGRATE_TO_SRC_BROKERAGE: 14
- MIGRATE_TO_SRC_RESEARCH: 9
- MIGRATE_TO_SRC_AI: 7
- MIGRATE_TO_SRC_BACKTESTING: 7

## Required Canonical Targets

- `src.core` for math/risk/pricing/portfolio/execution primitives.
- `src.services` for orchestration.
- `src.data` for data contracts/loading/storage boundaries.
- `src.backtesting` for backtest/replay/simulation.
- `src.analytics` for summaries/reporting/governance.
- `src.research` for research metadata/experiments/lanes.
- `src.ai` for disabled AI boundary.
- `src.brokerage` for production-shaped disabled execution/brokerage.
- `src.market_intelligence` later, if needed.

## Delete-Ready After Proof

- `automation_scheduler/baseball_impact_common.py`
- `automation_scheduler/basketball_lineup_matchup_context.py`
- `automation_scheduler/basketball_market_relevance.py`
- `automation_scheduler/basketball_player_impact_common.py`
- `automation_scheduler/basketball_player_impact_red_team.py`
- `automation_scheduler/combat_impact_common.py`
- `automation_scheduler/correlation_structure_diagnostics.py`
- `automation_scheduler/cross_asset_embedding_router.py`
- `automation_scheduler/deepseek_prompt_contracts.py`
- `automation_scheduler/deepseek_response_validator.py`
- `automation_scheduler/extreme_signal_red_team.py`
- `automation_scheduler/football_impact_common.py`
- `automation_scheduler/football_impact_red_team.py`
- `automation_scheduler/football_impact_schema.py`
- `automation_scheduler/golf_impact_common.py`
- `automation_scheduler/hockey_impact_common.py`
- `automation_scheduler/manifold_review_queue.py`
- `automation_scheduler/market_state_graph.py`
- `automation_scheduler/prediction_market_manifold_mapper.py`
- `automation_scheduler/security_readiness_report.py`
- `automation_scheduler/soccer_impact_common.py`
- `automation_scheduler/strategy_readiness_report.py`
- `automation_scheduler/tennis_impact_common.py`
