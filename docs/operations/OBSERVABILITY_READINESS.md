# Observability Readiness

## Purpose

This repository includes local validation, health reporting, and structured ops outputs so contributors can understand repository health without needing external monitoring infrastructure.

## Current Observability Surfaces

| Surface | What it provides | Status |
| --- | --- | --- |
| `scripts/ops_check.py` | Structured local repository health and governance output | Active |
| `scripts/check_*` validation scripts | Focused checks for root markdown, OpenAPI, architecture, document lifecycle, and audit lifecycle | Active |
| `src.services.system_health` | Runtime health snapshots and local health files | Active |
| `/health` smoke coverage | Quick runtime verification from tests | Active |
| `streamlit` dashboard adapters | Read-only health and readiness displays based on canonical data | Active |

## Logging And Errors

- Runtime code uses ordinary Python and framework error handling.
- Validation scripts produce structured pass/fail output rather than opaque stack traces when the repository is healthy.
- Governance scripts should prefer clear diagnostics over uncaught exceptions.

## Health And Readiness

- Repository health is measured first through local scripts and the smoke suite.
- `ops_check` is the central view for local orchestration.
- Health snapshots are stored locally when the runtime asks for them.
- The repository does not rely on a third-party observability vendor for correctness.

## Monitoring Readiness

- No external monitoring platform is required for validation.
- Existing health and readiness outputs are sufficient for the current repository modernization phase.
- A future production deployment can add dashboards or alerting, but that should not replace local validation.

## Gaps

- External alerting and metrics collection are not yet standardized across deployment targets.
- Some runtime surfaces still rely on the caller to inspect returned payloads rather than pushing to a dedicated monitoring backend.
