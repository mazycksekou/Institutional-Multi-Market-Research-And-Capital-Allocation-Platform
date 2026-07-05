# Provider Runtime Migration Map After 10K8ZFV

| Current path | Current responsibility | New canonical destination | Status | Notes |
| --- | --- | --- | --- | --- |
| `providers/kalshi_provider.py` | Live Kalshi fetch plus local prediction-market normalization | `src/providers/prediction_markets/adapters.py` | partial | Read-only normalization now delegates to canonical category logic; live fetch remains legacy |
| `betting_providers/normalization.py` | Sportsbook and prediction-market payload normalization | `src/providers/prediction_markets/adapters.py` and `src/providers/sportsbooks/adapters.py` | migrated-by-delegation | Pure translation now routes through canonical adapters |
| `src/providers/prediction_markets/models.py` | Prediction-market quote/event models | `src/providers/prediction_markets/` | new canonical | Local-only model surface |
| `src/providers/prediction_markets/adapters.py` | Prediction-market read-only adapter layer | `src/providers/prediction_markets/` | new canonical | Import-safe and local-only |
| `src/providers/sportsbooks/models.py` | Sportsbook event/quote models | `src/providers/sportsbooks/` | new canonical | Local-only model surface |
| `src/providers/sportsbooks/adapters.py` | Sportsbook read-only adapter layer | `src/providers/sportsbooks/` | new canonical | Import-safe and local-only |
| `src/providers/zero_dte_stocks/models.py` | 0DTE/stock quote model | `src/providers/zero_dte_stocks/` | new canonical | Scaffold for future runtime work |
| `src/providers/zero_dte_stocks/adapters.py` | 0DTE/stock read-only adapter layer | `src/providers/zero_dte_stocks/` | new canonical | Scaffold for future runtime work |
| `betting_providers/kalshi_api.py` | Live Kalshi client | deferred | deferred | Keep legacy live client intact for now |
| `betting_providers/sharp_api.py` | Live sportsbook client | deferred | deferred | Keep legacy live client intact for now |
| `betting_providers/the_odds_api.py` | Live sportsbook client | deferred | deferred | Keep legacy live client intact for now |
| `providers/sharp_provider.py` | Live Sharp enrichment client | deferred | deferred | Keep legacy live client intact for now |
| `providers/odds_provider_router.py` | Legacy enrichment wrapper | deferred | deferred | Compatibility surface only |
| `src/services/enrichment_service.py` | Screenshot/ticket enrichment orchestration | deferred | deferred | Depends on legacy provider clients today |

## Decision
Read-only adapter logic is now category-owned. Live client behavior remains deferred until the next batch.

