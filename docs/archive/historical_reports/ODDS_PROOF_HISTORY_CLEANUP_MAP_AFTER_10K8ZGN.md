# Odds Proof-History Cleanup Map After 10K8ZGN

| File | Before Cleanup | After Cleanup | Status |
| --- | --- | --- | --- |
| `tests/test_phase10k8zgi_odds_runtime_consumer_redirection.py` | legacy-shell redirection trail | canonical bridge/connector redirection only | cleaned |
| `tests/test_phase10k8zgl_odds_runtime_consumer_redirection_batch_2.py` | legacy-shell redirection trail | canonical bridge/connector redirection only | cleaned |
| `tests/test_phase10k8zgm_odds_historical_test_redirection.py` | historical test trail retained shell importability | canonical bridge/connector redirection only | cleaned |
| `PHASE10K8ZGM_ODDS_HISTORICAL_TEST_REDIRECTION.md` | shell references treated as blockers | shell references are historical evidence only | cleaned |
| `ODDS_HISTORICAL_TEST_REDIRECTION_MAP_AFTER_10K8ZGM.md` | shell references treated as blockers | shell references are historical evidence only | cleaned |
| `ODDS_SHELL_IMPORT_SCAN_AFTER_10K8ZGM.md` | shell references treated as retention requirements | shell references are historical evidence only | cleaned |
| `ODDS_SHELL_DELETE_READINESS_AFTER_10K8ZGM.md` | proof-history files blocked deletion | only explicit compatibility-proof tests block deletion | updated |

## Reclassification Summary
- Historical redirection files no longer keep legacy shells alive by themselves.
- The explicit compatibility-proof tests are now the only intentional blockers.

## Next Recommended Phase
Re-evaluate whether the explicit compatibility-proof tests can be redirected or retired.
