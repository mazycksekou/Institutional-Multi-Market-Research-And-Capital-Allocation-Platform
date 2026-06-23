# Phase 10K8ZHC - Screenshot Workflow Thinning Plan

## Executive Summary
`screenshot_intake.py` is a compatibility surface that still owns screenshot parsing, ticket normalization, and provider-enrichment coordination. The future canonical home for that workflow is `src/services/screenshot_workflow.py`.

The workflow belongs in services because it is orchestration:

- parse the ticket or OCR payload
- normalize the ticket
- call canonical provider/connector bridge services
- build the screenshot-analysis response

It is not core math, and it must not become a live connector boundary.

## Ownership Map

- `screenshot_intake.py`: `COMPATIBILITY_SHIM_CANDIDATE`
- `parse_ticket`: `MIGRATE_TO_SRC_SERVICES`
- `analyze_screenshot_ticket`: `MIGRATE_TO_SRC_SERVICES`
- `_cleanup_confirmed_selection_no_bets`: `MIGRATE_TO_SRC_SERVICES`
- future target: `src/services/screenshot_workflow.py`

## Boundary Notes

- OCR/image parsing is not core math.
- Scoring, pricing, and probability calculations must call `src/core`.
- Provider and connector data must continue to arrive through canonical services.
- No live connector calls or AI/LLM expansion are authorized in this phase.

## Required Statement
The screenshot workflow belongs in `src/services`, while `screenshot_intake.py` remains a compatibility surface until migration proof is complete.
