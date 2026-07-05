# Prediction Market Legacy Compatibility After 10K8ZGG

## Compatibility Policy
Legacy prediction-market modules remain importable:
- `kalshi_client.py`
- `providers/kalshi_provider.py`
- `betting_providers/kalshi_api.py`
- `automation_scheduler/kalshi_readonly_adapter.py`
- `automation_scheduler/kalshi_market_provider.py`

## What Remains
- Legacy modules continue to exist for compatibility and proof.
- The new connector-owned surfaces are disabled and canonical.
- No legacy module was deleted in this phase.

## What Did Not Change
- No live API calls
- No credential reads at import time in the new connector-owned modules
- No request signing execution
- No route rewrites
- No dashboard rewrite
- No main.py rewrite

## Deletion Notes
Legacy modules are still blocked from deletion until import redirection, compatibility proof, and connector ownership proof are complete.

## Required Statement
Prediction-market live-client migration is connector-owned but disabled in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.
