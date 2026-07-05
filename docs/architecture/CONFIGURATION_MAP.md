# Configuration Map

## Root-Level Configuration

| File | Purpose | Ownership |
| --- | --- | --- |
| `pyproject.toml` | Tooling and package configuration | Repository-level build config |
| `pytest.ini` | Pytest configuration and markers | Test governance |
| `requirements.txt` | Runtime dependencies | Repository-level dependency manifest |
| `requirements-dev.txt` | Development/test dependencies | Repository-level dependency manifest |
| `Dockerfile` | Container build instructions | Deployment config |
| `render.yaml` | Render deployment blueprint | Deployment config |
| `runtime.txt` | Runtime version declaration | Deployment config |
| `.env.example` | Environment template | Documentation/support |
| `.python-version` | Local Python version hint | Tooling support |

## Runtime Configuration

- Runtime behavior should be controlled close to the owning module whenever possible.
- Shared constants belong in the canonical runtime package that consumes them.
- Environment variables are configuration inputs, not documentation.

## Governance Notes

- Deployment configuration can remain at the root when a platform requires it.
- No source file should be hidden by `.gitignore`.
- Configuration ownership should be documented when it affects validation, runtime behavior, or deployment shape.
