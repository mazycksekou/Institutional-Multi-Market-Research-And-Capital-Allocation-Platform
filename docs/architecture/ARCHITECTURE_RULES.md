# Architecture Rules

Permanent repository rules:

## Runtime Ownership

- All runtime/application code lives under `src/`
- Root-level runtime Python files are limited to approved entrypoints
- No new runtime package may be created outside `src/`

## Approved Root Files

- `README.md`
- `pyproject.toml`
- `pytest.ini`
- `main.py`
- `api_server.py`
- `streamlit_app.py`
- other explicitly approved project configuration files

## Allowed Top-Level Areas

- `src/` for runtime/application code
- `tests/` for tests
- `scripts/` for tools and validation helpers
- `docs/` for all documentation

## Forbidden

- Runtime package roots outside `src/`
- `automation_scheduler/`
- `automation_scheduler_legacy/`
- Compatibility wrappers that duplicate business logic
- Tests that require deleted files to exist
- Broad `.gitignore` rules that hide valid `src/**/*.py` files

## Documentation Policy

- `README.md` is the only Markdown file allowed at the repository root
- All other Markdown files belong under `docs/`
