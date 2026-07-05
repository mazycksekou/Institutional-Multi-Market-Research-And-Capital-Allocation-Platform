# Automated Governance

## Purpose

Automated governance keeps the repository safe by making the validation rules executable.
Local scripts remain the source of truth; CI is only a wrapper around them.

## Local Validation Flow

The canonical local checks are:

1. `python scripts/check_root_markdown.py`
2. `python scripts/check_openapi_contract.py --output text`
3. `python scripts/check_architecture.py --output text`
4. `python scripts/ops_check.py --mode local --output text --skip-network`
5. `python -m compileall src tests scripts`
6. `pytest -m smoke -q`

## Current Governance Checks

| Check | Purpose | Authoritative source |
| --- | --- | --- |
| Root Markdown check | Enforces `README.md` as the only root Markdown file | `scripts/check_root_markdown.py` |
| OpenAPI validation | Validates syntax, uniqueness, and public contract hygiene | `scripts/check_openapi_contract.py` |
| Architecture validation | Enforces repository shape, import hygiene, and reference safety | `scripts/check_architecture.py` |
| Local ops bundle | Runs the local verification stack in one place | `scripts/ops_check.py` |
| Compile check | Detects syntax and import-time failures | `python -m compileall` |
| Smoke suite | Fast developer confidence check | `pytest -m smoke -q` |

## GitHub Actions Workflow

GitHub Actions is an optional automation wrapper that runs the same local scripts.

- Workflow file: `.github/workflows/repository-validation.yml`
- Workflow name: `Repository Validation`
- Trigger: push and pull requests targeting `phase-6-api-slimming` and `main`
- Purpose: provide an automated reminder and status signal without duplicating validation logic

## Required Checks

### Before commit

- Run the local scripts listed above
- Confirm the working tree is clean

### Before pull request

- Run the local checks and review the resulting reports
- Ensure the branch is ready to share without hidden architecture regressions

### Before merge

- Confirm the smoke suite and ops check pass
- Confirm architecture and OpenAPI checks pass

### Before release

- Confirm the same local checks, plus any deployment-specific checks required by the target environment

## Why Local Scripts Are Authoritative

- They run inside the repository context
- They reflect the actual checked-in code and docs
- They are versioned with the project
- CI wrappers can fail independently of the repository logic, so the repository scripts remain the trusted source

## Optional Future CI Enhancements

- Add caching if it does not obscure validation
- Add status badges if they help reviewers
- Add environment-specific jobs only after the local checks remain stable
