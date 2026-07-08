# Master System Architecture

This document is the front door for the repository.
It is written for new developers, reviewers, technical partners, investors, and due-diligence readers who need to understand the shape of the platform before reading code.

## 1. Platform Purpose

This repository contains a market-intelligence and analysis platform with canonical runtime ownership under `src/`.
It supports public API access, data and provider contracts, market intelligence, backtesting, reporting, dashboard presentation, governance, and repository validation.

The public surface is intentionally vendor-neutral.
Proprietary implementation details remain inside runtime modules and are not exposed in public docs or the OpenAPI contract.

## 2. Repository Structure

The current repository shape is documented in detail in [Final Repository Structure](./FINAL_REPOSITORY_STRUCTURE.md).

At a high level:

- `src/` contains runtime/application code and runtime assets
- `tests/` contains automated validation
- `scripts/` contains local validation and operational tooling
- `docs/` contains architecture, contracts, operations, reports, and archives
- the repository root keeps only approved entrypoints and required project files

## 3. Canonical Runtime Root Under `src/`

`src/` is the canonical runtime root.
It is the place to look for application ownership and the only place where new runtime code should normally be added.

Primary runtime owners are summarized in [Canonical Ownership Map](./CANONICAL_OWNERSHIP_MAP.md).

The major runtime packages are:

- `src.api` for the thin API layer
- `src.services` for orchestration, facades, and shared service wiring
- `src.providers` for provider contracts and provider-facing behavior
- `src.connectors` for external-source normalization and adapters
- `src.data` for canonical data contracts, lineage, storage, and local helpers
- `src.market_intelligence` for sports, prediction markets, options, manifold, and signal intelligence
- `src.backtesting` for replay, simulation, strategy profiles, and evaluation
- `src.analytics` for reporting, governance, readiness, and summaries
- `src.research` for experiments, calibration, and feature studies
- `src.security` for gates, policy, approval, and secret-safety helpers
- `src.ai` for disabled AI/prompt metadata only
- `src.brokerage` for production-shaped execution and brokerage boundaries without live activation

## 4. Thin Root Entrypoints

The repository root still includes approved entrypoints and local analysis tools for developer and deployment convenience:

- `main.py`
- `api_server.py`
- `orb_backtest.py`
- `streamlit_app.py`
- `zero_dte_orb.py`

These files should delegate into canonical `src.*` modules or remain scoped to their current analysis role.
They are not the place for new feature ownership.

## 5. Major Runtime Modules

The dependency direction and package expectations are summarized in [Dependency Flow Map](./DEPENDENCY_FLOW_MAP.md).

The current ownership boundaries are:

- `src.core` for math, pricing, portfolio, and execution primitives
- `src.data` for canonical datasets, lineage, persistence contracts, and local data helpers
- `src.providers` and `src.connectors` for external boundaries
- `src.market_intelligence` for domain intelligence and signal generation
- `src.backtesting` for replay and simulation
- `src.analytics` for reports and governance summaries
- `src.research` for studies and experiment metadata
- `src.services` for runtime orchestration and facades

## 6. API Layer and `openapi.yaml`

`openapi.yaml` is the checked-in public API contract and remains at repository root because it is the standard OpenAPI filename, not a vendor-branded file.
The contract governance summary lives in [OpenAPI Contract Governance](./OPENAPI_CONTRACT_GOVERNANCE.md) and the vendor-neutral naming policy lives in [Vendor Neutrality and OpenAPI Naming](./VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md).

The contract index in [Contract Index](../contracts/CONTRACT_INDEX.md) identifies the owner and validation status for the main contract surfaces.

The public API should describe the external interface only.
It should not expose proprietary algorithms, feature engineering internals, model weights, secret material, or provider keys.

## 7. Provider Architecture

Provider ownership is centralized under `src.providers`.
The repository treats providers as external sources or provider-facing boundaries that may supply data, model inference, or other platform inputs.

Provider responsibilities, ownership, and related notes are documented in [Canonical Ownership Map](./CANONICAL_OWNERSHIP_MAP.md) and [Provider Ownership Map](./PROVIDER_OWNERSHIP_MAP.md).

## 8. Connector Architecture

Connectors live under `src.connectors`.
They normalize or adapt external input sources into canonical internal contracts and should stay thin and explicit.

See [Connector Ownership Map](./CONNECTOR_OWNERSHIP_MAP.md).

## 9. Model / Runtime Architecture

