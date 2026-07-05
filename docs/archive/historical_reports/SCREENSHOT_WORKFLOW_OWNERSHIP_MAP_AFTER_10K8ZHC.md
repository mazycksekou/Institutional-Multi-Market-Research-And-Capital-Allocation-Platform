# Screenshot Workflow Ownership Map After 10K8ZHC

| Path / Function | Classification | Why |
| --- | --- | --- |
| `screenshot_intake.py` | `COMPATIBILITY_SHIM_CANDIDATE` | Root-level compatibility surface for screenshot analysis. |
| `parse_ticket` | `MIGRATE_TO_SRC_SERVICES` | Ticket normalization/orchestration, not core math. |
| `analyze_screenshot_ticket` | `MIGRATE_TO_SRC_SERVICES` | Service orchestration over normalization and provider enrichment. |
| `_cleanup_confirmed_selection_no_bets` | `MIGRATE_TO_SRC_SERVICES` | Response shaping and cleanup logic for the service workflow. |
| `src/services/screenshot_workflow.py` | future canonical owner | The planned service home for screenshot workflow logic. |

## Notes

- Image parsing/OCR does not belong in `src/core`.
- No live connector boundary should be created here.
- Provider enrichment must continue to flow through canonical services.
