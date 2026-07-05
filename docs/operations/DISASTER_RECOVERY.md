# Disaster Recovery

## Purpose

This document describes the repository-level recovery assumptions for code, documentation, and local persistent data.

## Recovery Model

### Repository state

- Source of truth is Git history.
- Recovery starts by checking out a known-good commit or tag.
- The modernization milestone tag should provide a stable rollback anchor once created.

### Local data

- Local data defaults to the repo-local `data/` fallback when `AUTOMATION_DATA_DIR` is unset.
- On Render, persistent data should be mounted or otherwise provisioned explicitly.
- The repository does not currently ship a full backup orchestration system.

### Deployment recovery

- Rebuild from the pinned Dockerfile and dependency files.
- Re-run local validation before redeploying.
- Confirm the environment variables required by the deployment target.

## Restore Process

1. Identify the last known good commit or tag.
2. Restore the repository checkout to that state.
3. Reinstall dependencies from the pinned requirement files.
4. Re-run the validation scripts.
5. Redeploy only after the repository is green again.

## Rollback Process

- Prefer revert commits for code and docs.
- If deployment changes caused the issue, roll back to the previous validated tag.
- Keep audit and milestone docs intact so the recovery history is visible.

## Gaps

- Automated backup schedules are not defined in the repository.
- Database and persistent volume backup policies must still be set by the deployment environment.
- Disaster recovery has not yet been exercised as a full drill inside this repository.
