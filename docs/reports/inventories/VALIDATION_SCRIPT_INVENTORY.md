# Validation Script Inventory

| Script | Role | Status | Notes |
| --- | --- | --- | --- |
| `scripts/check_root_markdown.py` | Root Markdown policy | ACTIVE | Enforces `README.md` as the only root Markdown file |
| `scripts/check_repo_preflight.py` | Repository pre-flight safety | ACTIVE | Enforces branch, upstream, and clean-state checks before task handoff |
| `scripts/check_openapi_contract.py` | OpenAPI contract validation | ACTIVE | Validates syntax and public contract hygiene |
| `scripts/check_architecture.py` | Repository architecture validation | ACTIVE | Validates root/runtime shape and legacy executable references |
| `scripts/ops_check.py` | Local ops orchestrator | ACTIVE | Primary local wrapper around the validation stack |
| `scripts/run_tests.ps1` | Full regression gate | ACTIVE | Authoritative full test suite wrapper |
| `scripts/check_all.ps1` | Full validation wrapper | ACTIVE | Convenience shell wrapper around the ops/full checks |
| `scripts/check_local.ps1` | Local validation wrapper | ACTIVE | Convenience wrapper for local mode |
| `scripts/check_render.ps1` | Render validation wrapper | ACTIVE | Environment-specific wrapper |
| `scripts/check_cron.ps1` | Cron validation wrapper | ACTIVE | Environment-specific wrapper |
| `scripts/check_outcome_reconcile.ps1` | Outcome reconciliation wrapper | ACTIVE | Environment-specific wrapper |
| `scripts/smoke_test.py` | Smoke entrypoint | ACTIVE | Supports fast validation workflows |

## Classification Notes

- ACTIVE means the script is part of the current validation story.
- DEPRECATED would mean a script is no longer used and should be archived or removed.
- RECOMMENDED would mean the repo should consider adding a new script for a missing capability.
