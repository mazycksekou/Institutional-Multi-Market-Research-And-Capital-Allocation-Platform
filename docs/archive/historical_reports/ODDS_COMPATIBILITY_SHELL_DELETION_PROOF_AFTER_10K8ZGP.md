# Odds Compatibility Shell Deletion Proof After 10K8ZGP

## Delete-Readiness Matrix
| Target | Proof source | Deleted | Notes |
| --- | --- | --- | --- |
| `sharp_client.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `providers/sharp_provider.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `betting_providers/sharp_api.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `betting_providers/the_odds_api.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `betting_providers/sportsgameodds.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `automation_scheduler/sharp_sportsbook_adapter.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |
| `automation_scheduler/sportsbook_odds_provider.py` | `10K8ZGO` final proof trail | yes | canonical odds flow retained |

## Import Scan Before Deletion
The 10K8ZGO proof trail showed the legacy odds shells were delete-ready and no longer required by active compatibility-proof tests.

## Import Scan After Deletion
The active Python runtime and test files no longer import the deleted odds shells.

## Tests Run
- `python -m py_compile tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py`
- `pytest tests/test_phase10k8zgp_odds_compatibility_shell_deletion.py -q`

## Behavior Preserved
- Canonical odds flow remains:
  `src.services.odds_runtime_bridge -> src.connectors.odds_data -> src.providers.sportsbooks`
- Disabled odds connector behavior remains disabled.
- No live odds API calls are enabled.
- No import-time credential reads are introduced.

## Next Recommended Phase
If desired, continue with cleanup of the remaining historical odds evidence docs, but no further odds-shell deletion is required for this batch.

## Required Statement
Only the seven proof-backed legacy odds compatibility shells are deleted in this phase. Runtime modules, dashboard files, entrypoints, connector scaffolds, AI scaffolds, brokerage scaffolds, and prediction-market legacy modules are preserved.
