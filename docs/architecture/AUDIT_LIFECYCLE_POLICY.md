# Audit Lifecycle Policy

This policy keeps audit material useful without letting temporary reports accumulate forever.

## States

### ACTIVE

- The report is currently being used to make or support a decision.
- The report still provides live guidance or evidence that has not yet been fully absorbed into canonical docs.

### DECISION CAPTURED

- The final decision has been moved into architecture docs, ADRs, ownership maps, standards, or contracts.
- The report may still be useful as evidence, but the decision itself now lives in canonical docs.

### ARCHIVE

- The report is useful historical evidence but is no longer active.
- Archive material should remain accessible for audit and due-diligence purposes.

### DELETE CANDIDATE

- The report is temporary, duplicated, superseded, unreferenced, and not historically useful.
- A delete candidate should not be removed until it has been validated against active docs, scripts, tests, and governance checks.

### DELETE APPROVED

- The report has been validated as safe to remove.
- Deletion should only happen after the lifecycle register and reference checks confirm that no active decision depends on it.

## Rules

- Never delete an audit report that is the only evidence for an architectural decision.
- Never delete docs referenced by active architecture docs, ADRs, tests, scripts, or governance checks.
- Prefer archive over delete when uncertainty remains.
- If an audit report is still needed for business review, due diligence, or provenance, keep it accessible even if it is no longer active.
- Archived material should still be recorded in the retention register so it does not disappear from governance view.

## Governance Boundary

- Active architecture docs, ADRs, contracts, and standards capture the current decision state.
- Audit reports support those decisions and should eventually transition to archive once the decision is captured.
- A report may remain ACTIVE for a period of time when it still informs current work, but it should be downgraded to ARCHIVE or DELETE CANDIDATE once its role is complete.

## Related References

- [Audit Retention Register](../reports/audits/AUDIT_RETENTION_REGISTER.md)
- [Master System Architecture](./MASTER_SYSTEM_ARCHITECTURE.md)
- [Final Repository Structure](./FINAL_REPOSITORY_STRUCTURE.md)
- [Canonical Ownership Map](./CANONICAL_OWNERSHIP_MAP.md)
- [Contract Index](../contracts/CONTRACT_INDEX.md)
- [Automated Governance](../operations/AUTOMATED_GOVERNANCE.md)
- [Validation Runbook](../operations/VALIDATION_RUNBOOK.md)
