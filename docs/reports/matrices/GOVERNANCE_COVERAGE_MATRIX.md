# Governance Coverage Matrix

| Governance area | Current coverage | Status | Notes |
| --- | --- | --- | --- |
| Root Markdown policy | `scripts/check_root_markdown.py` and `scripts/ops_check.py` | ACTIVE | Enforces `README.md` as the only root Markdown file |
| Repository pre-flight safety | `scripts/check_repo_preflight.py` | ACTIVE | Verifies branch, upstream, clean-state, and task-fit assumptions |
| Architecture and import hygiene | `scripts/check_architecture.py` and repo tests | ACTIVE | Checks runtime shape, ignored source files, and legacy executable references |
| OpenAPI validation | `scripts/check_openapi_contract.py` | ACTIVE | Validates syntax, duplicate IDs, and public contract wording |
| Local ops orchestration | `scripts/ops_check.py` | ACTIVE | Runs the repository checks in one place |
| Compile validation | `python -m compileall src tests scripts` | ACTIVE | Syntax and import-time safety |
| Smoke validation | `pytest -m smoke -q` | ACTIVE | Fast confidence gate |
| Full regression | `powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1 -Mode full` | ACTIVE | Authoritative full gate |
| Duplicate ownership scanning | Reports, audits, and architecture docs | RECOMMENDED | Useful as a review layer; not a single canonical script yet |
| Orphan/dead-code scanning | Reports and audits | RECOMMENDED | Useful for cleanup and freeze phases |
| Provider/connector ownership maps | Architecture docs | IMPLEMENTED IN THIS PASS | Added to make ownership visible to reviewers |
| GitHub Actions wrapper | `.github/workflows/repository-validation.yml` | IMPLEMENTED IN THIS PASS | Calls local scripts only |

## Summary

- Local-first governance is already present and remains authoritative.
- CI is now an automation wrapper around the same checks.
- Remaining future work is primarily additional consolidation, not a missing governance foundation.
