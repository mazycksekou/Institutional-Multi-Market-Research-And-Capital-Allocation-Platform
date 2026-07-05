# Live Fetch Deferred Modules After 10K8ZFX

## Executive Summary
The following modules still contain live-access, credential, or scraper behavior and therefore remain deferred until connector boundaries are proven.

## Deferred Modules
- `providers/kalshi_provider.py`
- `providers/sharp_provider.py`
- `betting_providers/kalshi_api.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`
- `automation_scheduler/calibration_collector.py`
- `automation_scheduler/ncaaf_collegefootballdata_adapter.py`
- `screenshot_intake.py`
- `automation_scheduler/institutional_deepseek_review.py`

## Why They Remain Deferred
- They read credentials.
- They perform live network calls.
- They mix live access with normalization.
- They have not yet been replaced by explicit connector contracts.

## Future Destinations
- `src/connectors/prediction_market_data`
- `src/connectors/odds_data`
- `src/connectors/market_data`
- `src/connectors/web_scraping`
- `src/ai/evaluation` for the AI review path

