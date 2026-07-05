# Provider to Connector Split Report After 10K8ZFX

## Executive Summary
Provider normalization is already isolated. The remaining work is to move live access out of provider-adjacent legacy modules and into connector ownership.

## Provider-Connector Split
- `src.providers` stays read-only and category-focused.
- `src.connectors` owns raw access, feeds, scraping, and client contracts.
- Legacy provider modules that still call networks remain deferred.

## Modules Still Pulling Toward Connectors
- `providers/kalshi_provider.py` -> `src/connectors/prediction_market_data`
- `providers/sharp_provider.py` -> `src/connectors/odds_data`
- `betting_providers/kalshi_api.py` -> `src/connectors/prediction_market_data`
- `betting_providers/sharp_api.py` -> `src/connectors/odds_data`
- `betting_providers/the_odds_api.py` -> `src/connectors/odds_data`
- `betting_providers/sportsgameodds.py` -> `src/connectors/odds_data`
- `automation_scheduler/kalshi_readonly_adapter.py` -> split between `src/connectors/prediction_market_data` and `src.providers.prediction_markets`
- `automation_scheduler/sharp_sportsbook_adapter.py` -> split between `src/connectors/odds_data` and `src.providers.sportsbooks`
- `automation_scheduler/calibration_collector.py` -> `src/connectors/market_data`
- `automation_scheduler/ncaaf_collegefootballdata_adapter.py` -> `src/connectors/market_data`
- `screenshot_intake.py` -> `src/connectors/web_scraping`

## Provider Modules That Depend on Connector Behavior Today
- `src/providers` read-only code can still be fed by legacy live clients indirectly.
- Those dependencies remain compatibility-only until connector batches land.

## Next Step
Move the pure connector contract layer first, then the first live client batch under explicit connector wrappers.

