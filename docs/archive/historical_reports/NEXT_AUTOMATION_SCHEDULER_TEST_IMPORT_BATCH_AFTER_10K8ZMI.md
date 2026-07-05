# Next Automation Scheduler Test Import Batch After 10K8ZMI

Recommended next test batch:

1. `tests/test_baseball_impact_intelligence.py` - `17` active imports
2. `tests/test_golf_impact_intelligence.py` - `16` active imports
3. `tests/test_hockey_impact_intelligence.py` - `16` active imports
4. `tests/test_soccer_impact_intelligence.py` - `16` active imports
5. `tests/test_combat_impact_intelligence.py` - `15` active imports
6. `tests/test_tennis_impact_intelligence.py` - `15` active imports

Current post-batch counts:
- Active test imports: `482` across `197` files
- Internal scheduler imports: `745` across `262` files

This keeps the largest active test blockers moving first while leaving the scheduler package intact for now.
