# OpenAPI Contract Governance

## Contract Quality Assessment
- OpenAPI version: 3.1.0
- Paths: 2
- Operations: 2
- Schemas: 3
- Duplicate operation IDs: none found in the current contract
- Duplicate schema keys: none found in the current contract

## Schema Improvement Recommendations

| Area | Current state | Recommendation | Risk |
| --- | --- | --- | --- |
| `additionalProperties` | Enabled on public request schemas | Keep for backward compatibility for now; tighten only in a major version. | Medium if narrowed too early |
| Loose scalar typing | Several fields accept `integer`, `number`, `string`, and `null` | Normalize progressively if client behavior stabilizes, but avoid a breaking change in this phase. | Medium |
| Nullable optional inputs | Many fields are optional and nullable | Preserve current behavior; document required-vs-optional semantics more clearly. | Low |
| Response payloads | Responses are intentionally flexible | Keep broad responses for compatibility; consider typed response envelopes in a future major revision. | Low to Medium |

## Validation Recommendations
- Add a repository validator that checks:
  - YAML syntax
  - duplicate mapping keys
  - duplicate `operationId` values
  - unresolved internal `$ref` targets
  - JSON Schema validity for component schemas
  - removal of vendor-specific wording from the public contract
- Integrate the validator into repository checks so contract regressions fail early.

## Version Governance Recommendations
- Use semantic versioning for the public contract.
- Increment the minor version for non-breaking wording and metadata updates.
- Increment the major version only for path removals, required-field additions, or schema narrowing that breaks clients.
- Use patch releases only for validation, documentation, or internal tooling changes that do not alter the public interface.
- Current recommended version after this hardening pass: `2.2.0`.

## Vendor Neutrality Recommendations
- Replace `Custom GPT`, `GPT Actions`, and `ChatGPT` with platform-neutral wording.
- Preferred public terms:
  - public API
  - platform
  - market intelligence platform
  - clients
  - analysis API
  - model gateway
- Avoid vendor names in the public contract unless a compatibility note is strictly necessary.

## Proprietary IP Exposure Assessment
- The contract does not expose proprietary algorithms, feature engineering, weights, or internal storage details.
- The public surface stays focused on request/response schemas, authentication, and error handling.
- The main exposure risk is descriptive language that could imply a specific vendor workflow rather than the platform itself.
- Recommendation: keep implementation details private and keep contract descriptions high level.

## Implementation Roadmap
1. Land the neutral wording updates in `openapi.yaml` and the runtime OpenAPI metadata.
2. Add a contract validator and wire it into repository checks.
3. Add tests for vendor neutrality and schema integrity.
4. Keep the root `openapi.yaml` as the canonical public artifact.
5. Revisit schema tightening only after client usage data shows it is safe to do so.

