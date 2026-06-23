# PREDICTION_MARKET_RUNTIME_DELETE_READINESS_AFTER_10K8ZGT

## Delete-Readiness Decision
The runtime scheduler redirection is complete, but the legacy prediction-market shells are still not delete-ready overall.

| File | Decision | Reason |
| --- | --- | --- |
| `kalshi_client.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it and evidence docs still reference it. |
| `providers/kalshi_provider.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it and patch compatibility symbols. |
| `betting_providers/kalshi_api.py` | `test-blocked`, `compatibility-blocked` | Historical tests still import it. |
| `automation_scheduler/kalshi_readonly_adapter.py` | `compatibility-blocked`, `test-blocked` | Runtime scheduler redirection removed direct runtime dependency, but compatibility tests still import it. |
| `automation_scheduler/kalshi_market_provider.py` | `compatibility-blocked`, `test-blocked` | Runtime scheduler redirection removed direct runtime dependency, but compatibility tests still import it. |

## What Changed
The runtime blockers were cleared because the scheduler path now imports the canonical bridge surface.

## Why Deletion Did Not Occur
Deletion is still blocked by historical compatibility and proof references.

## Next Recommended Phase
Redirect or retire the remaining compatibility/test references and then re-run delete-readiness proof for the five legacy prediction-market shells.
