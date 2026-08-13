# Next Action

## Next Phase

`Covariance and Time-Dependent Risk Capability Audit`

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

## Objective

Run only the Covariance and Time-Dependent Risk Capability Audit on top of the now-certified repository-owned OddsWarehouse NFL historical dataset and the completed NFL research pipeline.
Reuse the canonical historical dataset, certification, lifecycle, lineage, validation, query, retrieval, dashboard, backtesting, and Universal Market Framework owners.
Identify exactly which covariance and time-dependent risk capabilities are genuinely missing, where they belong, what evidence already exists, and what the smallest governed implementation surface would be.
Preserve the certified OddsWarehouse dataset, certified NFL reference behavior, parity evidence, lineage, provenance, determinism, and point-in-time integrity.
Do not implement the risk engine, another market, Worldview, capital allocation, paper trading, or live execution in this audit phase.

## Allowed Actions

- Reuse the certified repository-owned OddsWarehouse historical dataset as the canonical audit input.
- Reuse the canonical acquisition, storage, certification, lifecycle, lineage, provenance, validation, query, retrieval, dashboard, and Universal Market Framework owners.
- Inspect current dataset coverage, feature readiness, backtesting inputs, and contract boundaries for covariance and time-dependent risk gaps only.
- Produce bounded evidence, gap classification, and the governed implementation handoff for only the missing covariance and risk capabilities.
- Preserve all certified NFL reference behavior, lineage, provenance, determinism, point-in-time integrity, and Bronze, Silver, and Gold lifecycle mapping during the audit.
- Update project status, sequencing, and document indexes when the phase completes.
- Keep `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, and `docs/INTELLECTUAL_PROPERTY_REGISTER.md` as non-authoritative placeholders; update only references or indexes if required.

## Forbidden Actions

- Do not implement covariance or the risk engine during the audit.
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
- Do not re-implement the completed controlled vendor ingest, bounded replay, or dataset-certification workflow in this phase.
- Do not mutate certified OddsWarehouse outputs unless the audit proves a reproducible repository defect that requires governed remediation.
- Do not populate `docs/PRODUCT_SPEC.md`, `docs/BUSINESS_STRATEGY.md`, or `docs/INTELLECTUAL_PROPERTY_REGISTER.md`.
- Do not make uncontrolled network calls or require secrets in tests.

## Expected Deliverables

- A bounded audit of covariance and time-dependent risk capability readiness on top of the certified repository-owned NFL dataset.
- Explicit evidence of which covariance and risk capabilities already exist, which are missing, and where missing work belongs.
- Preserved certified NFL parity and unchanged certified NFL reference behavior during the audit.
- Updated project status, sequencing, and document indexes when the phase completes.
- Phase handoff:
  Covariance and Time-Dependent Risk Capability Audit
  -> Implement only covariance and risk capabilities confirmed missing by that audit

## Current Execution Checkpoint

Portable External Research-Data Storage is complete: the repository-owned full OddsWarehouse NFL Basic historical dataset is ingested on FantomHD, exact 1,000-row replay is green, exact full replay is green, dataset certification is complete, and repository-owned retrieval is verified.
The next governed operational step is to perform the Covariance and Time-Dependent Risk Capability Audit only, using the certified repository-owned dataset and current backtesting/runtime surfaces as evidence.

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
