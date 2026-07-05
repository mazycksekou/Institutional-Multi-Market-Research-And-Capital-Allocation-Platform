# Developer Onboarding

## Purpose

This guide helps a new contributor get from a fresh clone to a safe, validated change without having to rediscover the repository rules.

## Quick Start

1. Clone the repository.
2. Create and activate a Python 3.12.11 virtual environment.
3. Install runtime dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Install validation tooling:

   ```bash
   python -m pip install -r requirements-dev.txt
   ```

5. If you plan to run the dashboard entrypoint, install the optional Streamlit UI dependency set used by `streamlit_app.py`:

   ```bash
   python -m pip install streamlit
   ```

PowerShell is optional. The canonical validation workflow uses `python` commands and works from macOS Terminal, Linux shells, and Windows shells without needing the wrapper scripts.

## Validate Your Environment

Run the local repository safety checks before and after making changes:

```bash
python scripts/check_repo_preflight.py --start-task --include-ops
python scripts/check_root_markdown.py
python scripts/check_openapi_contract.py --output text
python scripts/check_architecture.py --output text
python scripts/check_audit_lifecycle.py
python scripts/check_document_lifecycle.py
python scripts/ops_check.py --mode local --output text --skip-network
python -m compileall src tests scripts
pytest -m smoke -q
```

## How To Start The App

- `python -m uvicorn main:app --reload` for local API development
- `python api_server.py` for the deployment adapter entrypoint
- `streamlit run streamlit_app.py` for the local dashboard shell

## How To Make A Safe Change

1. Check whether the task belongs on the current branch.
2. Read the relevant architecture, contract, and operations docs.
3. Keep runtime ownership under `src/`.
4. Update docs when ownership or contract meaning changes.
5. Run the relevant targeted tests first, then the smoke suite, then the local ops check.
6. Use the pre-flight checker before commit and before push.

## How To Open A Pull Request

1. Keep the branch focused on one logical task.
2. Confirm the working tree is clean.
3. Push the branch to the shared remote.
4. Open a pull request with the closeout summary and validation evidence.

## What New Contributors Should Read First

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/architecture/FINAL_REPOSITORY_STRUCTURE.md`
3. `docs/architecture/CANONICAL_OWNERSHIP_MAP.md`
4. `docs/architecture/DEPENDENCY_FLOW_MAP.md`
5. `docs/operations/AUTOMATED_GOVERNANCE.md`
6. `docs/operations/VALIDATION_RUNBOOK.md`
7. `docs/development/ENGINEERING_STANDARDS.md`
