# automation_scheduler Remaining Ownership After 10K8ZGE

## Summary
`automation_scheduler` remains a decommission target, but it still owns real runtime behavior across orchestration, dashboard data, live adapters, backtest/history, and model/risk utilities. This is why the package is not yet delete-ready.

## Ownership Families

| Family | Representative modules | Current role | Future destination |
|---|---|---|---|
| Orchestration / scheduler | `scheduler_runner.py`, `collector_scheduled_runner.py`, `ops_workflow.py`, `response_compactor.py`, `scheduler_config.py` | Runtime orchestration shell | `src/services` plus thin shell only |
| Dashboard data helpers | `streamlit_dashboard_data.py`, `model_data_field_catalog.py`, `historical_data_sources.py` | Dashboard payload and readiness helpers | Keep dashboard shell thin; some helpers later to `src/services` |
| Live provider / sportsbook adapters | `kalshi_readonly_adapter.py`, `kalshi_market_provider.py`, `sharp_sportsbook_adapter.py`, `sportsbook_odds_provider.py` | Mixed provider + connector runtime owner | `src.providers` + `src.connectors` split |
| Provider policy / safety | `provider_allowlist.py`, `provider_*` policies | Compatibility and safety policy | `src.providers.policy` |
| Risk / strategy / execution gates | `risk_limit_guard.py`, `hard_gate_policy.py`, `risk_of_ruin.py`, `session_risk_rules.py`, `liquidity_risk.py`, `strategy_router.py`, `strategy_registry.py` | Decision and gatekeeping logic | `src.core` or `src.brokerage` later |
| Backtest / historical replay | `backtesting_engine.py`, `historical_odds_sqlite.py`, `historical_backtest_bridge.py`, `historical_line_movement.py` | Historical replay and research logic | `src.core` / `src.services` later |
| AI / evaluation / policy | `advanced_red_team_provider_policy.py`, `ai_provider_security.py`, `deepseek_*`, `model_recheck_runner.py` | Future AI policy / evaluation scaffolds | `src.ai` later |
| Data-source registry / contracts | `data_source_registry.py`, adapter contract modules, stock/news contract helpers | Source registry and contract scaffolding | `src.connectors` and `src.services` later |

## What Must Leave automation_scheduler First
1. Live provider adapter behavior.
2. Provider status/registry bridge behavior.
3. Any env-reading connector/client behavior.
4. Dashboard payload helpers that can be moved to service-level helpers.

## What Can Become Compatibility Only
- Policy shims that now have canonical `src.providers.policy` equivalents.
- Provider status/registry bridge helpers after import redirection.
- Any routing helper that only forwards to canonical `src` code.

## What Must Not Be Deleted Yet
- Orchestration modules still imported by `main.py`, `streamlit_app.py`, and tests.
- Live adapters that still encode env/credential and HTTP behavior.
- Dashboard data helpers used by `streamlit_app.py`.
- Backtest/history utilities still used by tests and API route bridges.

## Unsafe-To-Touch Areas
- Modules that read environment credentials at import time.
- Modules that instantiate HTTP clients or make live calls.
- Modules used by API route bridges or dashboard shells.

## Why automation_scheduler Remains a Decommission Target
It is still the place where many old baskets mix together. The long-term target remains full removal or reduction to a minimal compatibility/orchestration shell before eventual retirement.

