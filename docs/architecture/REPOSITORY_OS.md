# Repository OS

This document is the canonical execution policy for repository work. Keep it concise, target 2-4 pages, and treat it as an index, not an encyclopedia.

Use it together with:

- [PROJECT_STATUS.md](../PROJECT_STATUS.md)
- [NEXT_ACTION.md](../NEXT_ACTION.md)
- [MASTER_ROADMAP.md](../MASTER_ROADMAP.md)
- [STATUS_UPDATE_POLICY.md](../STATUS_UPDATE_POLICY.md)
- [MASTER_DOCUMENT_INDEX.md](../MASTER_DOCUMENT_INDEX.md)
- [DOCUMENT_RETENTION_INDEX.md](../DOCUMENT_RETENTION_INDEX.md)

## Execution Rules

- Verify branch, HEAD, and worktree state before changing files.
- Treat `docs/PROJECT_STATUS.md` as current truth.
- Treat `docs/NEXT_ACTION.md` as the sole sequencing source.
- Reuse canonical owners before introducing new modules or parallel paths.
- Stop discovery once the needed owners, contracts, and validation points are identified.
- Keep changes scoped to the active phase or the explicitly requested infrastructure transition.

## Discovery Rules

- Search before creating.
- Reuse before extending.
- Extend before replacing.
- Create only when no canonical owner exists.
- Do not duplicate runtime owners, registries, storage engines, certification layers, lifecycle layers, or governance documents.
- Do not broaden scope because a related subsystem exists.

## Validation Policy

- Use targeted validation for isolated doc, runtime, or test changes.
- Run the full repository gate only when shared runtime, storage, certification, lifecycle, validation, governance, contract, or other cross-cutting behavior changes.
- Always run the validation required by the active phase or explicit task.
- Keep unrelated validation out of the task unless a shared contract truly changed.

## Repository Layer Order

1. `docs/PROJECT_STATUS.md`
2. `docs/NEXT_ACTION.md`
3. `docs/architecture/REPOSITORY_OS.md`
4. Canonical architecture and contract documents
5. `src/` runtime owners
6. `tests/` contract and regression coverage
7. `scripts/` validation and repository checks
8. `docs/reports/` and archive material for retained evidence

## Canonical Ownership Summary

- `docs/PROJECT_STATUS.md` owns live repository truth.
- `docs/NEXT_ACTION.md` owns sequencing only.
- `docs/STATUS_UPDATE_POLICY.md` owns status-update hygiene.
- `docs/MASTER_ROADMAP.md` owns long-range ordering.
- `docs/MASTER_DOCUMENT_INDEX.md` owns current-truth discoverability.
- `docs/DOCUMENT_RETENTION_INDEX.md` owns historical retention and lifecycle evidence.
- `src/` owns runtime behavior.
- `tests/` owns executable evidence and regression contracts.
- `scripts/` owns validation and preflight enforcement.

## AI Execution Policy

- AI sessions should read `PROJECT_STATUS.md`, `NEXT_ACTION.md`, and `REPOSITORY_OS.md` before execution.
- Future prompts should normally only verify repository state, read `PROJECT_STATUS.md`, `NEXT_ACTION.md`, and `REPOSITORY_OS.md`, execute the active phase, and return the standard report.
- AI should not recreate governance that already exists in canonical docs.
- AI should not invent new master documents, execution standards, or sequencing sources.
- AI should return the standard report shape after the active phase completes.
- AI should keep prompts short by referencing canonical docs instead of repeating policy text.
