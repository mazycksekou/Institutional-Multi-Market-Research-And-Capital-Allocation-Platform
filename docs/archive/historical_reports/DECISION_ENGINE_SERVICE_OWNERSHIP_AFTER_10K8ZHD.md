# Decision Engine Service Ownership After 10K8ZHD

| Path / Function | Classification | Why |
| --- | --- | --- |
| `src/services/decision_engine.py` | `SERVICE_ORCHESTRATION_OWNER` | Canonical decision orchestration over `src.core`. |
| `build_decision_context` | `SERVICE_ORCHESTRATION_OWNER` | Assembles a decision context from core helpers. |
| `evaluate_decision` | `SERVICE_ORCHESTRATION_OWNER` | Produces the decision envelope and keeps live execution disabled. |
| `build_decision_summary` | `SERVICE_ORCHESTRATION_OWNER` | Summarizes the decision context for route-facing callers. |
| `bet_decision_engine.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Legacy root wrapper kept for caller compatibility. |
| `decision_label` | `MIGRATE_TO_SRC_CORE` | Pure rule logic that belongs with the rest of the decision math. |
| `risk_grade_from_kelly` | `MIGRATE_TO_SRC_CORE` | Pure risk classification logic. |
| `kelly_fraction_multiplier` | `MIGRATE_TO_SRC_CORE` | Pure sizing math that belongs in `src.core`. |
| `no_vig_probability_for_line` | `MIGRATE_TO_SRC_CORE` | Pure probability math that belongs in `src.core`. |

## Notes

- `src/services/decision_engine.py` already depends only on canonical core helpers.
- No live connector or broker execution is allowed here.
- The root decision wrapper stays only until callers are redirected.
