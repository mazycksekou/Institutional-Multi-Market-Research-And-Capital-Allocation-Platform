# OpenAPI Dependency And Risk Report

## Baseline
- Repository state at audit start was clean on `phase-6-api-slimming`.
- `openapi.yaml` is tracked at repository root.
- No runtime code directly loads `openapi.yaml`.

## Reference Matrix

| Artifact | Current relationship | Reference type | Notes |
| --- | --- | --- | --- |
| `openapi.yaml` | Canonical checked-in contract artifact | Public contract | Contains the public OpenAPI contract for the platform; the filename follows the OpenAPI standard. |
| `main.py` | Generates runtime `/openapi.json` metadata | Active runtime | App title/description feed the live OpenAPI document. |
| `src/api/performance_routes.py` | Custom OpenAPI generator | Active runtime | Overrides live schema description and server URL. |
| `src/api/betting_action_routes.py` | Route descriptions for public analysis routes | Active runtime | Public contract wording appears in route docstrings/descriptions. |
| `scripts/smoke_test.py` | Validates live `/openapi.json` | Active script | Uses runtime OpenAPI, not the checked-in `openapi.yaml` file. |
| `tests/test_multi_sport_model_registry.py` | Checks live OpenAPI shape | Active test | Confirms `/api/actions/models/sports-registry` is exposed. |
| `tests/test_sport_analysis_endpoint.py` | Checks live OpenAPI shape | Active test | Confirms `/api/actions/models/sport-analysis` is exposed. |
| `docs/archive/historical_reports/*` | Historical mentions only | Documentation | References to `openapi.yaml` are audit history, not active code paths. |

## Dependency Report
- The checked-in contract is referenced directly by humans and tooling as a public artifact.
- The runtime application does not load `openapi.yaml` from disk.
- The live OpenAPI document is generated from FastAPI metadata and route definitions.
- The live smoke test depends on `/openapi.json`, not on the root file.
- No deployment tool currently requires `openapi.yaml` at a different location.

## Risk Report

| Risk | Severity | Why it matters | Recommendation |
| --- | --- | --- | --- |
| Vendor-specific contract wording | Medium | Public docs still suggest vendor-specific assistant branding. | Replace terminology with platform-neutral language. |
| Runtime and checked-in contract drift | Medium | `openapi.yaml` and `/openapi.json` can diverge if descriptions are updated in one place only. | Keep shared wording aligned and validate both surfaces. |
| Permissive schema shapes | Low to Medium | `additionalProperties: true` preserves compatibility but weakens contract specificity. | Tighten in a future major version only if client usage stabilizes. |
| Root file location churn | Low | Moving the contract without a concrete consumer benefit could break external references. | Keep `openapi.yaml` at repository root. |

## Root Location Recommendation
- Keep `openapi.yaml` at repository root.
- Reason: it is a stable public contract artifact, it is not loaded as runtime code, the filename is the standard OpenAPI filename, and there is no current evidence that moving it would improve safety or maintainability.
