# Next Action

## Next Phase

`Data Identity, Reconciliation and Lakehouse Foundation`

## Execution Policy

Follow `docs/architecture/REPOSITORY_OS.md` for discovery, validation, and ownership rules. This file owns sequencing only and remains the sole sequencing source.

## Previous Phase

`Phase 5.7 - Research Intelligence` built the deterministic explanatory layer on top of the certified and hardened NFL research pipeline.
`Universal Market Framework` built the first reusable market-agnostic framework surface on top of the certified NFL research pipeline and deterministic Research Intelligence layer. It preserves the NFL chain as immutable reference behavior while exposing reusable profile contracts, lifecycle gates, readiness surfaces, parity evidence, and dashboard/query interfaces for future market onboarding.
`NFL Production Completion` audited the certified NFL implementation against production-complete requirements, reused the Universal Market Framework, added the canonical production audit/report/query surface, and preserved all certified NFL reference behavior.
Close only verified NFL production gaps remained the governing closure rule for the completed NFL Production Completion phase.
The post-NFL-production sequence is corrected so shared data identity and controlled vendor ingest work complete before covariance implementation begins.

## Objective

Audit existing ingestion, normalization, identity, matching, reconciliation, quality-control, and physical-storage capabilities before implementation.
Reuse the acquisition, `LocalStorageEngine`, local-platform, historical-research-database, certification, lifecycle, lineage, and validation owners.
Add only missing shared identity, reconciliation, quarantine, revision-aware, and lakehouse capabilities.
Map Bronze, Silver, and Gold onto the existing lifecycle rather than replacing it.
Implement Parquet-based analytical storage and Delta-compatible interfaces.
Defer Spark until measured data scale proves distributed execution is required.
Do not ingest the vendor dataset in this phase.
Do not implement covariance, another market, Worldview, capital allocation, paper trading, or live execution in this phase.

## Allowed Actions

- Audit existing ingestion, normalization, identity, matching, reconciliation, quality-control, quarantine, revision, and physical-storage capabilities before implementation.
- Reuse the acquisition, `LocalStorageEngine`, local-platform, historical-research-database, certification, lifecycle, lineage, and validation owners.
- Add only missing shared identity, reconciliation, quarantine, revision-aware, and lakehouse capabilities.
- Map Bronze, Silver, and Gold onto the existing lifecycle rather than replacing it.
- Implement Parquet-based analytical storage and Delta-compatible interfaces.
- Defer Spark until measured data scale proves distributed execution is required.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, and point-in-time integrity while identifying extension seams only.
- Update project status, sequencing, and document indexes when the phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not ingest the vendor dataset in this phase.
- Do not implement covariance or the risk engine.
- Do not implement another sport.
- Do not implement the first controlled NFL vendor ingest in this phase.
- Do not implement prediction markets.
- Do not implement Zero-DTE options.
- Do not implement Worldview Intelligence.
- Do not implement cross-market intelligence.
- Do not implement universal risk and capital allocation.
- Do not implement live execution.
- Do not implement paper trading.
- Do not duplicate Universal Market Framework logic or create NFL-only replacements for reusable framework assets.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- A verified repository audit covering existing, partial, missing, duplicated, and deferred ingestion, normalization, identity, matching, reconciliation, quality-control, quarantine, revision-aware, and physical-storage support.
- A canonical owner and extension-seam inventory for shared data identity, reconciliation, and lakehouse implementation.
- A shared-lifecycle mapping for Bronze, Silver, and Gold that preserves the existing certification and lifecycle owners.
- A Parquet and Delta-compatible storage plan that preserves the current deterministic research pipeline boundaries and defers Spark unless measured scale requires it.
- Updated project status, sequencing, and document indexes when the audit completes.
- Phase handoff:
  Data Identity, Reconciliation and Lakehouse Foundation
  -> First Controlled NFL Vendor Ingest
  -> Covariance and Time-Dependent Risk Capability Audit

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
