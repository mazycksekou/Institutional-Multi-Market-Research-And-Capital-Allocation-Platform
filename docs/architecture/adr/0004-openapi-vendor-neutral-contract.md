# ADR 0004: OpenAPI vendor-neutral contract

## Status

Accepted

## Context

The public API contract must remain understandable to external clients without implying a specific AI vendor or proprietary implementation.

## Decision

`openapi.yaml` remains the canonical checked-in contract file at repository root.
Public wording should remain vendor-neutral and describe the platform interface rather than a vendor brand.

## Alternatives Considered

- Move the file away from the root
- Rename the file to vendor-branded terminology
- Expose internal model details in the public contract

## Consequences

- External consumers can rely on the standard OpenAPI filename
- The repository avoids confusing OpenAPI with a vendor brand
- Proprietary logic stays private

## Validation / Enforcement

- `scripts/check_openapi_contract.py`
- OpenAPI governance docs
- repo tests that check public contract wording
