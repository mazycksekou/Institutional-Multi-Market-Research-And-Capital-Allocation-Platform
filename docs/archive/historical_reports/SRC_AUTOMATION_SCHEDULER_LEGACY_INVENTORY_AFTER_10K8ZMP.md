# src.automation_scheduler_legacy Inventory After 10K8ZMP

## Status
- `src/automation_scheduler_legacy/` exists.
- It is a deliberate compatibility bridge and should remain for now.

## Classification
- `TEMPORARY_COMPATIBILITY_LAYER`: yes
- `MIGRATED_CANONICAL_LOGIC`: present in the bridge package where canonical parity still depends on it
- `DUPLICATE_LOGIC`: expected while the bridge remains
- `DELETE_READY_LATER`: some submodules may become eligible after bridge decommission proof
- `ACTIVE_DEPENDENCY`: yes, the bridge is still imported by the current compatibility surface
- `UNKNOWN`: none from the current inspection
