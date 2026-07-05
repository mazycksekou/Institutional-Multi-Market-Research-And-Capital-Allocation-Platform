# Dependency Reproducibility

## Purpose

This repository uses explicit dependency files and environment descriptors so the local developer setup, GitHub Actions validation, Docker image, and Render deployment can be reproduced with the same checked-in inputs.

The goal is reproducibility, not constant upgrade churn.

## Canonical Inputs

| Layer | Source | Status | Notes |
| --- | --- | --- | --- |
| Runtime Python version | `runtime.txt` | Pinned | `python-3.12.11` |
| Container runtime | `Dockerfile` | Pinned | Uses `python:3.12.11-slim` |
| Render runtime version | `render.yaml` | Pinned | `PYTHON_VERSION=3.12.11` |
| Runtime dependencies | `requirements.txt` | Pinned | Exact package versions are locked |
| Development / validation dependencies | `requirements-dev.txt` | Intentionally flexible | Tooling is resolved at install time |
| CI validation workflow | `.github/workflows/repository-validation.yml` | Authoritative wrapper | Calls repository scripts instead of duplicating validation logic |

## How Dependencies Are Installed

### Local development

1. Create a virtual environment with Python 3.12.11.
2. Install runtime dependencies with `python -m pip install -r requirements.txt`.
3. Install validation tooling with `python -m pip install -r requirements-dev.txt`.
4. If you want the dashboard entrypoint, install the optional UI dependency set used by `streamlit_app.py`.

### GitHub Actions

GitHub Actions uses the same repository scripts as local validation and now runs on Python 3.12.11 so the CI interpreter matches the pinned runtime version.

### Docker

The Dockerfile starts from `python:3.12.11-slim`, installs `requirements.txt`, and then copies the repository into the image.

### Render

`render.yaml` configures the web service to use the checked-in Dockerfile and pins `PYTHON_VERSION` to 3.12.11. Environment variables are injected by Render rather than baked into the image.

## What Is Intentionally Unpinned

The development tooling in `requirements-dev.txt` is intentionally not pinned to exact versions. These packages support validation and contributor workflows, and the repository relies on the local checks plus the smoke suite to detect compatibility issues.

## Reproducibility Guidance

- Use the same Python version as the runtime and deployment descriptors whenever possible.
- Reinstall dependencies from the checked-in requirement files when the repository changes.
- If a new tool becomes a required dependency, document it here and add it to the relevant validation step.
- Do not rely on undocumented global machine state for validation.

## Known Reproducibility Gap

The repository still depends on the availability of the package index during installation. That is normal for this phase, but it means full air-gapped reproducibility is not yet implemented.
