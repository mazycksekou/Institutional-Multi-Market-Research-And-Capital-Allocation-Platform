# ADR 0007: Thin root entrypoints

## Status

Accepted

## Context

The repository needs a few root entrypoints for developer ergonomics and platform integration.

## Decision

Root entrypoints such as `main.py`, `api_server.py`, and `streamlit_app.py` should remain thin wrappers that import canonical `src.*` modules.

## Alternatives Considered

- Move every entrypoint into `src`
- Put application logic directly into the root files
- Duplicate logic between root and `src`

## Consequences

- Tooling and deployment remain convenient
- Runtime ownership still lives under `src`
- Root files do not become hidden feature owners

## Validation / Enforcement

- `scripts/check_architecture.py`
- repo tests that inspect root runtime files
