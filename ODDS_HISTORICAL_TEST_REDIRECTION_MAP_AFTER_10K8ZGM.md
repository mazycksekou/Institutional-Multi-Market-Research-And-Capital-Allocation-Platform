# Odds Historical Test Redirection Map After 10K8ZGM

## Redirected Tests
| Test file | Former dependency | Canonical dependency | Status | Notes |
| --- | --- | --- | --- | --- |
| `tests/test_sharp_sportsbook_adapter.py` | legacy sportsbook shell modules | `src.services.odds_runtime_bridge`, `src.providers.sportsbooks` | redirected | adapter behavior now validates the canonical bridge and provider helpers |
| `tests/test_sportsbook_odds_provider.py` | legacy sportsbook shell modules | `src.services.odds_runtime_bridge`, `src.connectors.odds_data`, `src.providers.registry` | redirected | provider snapshot and scheduler assertions now use canonical surfaces |

## Import Scan Before Redirection
Historical sportsbook tests previously imported:
- `automation_scheduler.sharp_sportsbook_adapter`
- `automation_scheduler.sportsbook_odds_provider`

## Import Scan After Redirection
The updated historical tests now depend on:
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`
- `src.providers.registry`

## Remaining References
The deletion-proof phase files still mention the legacy shell names because they are the proof trail:
- `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py`
- `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py`
- `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py`
- `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py`

## Delete-Readiness Summary
- Runtime consumer redirection is complete
- Historical test redirection is complete
- Legacy shell deletion remains blocked by proof-history files

## Why No Deletion Occurred
This phase only redirects the historical tests.
The legacy odds shells remain on disk until compatibility-proof cleanup is finished and the local gate stays green.

## Next Recommended Deletion Phase
Re-run the odds shell delete-readiness proof with the redirected historical tests, then determine whether any of the legacy odds shells are finally eligible for removal.
