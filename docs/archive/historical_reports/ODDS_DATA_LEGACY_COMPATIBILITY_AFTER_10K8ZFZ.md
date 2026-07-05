# Odds Data Legacy Compatibility After 10K8ZFZ

## Executive Summary
Legacy odds and sportsbook modules remain in place while the inert connector wrapper is introduced.

## Compatibility Status
- legacy modules remain in place while the inert connector wrapper is introduced.
- `providers/sharp_provider.py` remains unchanged.
- `betting_providers/sharp_api.py` remains unchanged.
- `betting_providers/the_odds_api.py` remains unchanged.
- `betting_providers/sportsgameodds.py` remains unchanged.
- `automation_scheduler/sharp_sportsbook_adapter.py` remains unchanged.
- `automation_scheduler/sportsbook_odds_provider.py` remains unchanged.
- `sharp_client.py` remains unchanged.
- `providers/odds_provider_router.py` remains unchanged.
- `betting_providers/provider_router.py` remains unchanged.

## Compatibility Policy
- Legacy modules may continue to exist until dependency proof is complete.
- The canonical connector path is vendor-neutral.
- No deletion occurred in this phase.
