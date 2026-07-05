# Documentation Governance

## Permanent rules

- `src/` is reserved exclusively for runtime and application code.
- `docs/` is the canonical home for all documentation.
- The repository root may contain `README.md` only.
- No new Markdown file should be created at the repository root.

## Approved documentation layout

- `docs/architecture/`
- `docs/architecture/adr/`
- `docs/api/`
- `docs/setup/`
- `docs/development/`
- `docs/operations/`
- `docs/contracts/`
- `docs/catalogs/`
- `docs/discovery/`
- `docs/reports/`
- `docs/reports/audits/`
- `docs/reports/migrations/`
- `docs/reports/inventories/`
- `docs/reports/checkpoints/`
- `docs/reports/proofs/`
- `docs/reports/gap_analysis/`
- `docs/reports/matrices/`
- `docs/summaries/`
- `docs/archive/`
- `docs/archive/milestones/`
- `docs/archive/completed_phases/`
- `docs/archive/historical_reports/`
- `docs/archive/deprecated_docs/`

The only Markdown files intentionally kept at the `docs/` root are:

- `docs/MASTER_DOCUMENT_INDEX.md`
- `docs/DOCUMENT_RETENTION_INDEX.md`

## Enforcement

Before every commit:

1. Scan the repository root for `.md` files.
2. Allow only `README.md`.
3. Move or archive every other Markdown file into the `docs/` hierarchy.
4. Update active documentation links when a moved document is still referenced.
5. Keep the document retention index current so temporary work products do not accumulate indefinitely.

The repository validation scripts `scripts/check_root_markdown.py`, `scripts/check_document_lifecycle.py`, and `scripts/ops_check.py` enforce these rules.
GitHub Actions, when present, should call those same local scripts rather than duplicating validation logic.
