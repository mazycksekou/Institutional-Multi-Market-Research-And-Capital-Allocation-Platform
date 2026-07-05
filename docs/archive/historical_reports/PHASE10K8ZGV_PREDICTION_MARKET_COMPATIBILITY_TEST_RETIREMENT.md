# PHASE 10K8ZGV Prediction-Market Compatibility Test Retirement

## Executive Summary
This phase retires the remaining prediction-market compatibility-oriented tests so canonical ownership is validated through:

- `src.services.prediction_market_runtime_bridge`
- `src.connectors.prediction_market_data`
- `src.providers.prediction_markets`

The goal is to stop treating legacy prediction-market shell modules as the primary runtime owner in test coverage.

The legacy shells remain on disk. No runtime files are deleted, no prediction-market shells are deleted, and no live behavior is enabled.

Legacy shell modules remain on disk as historical evidence while the compatibility-oriented tests are retired.
legacy shell modules remain on disk until the final delete-readiness proof phase is complete.

> Prediction-market compatibility-test retirement is canonical-ownership driven in this phase. This phase does not authorize live API calls, credential reads at import time, request signing, scraping, broker execution, AI/LLM calls, route rewrites, or deletion of legacy modules.

## Current HEAD
`edffa0970fe2d451139f0bdb69d2e36f673e6d7c`

## Purpose
Retire or redirect the remaining compatibility-oriented prediction-market tests so the bridge, connector, and provider layers are the source of truth.

## Scope
Target tests:

- `tests/test_kalshi_readonly_adapter.py`
- `tests/test_kalshi_readonly_readiness_contract.py`
- `tests/test_calibration_collector.py`
- `tests/test_scheduler_runner.py`
- `tests/test_kalshi_market_provider.py`
- `tests/test_screenshot_analysis.py`

## Non-Goals
- No deletion of runtime files
- No deletion of prediction-market shell files
- No source moves
- No live network behavior
- No import-time credential reads
- No connector disabled-behavior changes
- No AI/LLM integration
- No broker execution
- No dashboard rewrite
- No main.py rewrite

## Big-Picture Architecture
The canonical prediction-market path remains:

`src.services.prediction_market_runtime_bridge`
-> `src.connectors.prediction_market_data`
-> `src.providers.prediction_markets`

The updated tests now assert that path directly instead of treating the legacy shell layer as the primary runtime owner.

## Tests Redirected
- `tests/test_kalshi_readonly_adapter.py` now validates the canonical bridge, connector readiness, disabled client behavior, and provider normalization.
- `tests/test_kalshi_readonly_readiness_contract.py` now patches the canonical bridge adapter, not the legacy shell module.
- `tests/test_calibration_collector.py` now imports the bridge adapter.
- `tests/test_scheduler_runner.py` now patches the bridge adapter at its canonical module path.
- `tests/test_kalshi_market_provider.py` now validates canonical bridge snapshot helpers and canonical provider registry entries.
- `tests/test_screenshot_analysis.py` now validates canonical provider normalization and canonical service-layer enrichment hooks.

## Remaining Blockers
The six active compatibility-oriented tests are no longer preserving legacy shell ownership.

What remains after this phase is historical evidence and compatibility documentation from earlier phases. Those references are not deleted here, but they are no longer the primary runtime owner in the six target tests.

## Delete-Readiness Decision
The legacy prediction-market shells are closer to deletion, but deletion is still deferred in this phase.

The remaining blockers are historical evidence references and proof-history documentation, which will be rechecked in a later delete-readiness phase.

## Why No Deletion Occurred
This phase only retires or redirects compatibility-oriented tests. Legacy shell modules remain on disk to preserve import compatibility and evidence until the final delete-readiness proof is complete.

## Next Recommended Phase
Proceed to the next prediction-market delete-readiness proof phase after verifying the updated tests and the historical evidence surface.
