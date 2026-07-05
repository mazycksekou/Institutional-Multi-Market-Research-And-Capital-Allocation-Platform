# Prediction Market Legacy Compatibility After 10K8ZFY

## Executive Summary
Legacy prediction-market modules remain in place and continue to resolve while the inert connector wrapper is introduced.

## Compatibility Status
- legacy modules remain in place while the inert connector wrapper is introduced.
- `providers/kalshi_provider.py` remains unchanged.
- `betting_providers/kalshi_api.py` remains unchanged.
- `automation_scheduler/kalshi_readonly_adapter.py` remains unchanged.
- `automation_scheduler/kalshi_market_provider.py` remains unchanged.
- `kalshi_client.py` remains unchanged.

## Compatibility Policy
- Legacy modules may continue to exist until dependency proof is complete.
- The canonical connector path is vendor-neutral.
- No deletion occurred in this phase.
