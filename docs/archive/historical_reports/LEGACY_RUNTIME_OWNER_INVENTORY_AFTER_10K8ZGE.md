# Legacy Runtime Owner Inventory After 10K8ZGE

## Inventory Snapshot
- `automation_scheduler/`: 347 files
- `providers/`: 3 files
- `betting_providers/`: 6 files
- `src/`: 104 files
- `tests/`: 379 files
- tracked JSON/JSONL/CSV under `data/`: 0

## Inventory Table

| Legacy owner family | Representative files | Classification | Where useful functionality should move |
|---|---|---|---|
| Entrypoint / dashboard shells | `main.py`, `streamlit_app.py` | `KEEP_ENTRYPOINT_OR_DASHBOARD` | Keep thin; do not delete yet. |
| Quant / pricing / probability | `quant_engine.py`, `market_pricing.py`, `model_probability.py` | `MIGRATE_TO_SRC_CORE` | `src/core` |
| Risk / bankroll | `risk_engine.py` | `MIGRATE_TO_SRC_CORE` | `src/core` |
| Decision / logging / intake | `bet_decision_engine.py`, `bet_log.py`, `screenshot_intake.py` | `MIGRATE_TO_SRC_SERVICES` | `src/services` |
| Live data clients | `kalshi_client.py`, `sharp_client.py` | `MIGRATE_TO_SRC_CONNECTORS` / `UNSAFE_TO_TOUCH` | `src/connectors` |
| Legacy provider enrichers | `providers/kalshi_provider.py`, `providers/sharp_provider.py` | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers` + `src.connectors` split |
| Vendor client package | `betting_providers/*.py` | `UNSAFE_TO_TOUCH` | `src/connectors` after proof |
| Automation provider/live adapter family | `automation_scheduler/kalshi_readonly_adapter.py`, `automation_scheduler/kalshi_market_provider.py`, `automation_scheduler/sharp_sportsbook_adapter.py`, `automation_scheduler/sportsbook_odds_provider.py` | `UNSAFE_TO_TOUCH` | `src.providers` + `src.connectors` split |
| Automation provider policy | `automation_scheduler/provider_allowlist.py` | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers.policy.allowlist` |
| API bridge | `src/api/provider_status_routes.py` | `MIGRATE_TO_SRC_SERVICES` | thin route shell |
| Service bridge | `src/services/enrichment_service.py` | `MIGRATE_TO_SRC_SERVICES` | thin service shell |

## Remaining Legacy Owners
- `automation_scheduler` still owns orchestration, dashboard data, risk/strategy, backtest, data-source registry, and live adapter code.
- `providers` still owns legacy enrichment surfaces for sharp and prediction-market logic.
- `betting_providers` still owns vendor client code and should be treated as compatibility-only until connector migration is proven safe.
- Root-level live clients remain runtime-critical and are not delete candidates yet.
- Root-level engines/utilities are useful runtime owners and should be classified by dependency role rather than deleted automatically.

## What Is Not Automatic Deletion
- `main.py`
- `streamlit_app.py`
- `quant_engine.py`
- `risk_engine.py`

## Notes
- `automation_scheduler` remains a decommission target.
- No deletion occurred.
- No migration occurred.

