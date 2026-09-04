# Next Action

## Next Phase

`Implement Confirmed Covariance And Time-Dependent Risk Gaps`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened National Football League (NFL) research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.
`NFL Production Completion` audited the certified NFL implementation against production-complete requirements, reused the Universal Market Framework, added the canonical production audit/report/query surface, and preserved all certified NFL reference behavior.
Close only verified NFL production gaps remained the governing closure rule for the completed NFL Production Completion phase.
`Data Identity, Reconciliation and Lakehouse Foundation` completed the shared identity, reconciliation, quarantine, revision-aware, and Parquet lakehouse contracts needed before vendor onboarding. It preserved certified NFL reference parity, produced deterministic readiness artifacts, and advanced the repository to First Controlled NFL Vendor Ingest readiness without ingesting vendor data in that phase.
That completed foundation phase added Parquet-based analytical storage, Delta-compatible interfaces, Bronze, Silver, and Gold lifecycle mapping, and the deterministic Research Intelligence layer handoff needed before controlled vendor onboarding.
`First Controlled NFL Vendor Ingest` completed the first controlled OddsWarehouse NFL Basic 2009 pilot ingest on top of the shared identity, reconciliation, quarantine, revision-aware, and lakehouse foundation. It reused the canonical acquisition, `LocalStorageEngine`, certification, lifecycle, lineage, and validation owners, preserved certified NFL reference behavior, and produced deterministic identity-binding, reconciliation, quarantine, Bronze, Silver, and Gold evidence for the first governed vendor slice.
`Portable External Research-Data Storage` then completed the real FantomHD storage migration and historical-state hardening path for the authoritative OddsWarehouse NFL Basic source. The repository now owns the externally stored full 5,075-row historical dataset, exact 1,000-row replay is green, exact full replay is green, dataset certification is complete, and repository-owned retrieval is verified without reopening the provider Comma-Separated Values source file.
`Covariance and Time-Dependent Risk Capability Audit` then completed on top of the certified repository-owned OddsWarehouse historical dataset, canonical backtesting surfaces, and existing market-profile contracts. The audit confirmed pairwise covariance/correlation, correlation matrix, portfolio variance/volatility, drawdown, Expected Value primitives, and deterministic point-in-time replay; bounded the partial and missing risk surfaces; and authorized implementation of only confirmed covariance and risk gaps.
`Static Covariance and Matrix Completion` then completed canonical covariance-matrix construction and direct `portfolio_variance()` compatibility in the existing pure-math owner.
`Dynamic and Point-in-Time Covariance` then completed rolling covariance/correlation, Exponentially Weighted Moving Average covariance/correlation, and deterministic point-in-time covariance/correlation reconstruction using only observations known at or before each cutoff.
`Portfolio Exposure and Incremental Risk` then completed canonical portfolio exposure, gross/net exposure, concentration, covariance-aware volatility, Marginal Contribution to Risk, component contribution to risk, incremental portfolio risk, diversification behavior, and point-in-time covariance-matrix composition.

## Objective

Implement only Time-Dependent Risk inside the active governed phase Implement Confirmed Covariance And Time-Dependent Risk Gaps.
Reuse the canonical time, pure-math, risk, portfolio, certification, validation, and backtesting owners already present in the repository.
Build only the minimum timing, horizon, freshness, and confidence-risk capability needed to distinguish opportunities whose risk depends on when evidence is observed and when exposure settles.
Preserve all existing covariance, correlation, covariance-matrix, correlation-matrix, rolling covariance/correlation, Exponentially Weighted Moving Average covariance/correlation, point-in-time reconstruction, portfolio-variance, portfolio-volatility, portfolio exposure, incremental-risk, drawdown, Expected Value, and deterministic replay behavior.
Do not begin another market, Worldview, universal capital allocation, paper trading, Live Model Testing, or execution in this checkpoint.

## Allowed Actions

- Reuse `src/core/math_utils.py` as the canonical pure covariance/correlation/matrix owner if repository evidence still supports it.
- Reuse `src/core/risk.py` as the current portfolio-risk consumer and `src/core/portfolio.py` as the current portfolio/exposure helper surface.
- Reuse `src/backtesting/baseline_backtesting.py` only for historical replay and point-in-time consumption if repository evidence still supports that ownership boundary.
- Reuse `src/core/market_clock.py` or the actual canonical time owner only if repository inspection confirms it owns timing semantics.
- Extend active tests around time horizon, holding period, time to event, evidence age, freshness, confidence, and point-in-time compatibility using only tiny deterministic fixtures.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity while implementing Time-Dependent Risk.
- Update project status, sequencing, and document indexes when the phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not reimplement completed static covariance, correlation, covariance-matrix, correlation-matrix, rolling covariance/correlation, Exponentially Weighted Moving Average covariance/correlation, point-in-time covariance/correlation reconstruction, portfolio exposure, or incremental portfolio risk.
- Do not implement covariance regimes or covariance stability outputs.
- Do not implement covariance-aware backtesting, scenario/stress risk, Value at Risk, Conditional Value at Risk, or Expected Shortfall.
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
- Do not re-implement the completed controlled vendor ingest, bounded replay, dataset-certification workflow, completed covariance audit, completed static covariance math, completed dynamic point-in-time covariance work, or completed portfolio incremental-risk work in this phase.
- Do not mutate certified OddsWarehouse outputs unless Time-Dependent Risk exposes a reproducible repository defect that requires governed remediation.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- Canonical time-dependent risk representation reused or minimally extended from the existing time/risk/backtesting owners.
- Holding-period, time-to-event, forecast-horizon, freshness, and confidence risk behavior defined without beginning capital allocation.
- Point-in-time compatibility proven so historical risk calculations cannot use evidence unavailable at the cutoff.
- Preserved certified NFL parity and unchanged certified NFL reference behavior during Time-Dependent Risk.
- Updated project status, sequencing, and document indexes when the phase completes.
- Phase handoff:
  Time-Dependent Risk
  -> Covariance-Aware Baseline Backtest Integration

## Current Execution Checkpoint

`Time-Dependent Risk`

The covariance/time-dependent-risk audit, static covariance math completion, Dynamic and Point-in-Time Covariance, and Portfolio Exposure and Incremental Risk are complete.
The active governed phase remains Implement Confirmed Covariance And Time-Dependent Risk Gaps, and Time-Dependent Risk is the current checkpoint.
Implement only the time-dependent risk work proven missing by the audit, using the existing time, math, risk, portfolio, and backtesting owners as the bounded surface.

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
