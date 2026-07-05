# ADR 0009: Proprietary implementation boundary

## Status

Accepted

## Context

Reviewers need to trust the platform without gaining access to proprietary algorithms, feature engineering, or private model details.

## Decision

Public docs and contracts should describe external behavior only.
Internal algorithms, feature generation, calibration, weights, and decision logic must remain private to runtime packages and local validation.

## Alternatives Considered

- Document private internals publicly
- Expose model mechanics in the API contract
- Keep proprietary behavior undocumented

## Consequences

- The platform remains reviewer-friendly without exposing sensitive logic
- Public contracts are simpler to understand
- Internal ownership boundaries remain enforceable

## Validation / Enforcement

- OpenAPI governance docs
- terminology standard
- architecture review docs
