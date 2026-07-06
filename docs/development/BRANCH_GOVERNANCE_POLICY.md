# Branch Governance Policy

The repository follows a task-focused branching strategy.

## Purpose

Use the current branch only when the requested work logically continues the same milestone or subsystem.

If a request appears unrelated to the current branch, do not automatically create or switch branches. Explain the mismatch and recommend a task-focused branch name instead.

## When a Task Belongs on the Current Branch

Proceed on the current branch when:

- the request continues the current milestone or feature
- the work affects the same subsystem or cleanup stream
- combining the commits will keep the history understandable

## When to Recommend a New Branch

Recommend a new branch when:

- the request belongs to a different milestone or subsystem
- the work would make the commit history harder to review if combined
- the task introduces a separate line of work that should be isolated

Suggested names:

- `feature/<feature-name>`
- `bugfix/<issue-name>`
- `docs/<topic>`
- `refactor/<component>`
- `architecture/<initiative>`
- `research/<topic>`
- `hotfix/<issue>`

## Required Behavior

Never automatically:

- create a branch
- switch branches
- merge branches
- delete branches
- rebase branches
- force push

Only perform those actions when explicitly instructed.

## Mainline Handoff

When a task branch has been merged and validated, `main` becomes the accepted clean-state branch for release and post-merge verification.

## Reporting Expectations

When evaluating branch fit, record:

- the branch used
- why the branch is appropriate
- whether a new branch was recommended
- whether branch creation was requested
