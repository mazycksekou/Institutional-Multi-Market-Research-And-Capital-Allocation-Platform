# Odds Data Legacy Compatibility After 10K8ZGH

## Compatibility Policy
Legacy odds/sportsbook modules remain importable:
- `sharp_client.py`
- `providers/sharp_provider.py`
- `betting_providers/sharp_api.py`
- `betting_providers/the_odds_api.py`
- `betting_providers/sportsgameodds.py`
- `automation_scheduler/sharp_sportsbook_adapter.py`
- `automation_scheduler/sportsbook_odds_provider.py`

## What Remains
- Legacy modules continue to exist for compatibility and proof.
- The new connector-owned surfaces are disabled and canonical.
- No legacy module was deleted in this phase.

## What Did Not Change
- No live API calls
- No credential reads at import time in the new connector-owned modules
- No request signing execution
- No bet execution
- No route rewrites
- No dashboard rewrite
- No main.py rewrite

## Deletion Notes
Legacy modules are still blocked from deletion until import redirection, compatibility proof, and connector ownership proof are complete.

## Required Statement
Odds-data live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, scraping, broker execution, bet execution, AI/LLM calls, route rewrites, or deletion of legacy modules.
