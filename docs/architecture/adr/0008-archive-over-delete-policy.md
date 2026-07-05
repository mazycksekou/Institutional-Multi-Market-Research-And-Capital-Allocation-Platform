# ADR 0008: Archive over delete

## Status

Accepted

## Context

Historical reports and proofs often still provide useful audit evidence even after they are no longer active documentation.

## Decision

Archive historical documents when they still have audit or provenance value.
Delete only files that are obsolete, duplicated, unreferenced, and not useful for future review.

## Alternatives Considered

- Delete aggressively
- Keep everything at the root
- Treat all historical reports as active docs

## Consequences

- Audit evidence is preserved
- The repository remains easier to inspect over time
- Deletion decisions require proof rather than guesswork

## Validation / Enforcement

- documentation governance docs
- archive folders under `docs/archive/`
- repository review discipline
