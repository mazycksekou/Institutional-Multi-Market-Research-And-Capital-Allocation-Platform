# Runtime Bridge Redirection Map After 10K8ZG4

## Runtime Bridge Targets
| Old import path | New import path | Status | Notes |
| --- | --- | --- | --- |
| `betting_providers.provider_router.ProviderRouter` in `main.py` | `src.providers.provider_router.ProviderRouter` | redirected | Behavior preserved via canonical bridge |
| `betting_providers.provider_router.ProviderRouter` in `src/api/model_card_service.py` | `src.providers.provider_router.ProviderRouter` | redirected | Behavior preserved via canonical bridge |
| `providers.odds_provider_router.enrich_ticket` patch sites | `screenshot_intake.enrich_ticket` where possible | partially redirected | Compatibility hook remains for legacy tests |

## Canonical Bridge
- `src.providers.provider_router.ProviderRouter` is the runtime bridge entrypoint.
- The bridge keeps consumer imports on `src.providers` while preserving the legacy router behavior.

## Legacy Modules Still Present
- `betting_providers.provider_router`
- `providers.odds_provider_router`

## Required Statement
Runtime bridge imports are redirected in this phase, but legacy modules are not deleted. This phase produces deletion proof only.
