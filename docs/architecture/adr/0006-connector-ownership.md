# ADR 0006: Connector ownership

## Status

Accepted

## Context

Connectors translate external sources into canonical internal contracts.
Without a clear owner, they can become duplicate mini-services.

## Decision

Connector implementations should live in `src.connectors` and stay thin, explicit, and adapter-like.

## Alternatives Considered

- Split connector logic across feature packages
- Let provider modules own transport glue
- Keep vendor-specific connector forks

## Consequences

- External input normalization has a clear home
- Connectors remain reusable and reviewable
- Source-specific logic stays bounded

## Validation / Enforcement

- architecture maps
- connector ownership docs
- repo tests
