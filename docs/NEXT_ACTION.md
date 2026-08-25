# Next Action

## Next Phase

`Implement Confirmed Covariance And Time-Dependent Risk Gaps`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.
`NFL Production Completion` audited the certified NFL implementation against production-complete requirements, reused the Universal Market Framework, added the canonical production audit/report/query surface, and preserved all certified NFL reference behavior.
Close only verified NFL production gaps remained the governing closure rule for the completed NFL Production Completion phase.
`Data Identity, Reconciliation and Lakehouse Foundation` completed the shared identity, reconciliation, quarantine, revision-aware, and Parquet lakehouse contracts needed before vendor onboarding. It preserved certified NFL reference parity, produced deterministic readiness artifacts, and advanced the repository to First Controlled NFL Vendor Ingest readiness without ingesting vendor data in that phase.
That completed foundation phase added Parquet-based analytical storage, Delta-compatible interfaces, Bronze, Silver, and Gold lifecycle mapping, and the deterministic Research Intelligence layer handoff needed before controlled vendor onboarding.
`First Controlled NFL Vendor Ingest` completed the first controlled OddsWarehouse NFL Basic 2009 pilot ingest on top of the shared identity, reconciliation, quarantine, revision-aware, and lakehouse foundation. It reused the canonical acquisition, `LocalStorageEngine`, certification, lifecycle, lineage, and validation owners, preserved certified NFL reference behavior, and produced deterministic identity-binding, reconciliation, quarantine, Bronze, Silver, and Gold evidence for the first governed vendor slice.
`Portable External Research-Data Storage` then completed the real FantomHD storage migration and historical-state hardening path for the authoritative OddsWarehouse NFL Basic source. The repository now owns the externally stored full 5,075-row historical dataset, exact 1,000-row replay is green, exact full replay is green, dataset certification is complete, and repository-owned retrieval is verified without reopening the provider CSV.
`Covariance and Time-Dependent Risk Capability Audit` then completed on top of the certified repository-owned OddsWarehouse historical dataset, canonical backtesting surfaces, and existing market-profile contracts. The audit confirmed pairwise covariance/correlation, correlation matrix, portfolio variance/volatility, drawdown, EV primitives, and deterministic PIT replay; bounded the partial and missing risk surfaces; and authorized the ordered implementation sequence A-F with Group A as the first active checkpoint.

## Objective

Implement only Group A — Canonical Covariance Math Completion inside the active governed phase Implement Confirmed Covariance And Time-Dependent Risk Gaps.
Reuse the canonical pure-math, portfolio-risk, portfolio-structure, certification, validation, and backtesting owners already present in the repository.
Add one reusable canonical covariance-matrix constructor to the existing pure-math owner, define its input and numerical contract explicitly, and prove direct compatibility with the current `portfolio_variance()` owner.
Preserve all existing covariance, correlation, correlation-matrix, portfolio-variance, portfolio-volatility, drawdown, EV, and deterministic PIT replay behavior.
Do not begin Groups B-F, another market, Worldview, universal capital allocation, paper trading, Live Model Testing, or execution in this checkpoint.

## Allowed Actions

- Reuse `src/core/math_utils.py` as the canonical pure covariance/correlation/matrix owner if repository evidence still supports it.
- Reuse `src/core/risk.py` as the current portfolio-risk consumer and `src/core/portfolio.py` as the current portfolio/exposure helper surface.
- Extend tests around covariance, correlation, correlation matrices, covariance matrices, and `portfolio_variance()` compatibility using only tiny deterministic fixtures.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity while implementing Group A.
- Update project status, sequencing, and document indexes when the phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not implement rolling covariance.
- Do not implement rolling correlation.
- Do not implement EWMA covariance.
- Do not implement covariance half-life or PIT covariance reconstruction.
- Do not implement covariance regimes or covariance stability outputs.
- Do not implement marginal contribution to risk or incremental portfolio risk.
- Do not implement time-to-event risk, holding-period risk, freshness decay application, or confidence decay.
- Do not implement covariance-aware backtesting, scenario/stress risk, VaR, CVaR, or Expected Shortfall.
- Do not implement another sport.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement Worldview Intelligence.
- Do not implement cross-market intelligence.
- Do not implement universal risk and capital allocation.
- Do not implement live execution.
- Do not implement paper trading.
- Do not duplicate Universal Market Framework logic or create NFL-only replacements for reusable framework assets.
- Do not create a parallel ingestion, storage, certification, lifecycle, identity, reconciliation, or retrieval framework.
- Do not create `covariance_engine.py`, `nfl_covariance.py`, `covariance_service.py`, or another top-level covariance package.
- Do not re-implement the completed controlled vendor ingest, bounded replay, dataset-certification workflow, or the completed covariance audit in this phase.
- Do not mutate certified OddsWarehouse outputs unless Group A exposes a reproducible repository defect that requires governed remediation.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- One canonical reusable covariance-matrix constructor inside the existing pure-math owner.
- Explicit input, ordering, numerical, and error-handling contract coverage for covariance-matrix construction.
- Proven compatibility with the existing `portfolio_variance()` owner without reshaping, hidden reordering, or side effects.
- Preserved certified NFL parity and unchanged certified NFL reference behavior during Group A.
- Updated project status, sequencing, and document indexes when the phase completes.
- Phase handoff:
  Group A — Canonical Covariance Math Completion
  -> Group B — Rolling And PIT Covariance Estimation

## Current Execution Checkpoint

`Group A — Canonical Covariance Math Completion`

The covariance/time-dependent-risk audit is complete.
The active governed phase is now Implement Confirmed Covariance And Time-Dependent Risk Gaps, and Group A is the first authorized checkpoint.
Implement only the canonical covariance-matrix completion work proven missing by the audit, using the existing pure-math owner and existing risk/portfolio consumers as the bounded surface.

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_audit_lifecycle.py`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python scripts/check_repo_preflight.py --end-task --include-ops`
- `python scripts/run_quality_gates.py --install`
- `git diff --check`
