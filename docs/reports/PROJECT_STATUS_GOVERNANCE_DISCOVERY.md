# Project Status Governance Discovery

## Purpose

This discovery report identifies which existing repository documents already own project-status, roadmap, index, and handoff responsibilities so the repository can reuse canonical files instead of creating duplicate master documents.

## Candidate Files Discovered

| file | current responsibility | reuse decision | update decision | new file needed? |
| --- | --- | --- | --- | --- |
| `docs/MASTER_ROADMAP.md` | Permanent market lifecycle roadmap and phase rule | Reuse | Update | No |
| `docs/MASTER_DOCUMENT_INDEX.md` | Current-truth document index | Reuse | Update | No |
| `docs/DOCUMENT_RETENTION_INDEX.md` | Retention and historical evidence register | Reuse | Update | No |
| `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` | Front-door architecture guide | Reuse | No change required | No |
| `docs/architecture/REVIEWER_GUIDE.md` | Reviewer-oriented navigation guide | Reuse | No change required | No |
| `docs/architecture/REPOSITORY_MODERNIZATION_COMPLETE_V1.md` | Modernization milestone summary | Reuse | No change required | No |
| `docs/architecture/REPOSITORY_INDEPENDENCE_SCORECARD.md` | Machine-independence and portability status | Reuse | No change required | No |
| `docs/operations/AUTOMATED_GOVERNANCE.md` | Governance automation policy | Reuse | No change required | No |
| `docs/operations/VALIDATION_RUNBOOK.md` | Validation workflow and operator guidance | Reuse | No change required | No |
| `docs/development/ENGINEERING_STANDARDS.md` | Development and documentation standards | Reuse | No change required | No |

## Findings

- No canonical `PROJECT_STATUS.md` existed before this task.
- No canonical `NEXT_ACTION.md` existed before this task.
- No canonical `STATUS_UPDATE_POLICY.md` existed before this task.
- The repository already had strong canonical master documents, but it lacked a concise live handoff layer for future Codex sessions.

## Decision

Create the following new current-truth documents:

- `docs/PROJECT_STATUS.md`
- `docs/NEXT_ACTION.md`
- `docs/STATUS_UPDATE_POLICY.md`

## Why New Files Are Needed

The roadmap explains lifecycle policy, the master document index explains where truth lives, and the retention index explains what stays historical. None of those files provide a concise, task-ready snapshot of:

- where the project is now
- what branch is active
- what the next Codex task should be
- what validation has already passed

Those responsibilities belong in the new project-status system.

## Recommended Update Path

1. Update the canonical roadmap.
2. Keep `PROJECT_STATUS.md` as the live snapshot.
3. Keep `NEXT_ACTION.md` as the immediate next-step contract.
4. Keep `STATUS_UPDATE_POLICY.md` as the rule set for future tasks.
5. Register the new current-truth docs in the master index and the retention index.

