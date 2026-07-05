# Document Lifecycle Policy

This policy governs documentation across the repository so audits, reports, summaries, and historical evidence stay useful without turning into unbounded clutter.

It complements [Audit Lifecycle Policy](./AUDIT_LIFECYCLE_POLICY.md). Audit reports are one document class inside the broader document lifecycle.

## States

### WORKING

- A document is still being shaped or is part of an active discovery pass.
- The document may inform current work but has not yet been consolidated into durable architecture, contract, standard, or summary docs.

### ACTIVE

- The document is current and authoritative for its responsibility.
- Examples include architecture docs, contracts, standards, runbooks, reviewer guidance, and current governance docs.

### DECISION CAPTURED

- The decision or reasoning now lives in canonical docs, ADRs, contracts, standards, or reviewer guidance.
- The original document may remain as evidence, but it is no longer the main source of truth.

### CONSOLIDATED

- The document is a milestone summary or curated aggregation that replaces several earlier reports.
- Consolidated documents should point readers to the current authoritative docs.

### ARCHIVED

- The document is durable historical evidence and is no longer active.
- Archived documents preserve the decision trail for audit and due-diligence purposes.

### DELETE CANDIDATE

- The document appears temporary, superseded, duplicated, unreferenced, and not historically useful.
- Delete candidates must still be validated against active docs, tests, scripts, and governance before removal.

### DELETE APPROVED

- The document has been validated as safe to remove.
- Only remove a document after the lifecycle register and reference checks confirm that nothing active depends on it.

## Transition Rules

- WORKING -> ACTIVE
- ACTIVE -> DECISION CAPTURED
- DECISION CAPTURED -> CONSOLIDATED
- CONSOLIDATED -> ARCHIVED
- ARCHIVED -> DELETE CANDIDATE
- DELETE CANDIDATE -> DELETE APPROVED
- DELETE APPROVED -> REMOVED

## Placement Rules

- Active documentation should live under `docs/architecture/`, `docs/contracts/`, `docs/development/`, or `docs/operations/` when it is current guidance.
- Temporary reports belong under `docs/reports/` until they are either consolidated or archived.
- Historical evidence belongs under `docs/archive/historical_reports/`.
- Milestone summaries belong under `docs/archive/milestones/`.
- Deprecated material belongs under `docs/archive/deprecated_docs/`.
- Root-level Markdown is not used for ordinary documentation files.
- The only root-level documentation indexes intentionally kept at `docs/` are:
  - `docs/MASTER_DOCUMENT_INDEX.md`
  - `docs/DOCUMENT_RETENTION_INDEX.md`

## Delete Rules

A document may be deleted only when all of the following are true:

1. Its knowledge exists elsewhere.
2. It has no unique historical value.
3. It is not referenced by active docs, tests, scripts, or governance.
4. It is not required for business, reviewer, legal, security, audit, or architecture evidence.
5. It is not the only proof of a decision.
6. The decision has been captured in an ADR, architecture map, contract, standard, runbook, or milestone summary.

## Governance Boundary

- Architecture docs, contracts, standards, runbooks, and reviewer docs capture the current truth.
- Reports, checkpoints, proofs, and discovery docs support those decisions and should eventually transition to consolidated or archived states.
- Temporary documents must not remain indefinitely when a durable summary exists.

## Related References

- [Audit Lifecycle Policy](./AUDIT_LIFECYCLE_POLICY.md)
- [Master Document Index](../MASTER_DOCUMENT_INDEX.md)
- [Document Retention Index](../DOCUMENT_RETENTION_INDEX.md)
- [Master System Architecture](./MASTER_SYSTEM_ARCHITECTURE.md)
- [Final Repository Structure](./FINAL_REPOSITORY_STRUCTURE.md)
- [Canonical Ownership Map](./CANONICAL_OWNERSHIP_MAP.md)
- [Documentation Governance](./DOCUMENTATION_GOVERNANCE.md)
- [Automated Governance](../operations/AUTOMATED_GOVERNANCE.md)
- [Validation Runbook](../operations/VALIDATION_RUNBOOK.md)
