# PHASE 10K8ZMJ - Sports Impact Test Import Redirection

This batch redirects the highest-volume sports impact tests away from `automation_scheduler` and onto canonical `src.market_intelligence` shims.

Scope:
- `tests/test_baseball_impact_intelligence.py`
- `tests/test_golf_impact_intelligence.py`
- `tests/test_hockey_impact_intelligence.py`
- `tests/test_soccer_impact_intelligence.py`
- `tests/test_combat_impact_intelligence.py`
- `tests/test_tennis_impact_intelligence.py`

Approach:
- Move sport-specific helpers to `src.market_intelligence.sports`.
- Move diagnostics compaction helpers to `src.market_intelligence.response_compactor`.
- Keep scheduler files intact for this phase.

Baseline before this batch:
- Active test imports: `482` across `197` files
- Internal scheduler imports: `745` across `262` files
- Runtime scheduler imports: `0`

Expected result:
- Remove `95` active test imports from the six sports tests.
- Preserve behavior coverage and avoid any live-trading surface.
