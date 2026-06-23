# Phase 10K8ZGZ — Post‑Provider/Connector Cleanup Freeze

## Status

Complete.  
This document freezes the architecture after the deletion of 7 odds legacy shells (Phase 10K8ZGP) and 5 prediction‑market legacy shells (Phase 10K8ZGY).  

## Deleted Odds Shells

| File | Path |
|------|------|
| sharp_client.py | `sharp_client.py` |
| sharp_provider.py | `providers/sharp_provider.py` |
| sharp_api.py | `betting_providers/sharp_api.py` |
| the_odds_api.py | `betting_providers/the_odds_api.py` |
| sportsgameodds.py | `betting_providers/sportsgameodds.py` |
| sharp_sportsbook_adapter.py | `automation_scheduler/sharp_sportsbook_adapter.py` |
| sportsbook_odds_provider.py | `automation_scheduler/sportsbook_odds_provider.py` |

## Deleted Prediction‑Market Shells

| File | Path |
|------|------|
| kalshi_client.py | `kalshi_client.py` |
| kalshi_provider.py | `providers/kalshi_provider.py` |
| kalshi_api.py | `betting_providers/kalshi_api.py` |
| kalshi_readonly_adapter.py | `automation_scheduler/kalshi_readonly_adapter.py` |
| kalshi_market_provider.py | `automation_scheduler/kalshi_market_provider.py` |

## Canonical Flows

Odds  
`src.services.odds_runtime_bridge` → `src.connectors.odds_data` → `src.providers.sportsbooks` (disabled, read‑only)

Prediction Markets  
`src.services.prediction_market_runtime_bridge` → `src.connectors.prediction_market_data` → `src.providers.prediction_markets` (disabled, read‑only)

Market Data / 0DTE Stocks  
`src.connectors.market_data` → `src.providers.zero_dte_stocks` (disabled, read‑only)

## Verification Points

- [ ] 7 odds shells no longer exist on disk.
- [ ] 5 prediction‑market shells no longer exist on disk.
- [ ] No runtime `.py` file imports a deleted shell.
- [ ] `main.py` is **not** a deletion candidate.
- [ ] `streamlit_app.py` is **not** a deletion candidate.
- [ ] `quant_engine.py`, `risk_engine.py`, `market_pricing.py`, `model_probability.py`, `bet_decision_engine.py`, `screenshot_intake.py` are **not** deletion candidates.
- [ ] `automation_scheduler/` remains a **decommission target**.

## Next Phase

Stage 2 – Core Engine Extraction Audit (Phase 10K8ZH0).
