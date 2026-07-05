# Contributing

Thanks for keeping the repository disciplined and reviewable.

## Before You Start

- Work from `phase-6-api-slimming`
- Confirm `git status` is clean
- Read the relevant architecture and contract docs before changing behavior

## Safe Workflow

1. Make a focused change
2. Run the relevant local validation
3. Update docs if the contract or ownership changes
4. Commit once the change is clean
5. Push to the branch after validation

## Required Local Checks

- `python scripts/check_root_markdown.py`
- `python scripts/check_openapi_contract.py --output text`
- `python scripts/check_architecture.py --output text`
- `python scripts/ops_check.py --mode local --output text --skip-network`
- `python -m compileall src tests scripts`
- `pytest -m smoke -q`

## When to Update Tests

- Update a test when the expected contract changed for a valid reason
- Do not weaken a test simply to make a change pass
- Prefer fixing stale assumptions in the test rather than creating duplicate runtime behavior

## Documentation Expectations

- Add new docs directly under `docs/`
- Keep historical evidence in archive folders when it still matters
- Avoid root Markdown except for `README.md`

## Commit Style

- Use concise, descriptive commit messages
- Keep migrations and documentation updates logically separated when that improves reviewability

## Helpfulness Rule

- If a change creates a new public rule or ownership boundary, document it in the architecture or operations docs so the next person does not have to rediscover it
