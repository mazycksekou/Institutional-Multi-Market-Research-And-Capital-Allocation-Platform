# Odds Compatibility Import Scan After 10K8ZGK

## Import Scan Summary
The canonical odds connector boundary remains import-safe through `src.connectors.odds_data`. The legacy odds compatibility shells still have remaining references, so deletion is not yet justified.

## Runtime References
- `src/services/enrichment_service.py` still imports `providers.sharp_provider`
- `automation_scheduler/scheduler_runner.py` still instantiates `SharpSportsbookAdapter`
- `automation_scheduler/__init__.py` still instantiates `SharpSportsbookAdapter`

## Test References
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgh_odds_data_live_client_connector_migration.py`
- `tests/test_phase10k8zfz_odds_data_connector_batch_2.py`
- `tests/test_screenshot_analysis.py`
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`

## Redirected Checks
- The new proof test for `10K8ZGK` validates the canonical `src.connectors.odds_data` boundary first.
- The new phase docs treat the legacy shells as compatibility evidence, not as canonical owners.
- No additional safe runtime redirection was completed because the remaining runtime and historical references are still active blockers.

## Compatibility Import State
- Legacy odds modules remain importable, but they are not delete-ready.
- `sharp_client.py` remains importable
- `providers/sharp_provider.py` remains importable
- `betting_providers/sharp_api.py` remains importable
- `betting_providers/the_odds_api.py` remains importable
- `betting_providers/sportsgameodds.py` remains importable
- `automation_scheduler/sharp_sportsbook_adapter.py` remains importable
- `automation_scheduler/sportsbook_odds_provider.py` remains importable

## Remaining Blockers
- Runtime scheduler imports
- Enrichment service import
- Historical proof-test imports

## Delete-Ready Files
- None yet

## Remaining Notes
- The import scan is proof-only and does not authorize deletion.
- The legacy odds shells remain blocked until runtime and test imports are fully redirected or explicitly retired in a later phase.
