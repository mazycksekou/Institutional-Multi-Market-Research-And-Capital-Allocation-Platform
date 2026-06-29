# src.automation_scheduler_legacy Caller Map After 10K8ZMP

## Observed callers
- `src/automation_scheduler_legacy/__init__.py` imports many bridge modules directly.
- Canonical `src.*` modules no longer depend on the deleted top-level scheduler package.
- Historical phase-doc references still mention the legacy bridge.

## Interpretation
- The bridge package is intentionally self-contained.
- The current checkpoint should preserve it until a later decommission phase.
