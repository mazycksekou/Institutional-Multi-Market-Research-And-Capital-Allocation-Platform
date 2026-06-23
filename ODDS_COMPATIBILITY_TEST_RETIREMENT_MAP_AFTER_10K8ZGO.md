# Odds Compatibility Test Retirement Map After 10K8ZGO

## Retired Compatibility Tests
| Test file | Before retirement | After retirement | Status |
| --- | --- | --- | --- |
| `tests/test_phase10k8zgj_odds_legacy_live_method_retirement.py` | explicit legacy-shell compatibility proof | canonical bridge/provider regression test | retired |
| `tests/test_phase10k8zgk_odds_compatibility_shell_delete_readiness.py` | explicit legacy-shell delete-readiness proof | canonical bridge/provider regression test | retired |

## Canonical Replacements
- `src.services.odds_runtime_bridge`
- `src.connectors.odds_data`
- `src.providers.sportsbooks`

## Remaining References
Legacy shell references that remain are historical evidence only and do not represent active test dependencies.

## Delete-Readiness Summary
- No active compatibility-proof test requires legacy odds shell imports.
- The legacy shells are delete-ready now.
- Behavior unchanged.

## Next Recommended Phase
Keep the final proof artifacts in place and delete the legacy odds shells in a later batch if that is the desired direction.
