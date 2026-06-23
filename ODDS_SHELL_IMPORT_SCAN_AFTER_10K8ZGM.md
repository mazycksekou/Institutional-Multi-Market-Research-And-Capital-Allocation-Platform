# Odds Shell Import Scan After 10K8ZGM

## Import Scan Summary
The sportsbook historical tests now reference canonical bridge and connector surfaces rather than the legacy odds shell modules for their main behavior assertions.

### Before Redirection
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`
- `automation_scheduler.sharp_sportsbook_adapter`
- `automation_scheduler.sportsbook_odds_provider`

### After Redirection
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`
- `src.providers.registry`

## Files Scanned
- `tests/test_sharp_sportsbook_adapter.py`
- `tests/test_sportsbook_odds_provider.py`
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py`

## Remaining Legacy References
The proof-history tests now treat the old legacy odds shell references as historical evidence only; they are no longer retention requirements.

## No-Deletion Confirmation
No files were deleted in this phase.
No live behavior was enabled.
No credentials were read at import time.

## Next Checkpoint
The next checkpoint is to re-evaluate the odds shell delete-readiness proof after the historical test redirection has been absorbed.
