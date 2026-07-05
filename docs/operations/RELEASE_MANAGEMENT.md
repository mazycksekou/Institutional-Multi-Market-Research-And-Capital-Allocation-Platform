# Release Management

## Purpose

This repository tracks release discipline for modernization, validation, and future product work.

This document is about repository and documentation readiness, not a product launch announcement.

## Versioning Policy

- **Patch**: documentation, governance, validation, and other non-breaking updates
- **Minor**: non-breaking runtime changes, new contracts, or additive capability
- **Major**: breaking contract changes, removed routes, or behavior changes that require consumer updates

## Modernization Milestone Tag

- Repository modernization closeout tag: `repository-modernization-v1.0`
- This tag marks the end of the repository modernization pass, not a production feature launch.

## Release Checklist

1. Run the repository pre-flight checks.
2. Confirm root markdown policy, OpenAPI contract, architecture, audit, and document lifecycle checks.
3. Run `ops_check` and the smoke suite.
4. Confirm the working tree is clean.
5. Review the closeout docs and remaining gaps.
6. Push the commit and, when appropriate, create or update a release tag.

## Rollback Expectations

- Prefer revert commits over force edits.
- Preserve milestone and audit evidence so the reason for rollback remains visible.
- Use the previous validated tag or commit as the rollback target when a release needs to be reversed.

## Production-Ready Criteria

- Local validation is green.
- Governance checks are green.
- The repo shape is documented.
- Remaining gaps are explicitly listed rather than implied.

## What Is Not Yet A Product Release

- Future NFL/backtesting capability work
- Provider expansion or live connector activation
- Deployment-specific feature rollouts
