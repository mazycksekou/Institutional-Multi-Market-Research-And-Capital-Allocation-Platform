# Root-Level Engine Ownership Map After 10K8ZGE

## Summary
The root-level runtime utilities are not automatic deletion candidates. Several contain reusable math or service behavior that should be transported into the correct `src` domain before any future cleanup.

## Ownership Map

| File | Current role | Tag | Recommended destination | Notes |
|---|---|---|---|---|
| `main.py` | FastAPI entrypoint and orchestration shell | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays as thin shell | Not an automatic deletion candidate. |
| `streamlit_app.py` | Streamlit dashboard shell | `KEEP_ENTRYPOINT_OR_DASHBOARD` | stays as thin shell | Not an automatic deletion candidate. |
| `quant_engine.py` | Odds, EV, Kelly, scoring, and classification math | `MIGRATE_TO_SRC_CORE` | `src/core` | Reusable quant logic. |
| `risk_engine.py` | Bankroll, exposure, ruin, and stake sizing math | `MIGRATE_TO_SRC_CORE` | `src/core` | Reusable risk logic. |
| `market_pricing.py` | Cross-book pricing and consensus helpers | `MIGRATE_TO_SRC_CORE` | `src/core` | Shared pricing math. |
| `model_probability.py` | Probability blending and confidence layer | `MIGRATE_TO_SRC_CORE` | `src/core` | Later evaluation/AI hooks only after foundations exist. |
| `bet_log.py` | JSONL bet log persistence | `MIGRATE_TO_SRC_SERVICES` | `src/services` | App bookkeeping and persistence. |
| `bet_decision_engine.py` | Betting decision orchestration | `MIGRATE_TO_SRC_SERVICES` | `src/services` | Decision glue, not execution. |
| `screenshot_intake.py` | Screenshot/file intake workflow | `MIGRATE_TO_SRC_SERVICES` | `src/services` | Intake orchestration. |
| `kalshi_client.py` | Live prediction-market HTTP client | `MIGRATE_TO_SRC_CONNECTORS` | `src/connectors/prediction_market_data` | Live external access boundary. |
| `sharp_client.py` | Live sportsbook HTTP client | `MIGRATE_TO_SRC_CONNECTORS` | `src/connectors/odds_data` | Live external access boundary. |

## Notes
- `main.py`, `streamlit_app.py`, `quant_engine.py`, and `risk_engine.py` are not automatic deletion candidates.
- The math/risk foundation should be integrated only after migration/deletion cleanup is complete.

