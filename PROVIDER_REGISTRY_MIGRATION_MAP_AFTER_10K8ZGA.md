# Provider Registry Migration Map After 10K8ZGA

## Canonical Ownership
- `src.providers.registry` owns canonical registry behavior.

## Migration Map
| Legacy Path | New Canonical Path | Status | Notes |
| --- | --- | --- | --- |
| `automation_scheduler/__init__.py` | `src.providers.registry` | redirected | Registry snapshot now uses canonical ownership. |
| `automation_scheduler/scheduler_config.py` | `src.providers.registry` | redirected | Scheduler config now reads the canonical registry with legacy aliases enabled. |
| `automation_scheduler/kalshi_readonly_readiness.py` | `src.providers.registry` | redirected | Readiness contract now resolves provider state through canonical ownership. |
| `automation_scheduler/cadence_controller.py` | `src.providers.registry` | redirected | Interval lookup now comes from the canonical helper. |
| `automation_scheduler/provider_registry.py` | `src.providers.registry` | compatibility shim | Remains importable, but no longer owns runtime behavior. |

## Behavior Moved or Already Canonical
- Registry construction
- Legacy alias generation when requested
- Provider interval lookup
- Canonical provider contract snapshots

## Compatibility Still Required
- `automation_scheduler/provider_registry.py` remains on disk for import compatibility.
- Legacy provider IDs remain available when the canonical helper is requested with legacy aliases enabled.

## Remaining Runtime Blocker
- `automation_scheduler/provider_write_firewall.py`

## Delete-Readiness Note
`automation_scheduler/provider_registry.py` is delete-ready from a dependency perspective, but deletion is deferred until the next batch.
