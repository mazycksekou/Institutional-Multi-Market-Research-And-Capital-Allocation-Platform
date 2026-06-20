# Connector Boundary Map After 10K8ZFX

## Executive Summary
This map captures the intended connector landing zones and the legacy modules that still mix live access with provider or scheduler behavior.

## Boundary Map

| Future connector area | What belongs there | Current examples | Status |
| --- | --- | --- | --- |
| `src/connectors/market_data` | raw market feeds, calibration pulls, public market datasets | `automation_scheduler/calibration_collector.py`, `automation_scheduler/ncaaf_collegefootballdata_adapter.py` | deferred |
| `src/connectors/odds_data` | sportsbook odds feeds and odds vendor clients | `providers/sharp_provider.py`, `betting_providers/sharp_api.py`, `betting_providers/the_odds_api.py`, `betting_providers/sportsgameodds.py` | deferred |
| `src/connectors/prediction_market_data` | raw prediction-market access | `providers/kalshi_provider.py`, `betting_providers/kalshi_api.py`, `automation_scheduler/kalshi_readonly_adapter.py` | deferred |
| `src/connectors/web_scraping` | scrape/intake boundaries only | `screenshot_intake.py` | deferred |
| `src/connectors/feeds` | feed-style push/poll contracts | feed-oriented scheduler utilities and adapters | scaffold-ready |

## What Must Not Cross the Boundary
- Provider packages must not own live fetch behavior.
- Connector scaffolds must not call external APIs.
- Connector scaffolds must not read credentials.
- Connector scaffolds must not depend on `automation_scheduler`, `providers`, or `betting_providers`.

## Readiness Summary
- Contracts, models, registry, errors, and policy scaffolds are ready.
- Live clients remain deferred.
- Scrapers remain deferred.
- Websocket/feed implementations remain deferred.

