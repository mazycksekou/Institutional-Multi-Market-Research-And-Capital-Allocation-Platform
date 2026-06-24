# Strategy / Execution Helper Ownership Map After 10K8ZIN

| File | Current status | Canonical owner | Delete-readiness |
| --- | --- | --- | --- |
| `automation_scheduler/broker_quality_scoring.py` | Active compatibility/runtime wrapper | `src.services.execution_service` | Not delete-ready |
| `automation_scheduler/small_account_strategy.py` | Active compatibility/runtime wrapper | `src.services.execution_service` | Not delete-ready |
| `automation_scheduler/manifold_no_bet_detector.py` | Active compatibility/runtime wrapper | `src.services.execution_service` | Not delete-ready |
| `automation_scheduler/institutional_execution_desk.py` | Active compatibility/runtime wrapper | `src.services.execution_service` | Not delete-ready |
| `src/services/execution_service.py` | Canonical service helper | `src.services` | N/A |

## Ownership notes

- Core math/risk/portfolio primitives remain in `src.core`.
- The service layer owns the orchestration and deterministic helper composition.
- The broker boundary remains disabled and production-shaped.
