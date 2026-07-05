# Prediction-Market Delete Readiness After 10K8ZGR

## Delete-Readiness Review

### `kalshi_client.py`
- Status: not yet delete-ready
- Reason: still preserved as a compatibility shell and historical import surface

### `providers/kalshi_provider.py`
- Status: not yet delete-ready
- Reason: still preserved as a compatibility shell for enrichment callers

### `betting_providers/kalshi_api.py`
- Status: not yet delete-ready
- Reason: still preserved as a compatibility shell for adapter callers

### `automation_scheduler/kalshi_readonly_adapter.py`
- Status: not yet delete-ready
- Reason: still preserved for scheduler compatibility and proof history

### `automation_scheduler/kalshi_market_provider.py`
- Status: not yet delete-ready
- Reason: still preserved as a compatibility wrapper over disabled snapshot metadata

## Why No Deletion Occurred
This phase only retires live methods. Deletion requires a later proof-backed cleanup batch.

## Next Recommended Phase
Proceed to `10K8ZGS Prediction-Market Compatibility Shell Delete-Readiness Proof`.
