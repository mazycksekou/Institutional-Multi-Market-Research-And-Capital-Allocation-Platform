# Vendor Reference Classification

## Scope
- Current active documentation, operational docs, and architecture docs were reviewed for vendor-specific or company-specific wording.
- Historical archive content was not normalized when it functions as evidence.

## Classification Table

| Reference | File | Classification | Reason | Action |
| --- | --- | --- | --- | --- |
| `Custom GPT`, `GPT Actions`, `ChatGPT` | `docs/architecture/OPENAPI_CONTRACT_GOVERNANCE.md` | SAFE TO NEUTRALIZE | Architecture guidance should describe the platform, not a vendor brand. | Reworded to platform-neutral language. |
| `Custom GPT`, `ChatGPT` | `docs/reports/audits/OPENAPI_DEPENDENCY_AND_RISK_REPORT.md` | SAFE TO NEUTRALIZE | Audit text can describe the risk without repeating vendor branding. | Reworded to neutral wording. |
| `DeepSeek` | `docs/DEEPSEEK_DATA_PULL_CHECK.md` | REQUIRED TECHNICAL REFERENCE | The wrapper and script names are still DeepSeek-named for compatibility and factual operational reference. | Keep the technical references; soften prose where practical. |
| `OpenAI` | `docs/architecture/VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md` | REQUIRED TECHNICAL REFERENCE | The doc explicitly explains the OpenAPI-versus-OpenAI distinction required by this audit. | Keep as a policy statement. |
| `Meta` | `docs/architecture/COMPLETE_STORAGE_BLUEPRINT.md`, `docs/architecture/STORAGE_DIRECTORY_MAP.md` | DO NOT TOUCH | Search hits come from words like `metadata`, not the company name. | False positive from substring matching. |
| `OpenAI`, `Anthropic`, `Gemini`, `Perplexity`, `Together` | `docs/archive/historical_reports/*.md` | REQUIRED HISTORICAL REFERENCE | These names appear in archived audits and evidence reports. | Keep as historical audit evidence. |

## Summary
- Public-facing platform wording is now vendor-neutral.
- Technical references remain where they are factual and useful.
- Historical archives continue to preserve the original evidence trail.
