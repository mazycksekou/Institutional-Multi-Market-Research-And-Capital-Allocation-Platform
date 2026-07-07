# Status Update Policy

## Purpose

This policy defines how Codex and future contributors keep the repository's live status current without creating duplicate master documents.

## Rules

- Every Codex task must update the canonical project status.
- Every Codex task must update the canonical next-action file.
- Current-truth documents belong in `docs/MASTER_DOCUMENT_INDEX.md`.
- Historical reports, audits, and phase reports belong in `docs/DOCUMENT_RETENTION_INDEX.md`.
- Do not add phase reports to the master index unless they become current-truth architecture documents.
- Use the existing canonical roadmap and status docs instead of creating parallel handoff files.

## Required Handoff Documents

- `docs/MASTER_ROADMAP.md`
- `docs/PROJECT_STATUS.md`
- `docs/NEXT_ACTION.md`
- `docs/STATUS_UPDATE_POLICY.md`

## Required Final Report Note

Every final report must state whether `PROJECT_STATUS.md` and `NEXT_ACTION.md` were updated.

## Maintenance Rule

When a status task completes:

1. Refresh `docs/PROJECT_STATUS.md`.
2. Refresh `docs/NEXT_ACTION.md` if the next task changed.
3. Regenerate the document lifecycle indexes if new docs were added.
4. Keep the master index focused on current truth.
5. Keep the retention index focused on historical evidence and working reports.

