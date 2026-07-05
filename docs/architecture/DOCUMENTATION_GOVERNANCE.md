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
- `docs/archive/completed_phases/`
- `docs/archive/historical_reports/`
- `docs/archive/deprecated_docs/`

## Enforcement

Before every commit:

1. Scan the repository root for `.md` files.
2. Allow only `README.md`.
3. Move or archive every other Markdown file into the `docs/` hierarchy.
4. Update active documentation links when a moved document is still referenced.

The repository validation script `scripts/check_root_markdown.py` and `scripts/ops_check.py` both enforce this rule.
GitHub Actions, when present, should call those same local scripts rather than duplicating validation logic.
