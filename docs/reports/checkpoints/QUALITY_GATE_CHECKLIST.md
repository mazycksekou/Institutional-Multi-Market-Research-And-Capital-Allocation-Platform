# Quality Gate Checklist

Use this checklist before commit, pull request, merge, or release.

## Pre-Commit

- [ ] `python scripts/check_repo_preflight.py --before-commit`
- [ ] `python scripts/check_root_markdown.py`
- [ ] `python scripts/check_openapi_contract.py --output text`
- [ ] `python scripts/check_architecture.py --output text`
- [ ] `python scripts/check_audit_lifecycle.py`
- [ ] `python scripts/check_document_lifecycle.py`
- [ ] `python scripts/ops_check.py --mode local --output text --skip-network`
- [ ] `python -m compileall src tests scripts`
- [ ] `pytest -m smoke -q`

## Pre-Push

- [ ] `python scripts/check_repo_preflight.py --before-push`
- [ ] Working tree is clean
- [ ] Branch is synchronized with upstream

## Pre-Pull Request

- [ ] Targeted tests for changed areas passed
- [ ] Architecture and contract checks passed
- [ ] Pre-flight checks are clean
- [ ] Working tree is clean

## Pre-Merge

- [ ] Smoke suite passed
- [ ] Ops check passed
- [ ] OpenAPI and architecture checks passed
- [ ] Pre-flight branch and upstream checks passed
- [ ] No unresolved review or policy concerns remain

## Pre-Release

- [ ] Full regression gate passed
- [ ] Deployment-specific validation completed
- [ ] Reviewer-facing docs are current

## Notes

- This checklist does not replace engineering judgment.
- If a check fails, fix the root cause before proceeding.
