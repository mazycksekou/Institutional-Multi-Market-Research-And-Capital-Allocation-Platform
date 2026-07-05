# Terminology Inventory And Classification

## Scope
This inventory reviews the repository for terminology related to vendor, provider, model, runtime, connector, adapter, integration, client, action, analysis route, inference, prediction, market intelligence, external model, proprietary model, and public API contract language.

## Classification Summary

| Term family | Where it appears | Classification | Action |
| --- | --- | --- | --- |
| `provider` | `src/`, `docs/`, `tests/`, `scripts/` | FUNCTIONALLY DIFFERENT — DO NOT CHANGE | Keep the exact term where it denotes data providers, model providers, sportsbook providers, or connector ownership. Standardize only the surrounding prose when the meaning is explicit. |
| `model` | `src/`, `docs/`, `tests/` | FUNCTIONALLY DIFFERENT — DO NOT CHANGE | Keep exact identifiers for ML models, data models, schema models, and business-model references. |
| `runtime` | `src/`, `docs/`, `tests/`, `scripts/` | FUNCTIONALLY DIFFERENT — DO NOT CHANGE | Preserve meaning by context: app runtime, model runtime, deployment runtime, or execution runtime. |
| `connector` / `adapter` | `src/`, `docs/` | CODE IDENTIFIER — DO NOT CHANGE WITHOUT IMPORT/RUNTIME CHECK | These are canonical architectural roles and live code names. |
| `client` / `integration` / `action` / `analysis route` | `docs/`, `openapi.yaml` | PUBLIC-FACING DOC — STANDARDIZE IF SAFE | Use neutral platform wording in active docs and contract text. |
| `OpenAPI` | `openapi.yaml`, docs/architecture notes | KEEP EXACT TERM | It is the specification standard, not a brand name. |
| `OpenAI`, `ChatGPT`, `Custom GPT`, `GPT Actions` | active docs, tests, archives | MIXED | Standardize in public docs when safe, keep in historical archives, keep in tests that assert forbidden public wording, and keep in policy docs when explaining the distinction. |
| `Anthropic`, `Claude`, `Google`, `Gemini`, `Microsoft`, `Meta`, `XAI`, `DeepSeek`, `Perplexity` | active docs, archives, scripts, code identifiers | MIXED | Keep when the reference is technical, historical, or part of a compatibility script/identifier. Do not rewrite archive evidence. |
| `public API contract` | `openapi.yaml`, docs/architecture | PUBLIC-FACING DOC — STANDARDIZE IF SAFE | Preferred neutral wording for the external contract. |
| `market intelligence platform` | docs/architecture | PUBLIC-FACING DOC — STANDARDIZE IF SAFE | Preferred neutral platform description. |
| `proprietary model logic` | docs/architecture | INTERNAL ARCHITECTURE DOC — STANDARDIZE IF SAFE | Preferred phrase for private implementation details. |

## Reviewed Active Documentation
- `openapi.yaml`
- `README.md`
- `docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md`
- `docs/architecture/VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md`
- `docs/reports/audits/OPENAPI_DEPENDENCY_AND_RISK_REPORT.md`
- `docs/reports/audits/VENDOR_REFERENCE_CLASSIFICATION.md`
- `docs/DEEPSEEK_DATA_PULL_CHECK.md`

## Reviewed Historical Records
- `docs/archive/historical_reports/*`

## Standardization Decisions
- Public contract language is neutralized.
- Technical compatibility names remain when they identify an active script, test, or code path.
- Historical evidence remains unchanged except for optional clarifying notes.
- Code identifiers are left unchanged unless a runtime-safe refactor is explicitly validated.

## False Positives And Distinctions
- `Meta` matches in active docs were substring false positives from words such as `metadata`.
- `provider` is not always a vendor reference.
- `model` is not always an ML model.
- `runtime` is not always a deployment/runtime concern.
- `connector` is not always a network integration.

## Repository Guidance
- Standardize public-facing prose in active docs.
- Preserve functional identifiers in code.
- Preserve historical truth in archive documents.
- Use the terminology standard as the single canonical reference when future wording decisions are needed.

