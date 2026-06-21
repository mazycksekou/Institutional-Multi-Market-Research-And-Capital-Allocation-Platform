# Legacy Apple Transport Map After 10K8ZGE

## Purpose
This map lists the useful legacy runtime owners that should be transported into the correct `src` domain instead of being deleted.

## Transport Table

| Current file | Current ownership | Tag | Future destination | Notes |
|---|---|---|---|---|
| `main.py` | Entrypoint/orchestration shell | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays thin | Not an automatic deletion candidate. |
| `streamlit_app.py` | Dashboard shell | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays thin | Not an automatic deletion candidate. |
| `quant_engine.py` | Odds/EV/Kelly/scoring math | `MIGRATE_TO_SRC_CORE` | `src/core` | Pure math should move first. |
| `risk_engine.py` | Bankroll, exposure, ruin math | `MIGRATE_TO_SRC_CORE` | `src/core` | Useful risk math, not delete-now. |
| `market_pricing.py` | Market pricing and consensus math | `MIGRATE_TO_SRC_CORE` | `src/core` | Reusable pricing logic. |
| `model_probability.py` | Probability blending and confidence | `MIGRATE_TO_SRC_CORE` | `src/core` | Later evaluation/AI hooks only after foundations exist. |
| `bet_log.py` | Bet logging and result persistence | `MIGRATE_TO_SRC_SERVICES` | `src/services` | App bookkeeping, not core math. |
| `bet_decision_engine.py` | Line evaluation / recommendation orchestration | `MIGRATE_TO_SRC_SERVICES` | `src/services` | Decision glue, not execution. |
| `screenshot_intake.py` | Screenshot intake workflow | `MIGRATE_TO_SRC_SERVICES` | `src/services` | Intake/orchestration logic. |
| `kalshi_client.py` | Live prediction-market HTTP client | `MIGRATE_TO_SRC_CONNECTORS` | `src/connectors/prediction_market_data` | Unsafe until connector boundary is fully isolated. |
| `sharp_client.py` | Live sportsbook HTTP client | `MIGRATE_TO_SRC_CONNECTORS` | `src/connectors/odds_data` | Unsafe until connector boundary is fully isolated. |
| `providers/kalshi_provider.py` | Mixed normalization + live fetch | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers.prediction_markets` + `src.connectors/prediction_market_data` | Split useful normalization from live access. |
| `providers/sharp_provider.py` | Mixed enrichment + live fetch | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers.sportsbooks` + `src.connectors/odds_data` | Split useful normalization from live access. |
| `betting_providers/kalshi_api.py` | Vendor client | `UNSAFE_TO_TOUCH` | `src/connectors/prediction_market_data` | Live connector behavior remains deferred. |
| `betting_providers/sharp_api.py` | Vendor client | `UNSAFE_TO_TOUCH` | `src/connectors/odds_data` | Live connector behavior remains deferred. |
| `betting_providers/the_odds_api.py` | Vendor client | `UNSAFE_TO_TOUCH` | `src/connectors/odds_data` | Live connector behavior remains deferred. |
| `betting_providers/sportsgameodds.py` | Vendor client | `UNSAFE_TO_TOUCH` | `src/connectors/odds_data` | Live connector behavior remains deferred. |
| `automation_scheduler/kalshi_readonly_adapter.py` | Read-only adapter with env/HTTP behavior | `UNSAFE_TO_TOUCH` | `src.connectors/prediction_market_data` | Read-only shape can be reused later. |
| `automation_scheduler/kalshi_market_provider.py` | Prediction-market provider wrapper | `UNSAFE_TO_TOUCH` | `src.providers.prediction_markets` + `src.connectors/prediction_market_data` | Mixed provider/connector behavior. |
| `automation_scheduler/sharp_sportsbook_adapter.py` | Sportsbook adapter wrapper | `UNSAFE_TO_TOUCH` | `src.connectors/odds_data` | Mixed provider/connector behavior. |
| `automation_scheduler/sportsbook_odds_provider.py` | Sportsbook provider wrapper | `UNSAFE_TO_TOUCH` | `src.providers.sportsbooks` + `src.connectors/odds_data` | Mixed provider/connector behavior. |
| `automation_scheduler/provider_allowlist.py` | Legacy provider policy shim | `COMPATIBILITY_SHIM_CANDIDATE` | `src.providers.policy.allowlist` | Canonical policy already exists. |
| `src/api/provider_status_routes.py` | API bridge to legacy automation state | `MIGRATE_TO_SRC_SERVICES` | thin route shell | Still bridges to runtime state. |
| `src/services/enrichment_service.py` | Enrichment orchestration | `MIGRATE_TO_SRC_SERVICES` | thin service shell | Still calls legacy provider enrichers. |

## Required Statement
Useful functionality should be transported into the correct src domain before legacy modules are deleted. Entrypoints, dashboards, quant logic, and risk logic are not automatic deletion candidates; they must be classified by ownership and dependency role.

## Notes
- `main.py`, `streamlit_app.py`, `quant_engine.py`, and `risk_engine.py` are not automatic deletion candidates.
- No deletion occurred and no migration occurred.

