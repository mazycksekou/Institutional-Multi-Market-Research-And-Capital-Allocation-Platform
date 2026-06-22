# Odds Compatibility Test Redirection After 10K8ZGK

## Executive Summary
`10K8ZGK` does not delete legacy odds shells. It adds a focused proof test that validates the canonical odds connector boundary first and then checks the remaining legacy shells only as compatibility evidence.

## Current HEAD
`88db1f3d6ab4cc7d0c8cd606062b165e702b6cf0`

## Purpose
Document how the delete-readiness proof test is structured so that future test redirection can happen without relying on the legacy odds shells as the primary validation surface.

## Scope
This phase test focuses on:
- canonical `src.connectors.odds_data` imports
- disabled live-client behavior
- import-time credential safety
- legacy shell importability
- current runtime blocker visibility

## Non-Goals
- No files deleted
- No files moved
- No source migration
- No live API calls
- No credential reads at import time
- No connector activation

## Big-Picture Architecture
- `src.connectors.odds_data` is the canonical connector boundary
- `src.providers` owns provider normalization and routing
- Legacy odds modules remain compatibility shells until the remaining runtime and test blockers are retired

## Test Redirection Summary
- The new proof test validates the canonical connector package directly
- The new proof test checks the legacy shells for disabled importability and disabled-method behavior only
- The historical phase tests remain in place as evidence for the remaining blockers

## Canonical Test Surface
- `src.connectors.odds_data`
- `src.connectors.errors.ConnectorDisabledError`
- `src.connectors.odds_data.build_odds_data_disabled_live_client()`

## Legacy Test Evidence Kept
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`

## Import Safety Contract
- No import-time credential access
- No live network imports
- No live calls
- No re-enabled live methods

## Compatibility Policy
- Legacy modules remain importable until the final deletion proof is clean
- Disabled behavior remains the contract for now

## No-Deletion Guarantee
- This phase does not delete legacy odds modules
- This phase does not remove proof-test coverage

## Next Recommended Phase
- Redirect any remaining safe test references to canonical connector surfaces where possible
- Retire runtime blocker references in a later proof phase