There is no separate public `src.models` package that owns the whole platform.
Model-like concerns are split by purpose:

- `src.ai` for disabled AI/prompt metadata
- `src.market_intelligence` for model inputs and intelligence-oriented scoring
- `src.research` for experiments and calibration
- `src.backtesting` for evaluation against historical data
- `src.analytics` for readiness and governance summaries

The boundary is described in [Model Flow Map](./MODEL_FLOW_MAP.md).

## 10. Prompt / Runtime Asset Ownership

Prompt assets are owned under `src.ai`.
They are treated as runtime assets only when they are part of the canonical application flow.

Prompt and AI-related assets should not be used to expose or enable live AI behavior in this repository.

## 11. Data Flow

The intended data flow is event-centric and certified before downstream research uses it:

source -> acquisition -> archive -> normalize -> certify -> event -> market -> selection -> feature snapshot -> decision row -> backtest -> consume

Decision rows are generated research artifacts, not the storage primitive.

The canonical data flow and storage expectations are described in [Data Flow Map](./DATA_FLOW_MAP.md), [Historical Research Database](./HISTORICAL_RESEARCH_DATABASE.md), [Storage Directory Map](./STORAGE_DIRECTORY_MAP.md), [Storage Layer Documentation](./STORAGE_LAYER_DOCUMENTATION.md), and the data contracts in `docs/contracts/`.

## 12. Request Flow

Public requests should enter through thin entrypoints and route layers, then move into services and canonical runtime owners.
The API layer should not own duplicate business logic.

For the intended dependency shape, see [Dependency Flow Map](./DEPENDENCY_FLOW_MAP.md) and [Module Dependency Map](./MODULE_DEPENDENCY_MAP.md).

## 13. Backtesting Flow

Backtesting and replay logic lives under `src.backtesting`.
It consumes canonical historical events, markets, selections, and feature snapshots rather than creating a parallel data system.
Decision rows are derived from certified historical data and are not read directly from provider sources.

The backtest contract and related storage expectations are indexed in `docs/contracts/CONTRACT_INDEX.md`.

## 14. Market Intelligence Flow

Market intelligence lives under `src.market_intelligence`.
It covers sports, prediction markets, manifold, options, and signal-oriented analysis where the repository already has canonical ownership.

The market and sport capability views are documented in the architecture and report layers referenced from the docs index.

## 15. Dashboard / Streamlit Flow

Dashboard and Streamlit adapters should consume canonical data and service layers rather than building their own persistence or model logic.

The dashboard-oriented contracts are indexed in `docs/contracts/CONTRACT_INDEX.md`.
The intended pipeline is documented in [Streamlit Data Pipeline](./STREAMLIT_DATA_PIPELINE.md) and the field/display matrices under `docs/reports/matrices/`.

## 16. Storage and Artifact Ownership

Canonical storage and local data helpers live under `src.data` and `src.storage`.
The event-centric historical research database is a shared repository asset, not a market-specific storage fork.

The intended storage hierarchy and local artifact expectations are documented in:

- [Historical Research Database](./HISTORICAL_RESEARCH_DATABASE.md)
- [Storage Directory Map](./STORAGE_DIRECTORY_MAP.md)
- [Storage Layer Documentation](./STORAGE_LAYER_DOCUMENTATION.md)
- [Dataset Registry](../contracts/DATASET_REGISTRY.md)
- [Data Lineage Contract](../contracts/DATA_LINEAGE_CONTRACT.md)

## 17. Public API vs Private Proprietary Boundary

The public API contract exposes the external interface.
It should remain vendor-neutral and readable by external clients.

Private proprietary implementation includes internal algorithms, feature engineering, calibration, scoring, model weights, and decision logic.
Those details remain inside runtime modules and are not documented as public contract surfaces.

This boundary is reinforced by:

- [Terminology Standard](./TERMINOLOGY_STANDARD.md)
- [OpenAPI Contract Governance](./OPENAPI_CONTRACT_GOVERNANCE.md)
- [Vendor Neutrality and OpenAPI Naming](./VENDOR_NEUTRALITY_AND_OPENAPI_NAMING.md)
- ADRs under [docs/architecture/adr/](./adr/)

## 18. Documentation Hierarchy

The repository follows a strict documentation policy:

