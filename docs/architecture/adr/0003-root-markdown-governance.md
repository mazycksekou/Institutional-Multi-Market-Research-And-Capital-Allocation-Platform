# ADR 0003: Root Markdown governance

## Status

Accepted

## Context

Root-level Markdown outside `README.md` creates ambiguity about what is current, authoritative, and user-facing.

## Decision

Only `README.md` is permitted at the repository root.
All other Markdown should be created directly under the correct `docs/` subfolder.

## Alternatives Considered

- Allow a small set of root reports
- Allow temporary root reports during migration
- Use root Markdown as a staging area

## Consequences

- Documentation structure stays clean
- Reviewers have a single authoritative place to look
- Historical reports remain available in archive/report folders

## Validation / Enforcement

- `scripts/check_root_markdown.py`
- `scripts/ops_check.py`
- repo tests that inspect root Markdown policy
