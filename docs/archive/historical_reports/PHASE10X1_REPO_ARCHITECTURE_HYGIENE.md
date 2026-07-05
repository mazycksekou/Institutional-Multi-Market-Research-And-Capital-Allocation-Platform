# Phase 10X1 Repo Architecture Hygiene

Generated: 2026-06-12T22:10:58

## Audit Findings Addressed
- Removed BOM/non-printable parse failure from `src/api/schemas/__init__.py`.
- Removed direct AST-level `from main import ...` from `api_server.py`.
- Removed direct `import main` from `tests/support/action_imports.py`.
- Added permanent repo architecture guard tests.

## Professional Decision
- Do not broad-delete runtime data; audit showed `0` tracked generated/runtime files.
- Do not delete template/test files from weak `_new`, `_fixed`, `_template`, or `_v2` filename heuristics without targeted owner review.
- Keep `main.py` as app assembly for now because it has no direct route decorators.
- Deeper app-factory migration is deferred until there is evidence it improves deployment/test reliability.

## Guardrails Added
- All Python files must parse cleanly.
- No Python file may directly `import main` or `from main import ...`.
- `main.py` must not regain direct `@app.*` route decorators.
- Runtime data under key data directories must not be tracked by Git.

RESULT: `repo_architecture_hygiene_guard_added`