- `docs/architecture/` for architecture, maps, and front-door guidance
- `docs/contracts/` for active contracts
- `docs/development/` for engineering standards and contributor guidance
- `docs/operations/` for governance and runbooks
- `docs/reports/` for audits, inventories, matrices, proofs, and checkpoints
- `docs/archive/milestones/` for consolidated milestone summaries
- `docs/archive/` for historical evidence and deprecated material
- `docs/MASTER_DOCUMENT_INDEX.md` and `docs/DOCUMENT_RETENTION_INDEX.md` for the top-level documentation indexes

The documentation policy is summarized in [Documentation Governance](./DOCUMENTATION_GOVERNANCE.md) and [Documentation Map](./DOCUMENTATION_MAP.md).

The market-input governing specification is documented in [Master Market Input Specification](./MASTER_MARKET_INPUT_SPECIFICATION.md).

## 19. Contract Hierarchy

The repository’s active contract surfaces are indexed in [Contract Index](../contracts/CONTRACT_INDEX.md).

In practical terms:

1. public API contract
2. data contracts
3. provider and connector contracts
4. backtest contracts
5. storage contracts
6. feature snapshot and versioning contracts
7. dashboard / Streamlit contracts

Contract quality and validation expectations are described in [OpenAPI Contract Governance](./OPENAPI_CONTRACT_GOVERNANCE.md).

## 20. Governance and Validation Checks

The repository is validated locally first.
The canonical governance checks are documented in [Automated Governance](../operations/AUTOMATED_GOVERNANCE.md) and [Validation Runbook](../operations/VALIDATION_RUNBOOK.md).

The core local checks are:

- `python scripts/check_repo_preflight.py --start-task`
- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_document_lifecycle.py`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python -m compileall src tests scripts`
- `pytest -m smoke -q`

GitHub Actions is an optional wrapper around those same local scripts.

## 21. ADR / Decision Record Locations

Architecture decision records live under `docs/architecture/adr/`.

Current ADR topics include:

- canonical runtime under `src`
- documentation under `docs`
- root markdown governance
- OpenAPI vendor-neutral contract
- provider ownership
- connector ownership
- thin root entrypoints
- archive-over-delete policy
- proprietary implementation boundary
- local-first governance with GitHub Actions wrapper

## 22. Engineering Standards Locations

The engineering standards and contribution guidance live in:

- [Engineering Standards](../development/ENGINEERING_STANDARDS.md)
- [Branch Governance Policy](../development/BRANCH_GOVERNANCE_POLICY.md)
- [Contributing](../development/CONTRIBUTING.md)

These documents describe folder rules, naming rules, import rules, test expectations, archive policy, and how to add new providers, connectors, models, or market lanes safely.

## 23. How a New Developer Should Navigate the Repo

Start with:

1. this document
2. [Final Repository Structure](./FINAL_REPOSITORY_STRUCTURE.md)
3. [Canonical Ownership Map](./CANONICAL_OWNERSHIP_MAP.md)
4. [Terminology Standard](./TERMINOLOGY_STANDARD.md)
5. [Contract Index](../contracts/CONTRACT_INDEX.md)
6. [Engineering Standards](../development/ENGINEERING_STANDARDS.md)
7. [Validation Runbook](../operations/VALIDATION_RUNBOOK.md)

Then inspect the canonical owner for the area you want to change.
Avoid adding duplicate ownership or bypassing the service/data boundaries.

## 24. How a Reviewer Should Validate the Repo

Use the local validation stack first:

1. `python scripts/check_root_markdown.py`
2. `python scripts/check_openapi_contract.py --output text`
3. `python scripts/check_architecture.py --output text`
4. `python scripts/ops_check.py --mode local --output text --skip-network`
5. `python -m compileall src tests scripts`
6. `pytest -m smoke -q`

If you need the deeper validation story, read:

- [Automated Governance](../operations/AUTOMATED_GOVERNANCE.md)
- [Validation Runbook](../operations/VALIDATION_RUNBOOK.md)
- the architecture ADRs in `docs/architecture/adr/`

## 25. Remaining Technical Debt or Future Work

The repository is in a strong architectural state, but it is not claiming perfection.

Known ongoing work includes:

- continuing to keep historical reports and audit evidence organized as the repo evolves
- preserving the thin-entrypoint model for any future root-level tools
- maintaining vendor-neutral wording as the public API and docs evolve
- tightening schemas or contracts only when the breaking-change cost is justified

If stricter root minimization or additional archive consolidation is desired later, that should be handled as a separate, reviewable cleanup phase.
