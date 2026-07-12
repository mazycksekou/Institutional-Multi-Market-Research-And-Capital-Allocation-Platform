# Subsystem Dependency Map

This map shows the main dependency directions that the repository should preserve.
It is an index over the canonical ownership and dependency documents, not a replacement for them.

| Subsystem | Upstream dependencies | Downstream dependencies | Forbidden dependencies | Reusable contracts |
| --- | --- | --- | --- | --- |
| Governance layer | `PROJECT_STATUS.md`, `NEXT_ACTION.md`, `STATUS_UPDATE_POLICY.md`, `MASTER_ROADMAP.md`, `REPOSITORY_OS.md` | All active phases, tests, and validation scripts | Runtime modules, provider logic, or dataset mutation | `MASTER_DOCUMENT_INDEX.md`, `DOCUMENT_RETENTION_INDEX.md`, `DOCUMENT_LIFECYCLE_POLICY.md` |
| Historical acquisition and certification | Source discovery, connector mapping, raw acquisition cache, lineage, and lifecycle runtimes | Historical dataset population and later evidence layers | Direct provider writes into certified tables | `HISTORICAL_DATASET_ACQUISITION_FRAMEWORK.md`, `HISTORICAL_DATASET_ACQUISITION_RUNTIME.md`, `HISTORICAL_RESEARCH_ASSET_CERTIFICATION_RUNTIME.md`, `RESEARCH_ASSET_LIFECYCLE_RUNTIME.md` |
| Dataset, feature, math, signal, and decision chain | Certified historical dataset rows and upstream lineage | Feature snapshots, math outputs, signals, decision rows, and backtests | Raw-provider rereads, post-cutoff leakage, or recomputation from uncertified sources | `HISTORICAL_DATASET_POPULATION_LAYER.md`, `FEATURE_SNAPSHOT_CONTRACT.md`, `UNIVERSAL_MATHEMATICAL_ENGINE_CONTRACTS.md`, `SIGNAL_POPULATION_LAYER.md`, `DECISION_ROW_POPULATION_LAYER.md` |
| Dashboard and P0 readiness | Persisted dataset, feature, signal, decision, lifecycle, and certification evidence | `streamlit_dashboard_data`, `nfl_p0_foundation`, and human readiness review | Live execution, mutable source truth, or hidden joins | `NFL_P0_DATA_FOUNDATION.md`, `STREAMLIT_DATA_PIPELINE.md`, `RESEARCH_ASSET_LIFECYCLE_RUNTIME.md` |
| Validation and preflight | Canonical docs, runtime owners, and repository OS policy | Repository preflight, smoke tests, docs checks, and full gate execution | Product logic, provider access, or data rewrites | `AUTOMATED_GOVERNANCE.md`, `VALIDATION_RUNBOOK.md`, `OPS_WORKFLOW.md` |

The safest design rule is simple: dependencies should flow from governed source evidence into derived layers, never in reverse.
