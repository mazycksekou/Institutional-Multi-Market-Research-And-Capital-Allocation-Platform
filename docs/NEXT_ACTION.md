# Next Action

## Next Phase

`Portable External Research-Data Storage`

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

## Objective

Activate only portable external research-data storage on top of the completed shared identity, reconciliation, quarantine, revision-aware, lakehouse, and First Controlled NFL Vendor Ingest foundation.
Reuse the canonical acquisition, `LocalStorageEngine`, local-platform, historical-research-database, certification, lifecycle, lineage, validation, dashboard, and Universal Market Framework owners.
Add only the configuration, external-root binding, storage portability, migration-safe persistence, and readiness work required to make repository-owned historical, lakehouse, and research artifacts portable beyond the current local-only layout.
Preserve all certified NFL reference behavior, parity evidence, lineage, provenance, determinism, and point-in-time integrity.
Do not implement covariance, another market, Worldview, capital allocation, paper trading, or live execution in this phase.

## Allowed Actions

- Reuse the completed shared identity, reconciliation, quarantine, revision-aware, and lakehouse contracts.
- Reuse the completed First Controlled NFL Vendor Ingest outputs as the storage-portability baseline.
- Reuse the canonical acquisition, storage, certification, lifecycle, lineage, provenance, validation, and dashboard owners.
- Externalize only the storage roots, configuration, portability seams, and readiness evidence required to make repository-owned data portable.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, point-in-time integrity, and Bronze, Silver, and Gold lifecycle mapping while changing storage location mechanics only.
- Extend dashboard, query, audit, and readiness surfaces only where the external-storage phase requires them.
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
- Do not re-implement the controlled vendor ingest or broaden from the first controlled NFL vendor slice to additional vendors or markets in this phase.
- Do not mutate certified NFL outputs merely to relocate storage.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- A portable external research-data storage implementation that reuses the completed shared identity, reconciliation, quarantine, revision, lakehouse, and controlled vendor-ingest contracts.
- Deterministic external-root configuration, migration-safe persistence, and readiness evidence for repository-owned historical, lakehouse, and research artifacts.
- Preserved certified NFL parity and unchanged certified NFL reference behavior.
- Updated project status, sequencing, and document indexes when the phase completes.
- Phase handoff:
  Portable External Research-Data Storage
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
