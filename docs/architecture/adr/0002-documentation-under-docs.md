# ADR 0002: Documentation under `docs`

## Status

Accepted

## Context

Markdown files were historically scattered across the repository, which made it harder to find current guidance and audit history.

## Decision

`docs/` is the canonical home for documentation.
The repository root should keep only `README.md` as Markdown.

## Alternatives Considered

- Keep phase reports at the root
- Split docs across multiple top-level folders
- Rely on convention without enforcement

## Consequences

- Documentation becomes easier to browse
- Historical material can be archived without cluttering the root
- Automated checks can enforce the rule consistently

## Validation / Enforcement

- `scripts/check_root_markdown.py`
- `scripts/ops_check.py`
- documentation governance docs
