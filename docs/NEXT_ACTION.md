# Next Action

## Next Phase

`First Controlled NFL Vendor Ingest`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.
`NFL Production Completion` audited the certified NFL implementation against production-complete requirements, reused the Universal Market Framework, added the canonical production audit/report/query surface, and preserved all certified NFL reference behavior.
Close only verified NFL production gaps remained the governing closure rule for the completed NFL Production Completion phase.
`Data Identity, Reconciliation and Lakehouse Foundation` completed the shared identity, reconciliation, quarantine, revision-aware, and Parquet lakehouse contracts needed before vendor onboarding. It preserved certified NFL reference parity, produced deterministic readiness artifacts, and advanced the repository to First Controlled NFL Vendor Ingest readiness without ingesting vendor data in that phase.
That completed foundation phase added Parquet-based analytical storage, Delta-compatible interfaces, Bronze, Silver, and Gold lifecycle mapping, and the deterministic Research Intelligence layer handoff needed before controlled vendor onboarding.

## Objective

Activate only the first controlled NFL vendor ingest on top of the completed shared identity, reconciliation, quarantine, revision-aware, and lakehouse foundation.
Reuse the canonical acquisition, `LocalStorageEngine`, local-platform, historical-research-database, certification, lifecycle, lineage, validation, dashboard, and Universal Market Framework owners.
Add only the controlled ingest, normalization, identity-binding, reconciliation-evidence, quarantine, certification, persistence, and readiness work required to prove the first vendor slice can enter the certified NFL chain safely.
Preserve all certified NFL reference behavior, parity evidence, lineage, provenance, determinism, and point-in-time integrity.
Do not implement covariance, another market, Worldview, capital allocation, paper trading, or live execution in this phase.

## Allowed Actions

- Reuse the completed shared identity, reconciliation, quarantine, revision-aware, and lakehouse contracts.
- Reuse the canonical acquisition, certification, lifecycle, lineage, provenance, validation, and dashboard owners.
- Ingest only the first controlled NFL vendor slice needed to validate the generalized shared contracts in production.
- Persist deterministic raw, normalized, identity-bound, reconciliation-aware, quarantine-aware, and certification-ready vendor records through the canonical owners.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity while adding controlled ingest evidence only.
- Extend dashboard, query, audit, and readiness surfaces only where the controlled ingest phase requires them.
- Update project status, sequencing, and document indexes when the phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not implement covariance or the risk engine.
- Do not implement another sport.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement Worldview Intelligence.
- Do not implement cross-market intelligence.
- Do not implement universal risk and capital allocation.
- Do not implement live execution.
- Do not implement paper trading.
- Do not duplicate Universal Market Framework logic or create NFL-only replacements for reusable framework assets.
- Do not create a parallel ingestion, storage, certification, lifecycle, identity, or reconciliation framework.
- Do not broaden from the first controlled NFL vendor slice to additional vendors or markets in this phase.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- A controlled first-vendor-ingest implementation that reuses the completed shared identity, reconciliation, quarantine, revision, and lakehouse contracts.
- Deterministic acquisition, normalization, identity-binding, reconciliation, quarantine, certification, persistence, and readiness evidence for the first controlled NFL vendor slice.
- Preserved certified NFL parity and unchanged certified NFL reference behavior.
- Updated project status, sequencing, and document indexes when the phase completes.
- Phase handoff:
  First Controlled NFL Vendor Ingest
  -> Covariance and Time-Dependent Risk Capability Audit
  -> Implement only covariance and risk capabilities confirmed missing by that audit

## Validation Commands

- `python -m compileall src tests scripts`
- `pytest -m smoke -q`
- `python scripts/check_root_markdown.py`
- `python scripts/check_architecture.py --output text`
- `python scripts/check_document_lifecycle.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python scripts/check_repo_preflight.py --before-commit --include-ops`
- `python scripts/check_repo_preflight.py --before-push --include-ops`
- `python scripts/check_repo_preflight.py --end-task --include-ops`
- `git diff --check`
- `powershell -ExecutionPolicy Bypass -File .\\scripts\\run_tests.ps1 -Mode full`
