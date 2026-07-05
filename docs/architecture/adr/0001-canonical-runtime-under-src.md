# ADR 0001: Canonical runtime under `src`

## Status

Accepted

## Context

The repository previously accumulated runtime-like code and compatibility surfaces outside the canonical runtime root.
That created ambiguity for contributors and reviewers.

## Decision

All runtime and application code should live under `src/`.
Root-level runtime logic should be limited to thin entrypoints only.

## Alternatives Considered

- Keep multiple runtime roots
- Move only selected modules
- Preserve compatibility surfaces indefinitely

## Consequences

- Ownership becomes easier to reason about
- New runtime code has a clear home
- Compatibility layers must remain thin and documented

## Validation / Enforcement

- `scripts/check_architecture.py`
- `scripts/ops_check.py`
- architecture docs and repo tests
