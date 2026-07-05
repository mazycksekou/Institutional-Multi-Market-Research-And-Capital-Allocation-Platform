# ADR 0005: Provider ownership

## Status

Accepted

## Context

Provider responsibilities were historically easy to duplicate across multiple packages.

## Decision

Provider contracts and provider-facing behavior should have one canonical owner under `src.providers`.
Policy and gate logic may live in the security layer when the concern is safety rather than provider shape.

## Alternatives Considered

- Let each feature own its own provider wrapper
- Keep compatibility packages as long-term owners
- Merge provider behavior into unrelated runtime modules

## Consequences

- Provider semantics become clearer
- Reviewers can see where provider ownership lives
- Duplicate provider logic is less likely to reappear

## Validation / Enforcement

- architecture maps
- repo tests
- local architecture checks
