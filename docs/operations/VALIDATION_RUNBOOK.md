# Validation Runbook

Use this runbook when you need to verify repository health locally.

## Standard Order

1. `python scripts/check_root_markdown.py`
2. `python scripts/check_openapi_contract.py --output text`
3. `python scripts/check_architecture.py --output text`
4. `python scripts/ops_check.py --mode local --output text --skip-network`
5. `python -m compileall src tests scripts`
6. `pytest -m smoke -q`

## When to Use Full Regression

- Use the full regression suite when runtime code, contracts, or architecture rules change
- Use the targeted tests for the touched subsystem first, then expand if needed

## Interpreting Results

- Root Markdown failures usually mean a new Markdown file was created outside `docs/`
- OpenAPI failures usually mean the public contract changed or became inconsistent
- Architecture failures usually mean imports, root files, or ignored source files need review
- Ops failures usually mean one of the local governance checks failed or the repository state is inconsistent

## Recovery Guidance

- Fix the root cause first
- Re-run the narrowest relevant check
- Do not skip from a failing targeted check straight to a merge

## Reviewer Use

- This runbook exists so a reviewer can confirm the repository is healthy without needing to understand every implementation detail
