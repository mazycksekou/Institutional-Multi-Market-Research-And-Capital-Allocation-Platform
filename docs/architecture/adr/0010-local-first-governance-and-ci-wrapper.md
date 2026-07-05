# ADR 0010: Local-first governance with CI wrapper

## Status

Accepted

## Context

The repository needs automated checks, but correctness should not depend on an external CI service.

## Decision

Local scripts are the canonical validation source.
GitHub Actions may run the same scripts as an automation wrapper, but it should not duplicate validation logic.

## Alternatives Considered

- Make CI the only source of validation truth
- Embed validation logic directly in workflow YAML
- Skip automation entirely

## Consequences

- Local development stays authoritative
- CI provides review signals without changing the rules
- The repository remains usable even when CI is unavailable

## Validation / Enforcement

- `scripts/check_root_markdown.py`
- `scripts/check_openapi_contract.py`
- `scripts/check_architecture.py`
- `scripts/ops_check.py`
- `.github/workflows/repository-validation.yml`
