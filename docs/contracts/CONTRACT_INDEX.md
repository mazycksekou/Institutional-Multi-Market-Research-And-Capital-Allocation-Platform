# Contract Index

This index points reviewers and contributors to the active contracts that define repository behavior.

| Contract | Owner | Purpose | Compatibility notes | Validation status |
| --- | --- | --- | --- | --- |
| OpenAPI contract | `src.api` / `openapi.yaml` | Public machine-readable API interface | Keep vendor-neutral and root-based unless tooling proves otherwise | Validated by `scripts/check_openapi_contract.py` |
| Dataset registry | `src.data` | Canonical dataset metadata and readiness state | Keep versioned and traceable | Documented and covered by repo tests |
| Data lineage contract | `src.data` | Source-to-consumer traceability | Preserve lineage for reproducibility | Documented |
| Database schema | `src.storage` / `src.data` | Local storage and table ownership | Keep backend-neutral where possible | Documented |
| Feature snapshot contract | `src.data` / `src.backtesting` | Persisted feature values and versioning | Avoid leakage between training and evaluation | Documented |
| Mathematical engine contracts | `src.core` / `src.data` | Canonical math-engine inputs, outputs, lifecycle, and validation rules | Keep engine dependencies limited to features in the universal feature registry | Documented |
| Backtest contract | `src.backtesting` | Historical replay and evaluation payloads | Preserve payload shape for compatibility | Documented and tested |
| Model input contract | `src.market_intelligence` / `src.research` | Inputs consumed by model or analysis runtime | Keep private feature details out of public docs | Documented |
| Model output contract | `src.analytics` / `src.services` | Public or internal output shape | Keep outputs stable across consumers | Documented |
| Market profile contract | `src.data` / `src.market_intelligence` | Canonical profile shape for each reusable market family | Keep profiles reusable and point-in-time aware | Documented and tested |
| Sports market profile | `src.market_intelligence` | Reusable sports-family contract | NFL is the first sports instance, not a separate architecture | Documented |
| Prediction market profile | `src.market_intelligence` | Reusable prediction-market contract | Preserve settlement and order book semantics | Documented |
| Options / 0DTE market profile | `src.market_intelligence` | Reusable short-dated options contract | Preserve expiry-aware and chain-aware behavior | Documented |
| NFL sports profile instance | `src.market_intelligence` | NFL configuration of the sports profile family | Keep NFL inside the sports architecture | Documented |
| Provider field matrix | `src.providers` / `src.data` | Which provider can supply each field | No single provider is assumed for all fields | Documented |
| Sport-specific field contracts | `src.market_intelligence` | Sport-by-sport required and optional fields | Do not invent sports or merge different sports | Documented |
| Streamlit contract | `src.services` | Dashboard presentation and adapter expectations | Keep presentation separate from storage | Documented |
| Validation framework | `src.data` / `scripts/check_architecture.py` | Required field, type, and compatibility checks | Run locally before commit | Validated by repo scripts |
| Versioning strategy | `src.data` / `src.services` | Dataset, schema, feature, and lineage versioning | No anonymous writes | Documented |

## Notes

- This index intentionally separates public-facing contracts from implementation helpers.
- A contract is considered mature when its owner, validation path, and compatibility expectations are documented.
- Contracts that expose internal behavior should be rewritten to describe only the external interface.
