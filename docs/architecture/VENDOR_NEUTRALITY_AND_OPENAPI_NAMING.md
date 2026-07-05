# Vendor Neutrality And OpenAPI Naming

## Principle
- OpenAPI is a public API specification standard.
- OpenAPI is not OpenAI.
- `openapi.yaml` is the correct contract filename for a checked-in OpenAPI document.
- `openapi.yaml` should remain at repository root unless a real tooling or deployment dependency proves a safe move.
- This note is specialized; the canonical terminology definitions live in `TERMINOLOGY_STANDARD.md`.

## Public Contract Boundary
- The OpenAPI contract exposes only the public interface.
- It should stay vendor-neutral and platform-oriented.
- It must not expose proprietary algorithms, feature engineering, model weights, internal storage, or decision logic.

## Naming Guidance
- Preferred public wording:
  - public API contract
  - analysis API
  - market intelligence platform
  - model provider
  - external client
  - provider-backed model
  - API action
- Avoid branding the platform around a specific vendor when describing public endpoints, docs, or contract behavior.

## What May Keep Vendor Names
- Historical archives
- Factual dependency or provider documentation
- Legal, security, or licensing notes
- Tests that intentionally assert forbidden public contract terms

## Compatibility Note
- Some operational scripts and legacy technical references may still use provider-specific names for compatibility.
- Those names should be treated as technical identifiers, not platform branding.

## Implementation Note
- The current checked-in OpenAPI contract and runtime OpenAPI metadata are vendor-neutral.
- The root `openapi.yaml` filename is correct and should not be renamed for branding reasons.
