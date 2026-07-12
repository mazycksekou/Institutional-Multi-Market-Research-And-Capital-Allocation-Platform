# Contributing

Thanks for keeping the repository disciplined and reviewable.

## Before You Start

- Work from `phase-6-api-slimming`
- Confirm `git status` is clean
- Read the relevant architecture and contract docs before changing behavior
- Check the [Branch Governance Policy](./BRANCH_GOVERNANCE_POLICY.md) before deciding whether the work belongs on the current branch

## Safe Workflow

1. Make a focused change
2. Run the pre-flight safety check before starting work and again before handoff
3. Run the canonical local validation command
4. Update docs if the contract or ownership changes
5. Commit once the change is clean
6. Push to the branch after validation

## Required Local Checks

- `./.venv/bin/python scripts/run_quality_gates.py --install`

Use the canonical command above for dependency installation and the full validation pass. Re-run targeted checks only when you are isolating a failure.

## When to Update Tests

- Update a test when the expected contract changed for a valid reason
- Do not weaken a test simply to make a change pass
- Prefer fixing stale assumptions in the test rather than creating duplicate runtime behavior

## Documentation Expectations

- Add new docs directly under `docs/`
- Keep historical evidence in archive folders when it still matters
- Avoid root Markdown except for `README.md`
- Keep branch and task governance guidance in the development docs so it is easy to find during reviews

## Commit Style

- Use concise, descriptive commit messages
- Keep migrations and documentation updates logically separated when that improves reviewability

## Helpfulness Rule

- If a change creates a new public rule or ownership boundary, document it in the architecture or operations docs so the next person does not have to rediscover it
